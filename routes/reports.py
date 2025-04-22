from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import joinedload
from models import db, Party, PartyType, PurchaseTransaction, PurchaseItem, SalesTransaction, SalesItem, Payment, Item, PaymentType
from flask import session
import calendar
from models import db, PurchaseTransaction, SalesTransaction, Payment, PaymentType, Expense
from sqlalchemy.orm import joinedload



reports_bp = Blueprint('reports', __name__, template_folder='../templates/reports')

# --- Report Form Page --- #
@reports_bp.route('/form')
def report_form():
    parties = Party.query.order_by(Party.name).all()
    items = Item.query.order_by(Item.name).all()
    return render_template('report_form.html', parties=parties, items=items, PartyType=PartyType, active_page='reports')

# --- Generate Report --- #
@reports_bp.route('/generate', methods=['GET', 'POST'])
def generate_report():
    report_type = request.values.get('report_type')  # works for both GET and POST

    if report_type == 'ledger':
        return generate_ledger()
    elif report_type == 'daybook':
        return generate_daybook()
    elif report_type == 'item_report':
        return generate_item_report()
    elif report_type == 'monthly_summary':
        return generate_monthly_summary()
    elif report_type == 'outstanding':
        return generate_outstanding_report()

    flash("❌ Invalid report type selected.", "danger")
    return redirect(url_for('reports.report_form'))

# ------------------ LEDGER STATEMENT ------------------ #
def generate_ledger():
    party_id = request.values.get('party_id')
    start_date = request.values.get('start_date')
    end_date = request.values.get('end_date')

    if not party_id or not start_date or not end_date:
        flash("❌ Party and date range required for ledger.", "danger")
        return redirect(url_for('reports.report_form'))

    party = Party.query.get(party_id)
    if not party:
        flash("❌ Invalid party selected.", "danger")
        return redirect(url_for('reports.report_form'))

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    events = []

    purchases = PurchaseTransaction.query.options(joinedload(PurchaseTransaction.items)).filter_by(party_id=party.id).all()
    sales = SalesTransaction.query.filter_by(party_id=party.id).all()
    payments = Payment.query.filter_by(party_id=party.id).all()

    for p in purchases:
        total = sum(Decimal(item.amount or 0) for item in p.items)
        events.append((p.transaction_date, 'Purchase', p, total))

    for s in sales:
        total = Decimal(s.total_amount or '0.00')
        events.append((s.transaction_date, 'Sale', s, total))

    for pay in payments:
        total = Decimal(pay.amount or '0.00')
        events.append((pay.payment_date, 'Payment', pay, total))

    events.sort(key=lambda x: x[0])

    balance = Decimal('0.00')
    statement_entries = []

    for event_date, event_type, obj, amount in events:
        # Normalize event_date to date if it's datetime
        if isinstance(event_date, datetime):
            event_date = event_date.date()

        if not (start <= event_date <= end):
            continue

        debit = Decimal('0.00')
        credit = Decimal('0.00')
        particulars = ""

        if event_type == 'Purchase':
            particulars = f"Purchase Bill: {obj.bill_number or 'N/A'}"
            credit = amount if party.party_type == PartyType.Supplier else amount

        elif event_type == 'Sale':
            particulars = f"Sale Bill: {obj.bill_number or 'N/A'}"
            debit = amount if party.party_type == PartyType.Customer else amount

        elif event_type == 'Payment':
            if obj.payment_type == PaymentType.Received:
                particulars = f"Payment Received - Ref: {obj.reference or obj.payment_mode or 'N/A'}"
                credit = amount
            elif obj.payment_type == PaymentType.Paid:
                particulars = f"Payment Paid - Ref: {obj.reference or obj.payment_mode or 'N/A'}"
                debit = amount

        balance += debit - credit

        statement_entries.append({
            'date': event_date,
            'particulars': particulars,
            'debit': debit,
            'credit': credit,
            'running_balance': balance
        })

    generated_at = datetime.now()

    return render_template('ledger_statement.html',
                           party=party,
                           statement_entries=statement_entries,
                           start_date=start,
                           end_date=end,
                           generated_at_datetime=generated_at,
                           current_balance=balance,
                           PartyType=PartyType)

# ------------------ Placeholder Handlers ------------------ #
def generate_daybook():
    start_date_str = request.values.get('start_date')
    end_date_str = request.values.get('end_date')

    if not start_date_str or not end_date_str:
        flash("❌ Start and End date are required for Daybook report.", "danger")
        return redirect(url_for('reports.report_form'))

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    transactions = []

    # --- Purchase Transactions ---
    purchases = PurchaseTransaction.query.options(joinedload(PurchaseTransaction.party), joinedload(PurchaseTransaction.items))\
        .filter(PurchaseTransaction.transaction_date.between(start_date, end_date)).all()
    for p in purchases:
        total = sum(Decimal(item.amount or 0) for item in p.items)
        transactions.append({
            'date': p.transaction_date,
            'type': 'Purchase',
            'party_name': p.party.name,
            'notes_or_ref': p.bill_number,
            'debit': Decimal('0.00'),
            'credit': total
        })

    # --- Sales Transactions ---
    sales = SalesTransaction.query.options(joinedload(SalesTransaction.party))\
        .filter(SalesTransaction.transaction_date.between(start_date, end_date)).all()
    for s in sales:
        total = Decimal(s.total_amount or '0.00')
        transactions.append({
            'date': s.transaction_date,
            'type': 'Sale',
            'party_name': s.party.name,
            'notes_or_ref': s.bill_number,
            'debit': total,
            'credit': Decimal('0.00')
        })

    # --- Payments ---
    payments = Payment.query.options(joinedload(Payment.party))\
        .filter(Payment.payment_date.between(start_date, end_date)).all()
    for p in payments:
        amount = Decimal(p.amount or '0.00')
        if p.payment_type == PaymentType.Received:
            transactions.append({
                'date': p.payment_date,
                'type': 'Pmt Recd',
                'party_name': p.party.name,
                'notes_or_ref': p.reference or p.payment_mode,
                'debit': Decimal('0.00'),
                'credit': amount
            })
        elif p.payment_type == PaymentType.Paid:
            transactions.append({
                'date': p.payment_date,
                'type': 'Pmt Paid',
                'party_name': p.party.name,
                'notes_or_ref': p.reference or p.payment_mode,
                'debit': amount,
                'credit': Decimal('0.00')
            })

    # --- Expenses ---
    expenses = Expense.query.options(joinedload(Expense.category))\
        .filter(Expense.expense_date.between(start_date, end_date)).all()
    for e in expenses:
        transactions.append({
            'date': e.expense_date,
            'type': 'Expense',
            'party_name': e.category.name if e.category else '-',
            'notes_or_ref': e.reference or e.notes,
            'debit': Decimal(e.amount or '0.00'),
            'credit': Decimal('0.00')
        })

    # Sort all transactions by date
    transactions.sort(key=lambda tx: tx['date'])

    total_debit = sum(tx['debit'] for tx in transactions)
    total_credit = sum(tx['credit'] for tx in transactions)

    return render_template("reports/daybook.html",
                           transactions=transactions,
                           total_debit=total_debit,
                           total_credit=total_credit,
                           start_date=start_date,
                           end_date=end_date,
                           generated_on=datetime.now(),
                           generated_by='System')



def generate_item_report():
    item_id = request.values.get('item_id')
    party_id = request.values.get('party_id')
    start_date = request.values.get('start_date')
    end_date = request.values.get('end_date')

    start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    item = Item.query.get(item_id) if item_id else None
    party = Party.query.get(party_id) if party_id else None

    # Purchases
    purchase_query = PurchaseItem.query.join(PurchaseTransaction).filter(
        (PurchaseItem.item_id == item.id if item else True),
        (PurchaseTransaction.party_id == party.id if party else True),
        (PurchaseTransaction.transaction_date >= start if start else True),
        (PurchaseTransaction.transaction_date <= end if end else True)
    ).all()

    purchase_transactions = []
    total_purchase_qty = 0
    total_purchase_weight = Decimal('0.00')
    total_purchase_amount = Decimal('0.00')

    for pi in purchase_query:
        rate = (Decimal(str(pi.amount)) / Decimal(str(pi.weight))) if pi.weight else None
        purchase_transactions.append({
            'transaction_date': pi.purchase.transaction_date,
            'party': pi.purchase.party,
            'quantity': pi.quantity,
            'weight': Decimal(str(pi.weight or 0)),
            'rate': rate,
            'total_amount': Decimal(str(pi.amount))
        })
        total_purchase_qty += pi.quantity
        total_purchase_weight += Decimal(str(pi.weight or 0))
        total_purchase_amount += Decimal(str(pi.amount))

    # Sales
    sales_query = SalesItem.query.join(SalesTransaction).filter(
        (SalesItem.item_id == item.id if item else True),
        (SalesTransaction.party_id == party.id if party else True),
        (SalesTransaction.transaction_date >= start if start else True),
        (SalesTransaction.transaction_date <= end if end else True)
    ).all()

    sales_transactions = []
    total_sale_qty = 0
    total_sale_weight = Decimal('0.00')
    total_sale_amount = Decimal('0.00')

    for si in sales_query:
        sales_transactions.append({
            'transaction_date': si.sale.transaction_date,
            'party': si.sale.party,
            'quantity': si.quantity,
            'weight': Decimal(str(si.total_weight)),
            'rate': Decimal(str(si.rate)),
            'total_amount': Decimal(str(si.total_amount))
        })
        total_sale_qty += si.quantity
        total_sale_weight += Decimal(str(si.total_weight))
        total_sale_amount += Decimal(str(si.total_amount))

    # Stock Summary
    stock_remaining_qty = total_purchase_qty - total_sale_qty
    stock_remaining_weight = total_purchase_weight - total_sale_weight

    return render_template("reports/item_report.html",
                           item=item,
                           party=party,
                           start_date=start,
                           end_date=end,
                           generated_on=datetime.now(),
                           generated_by=session.get("user_name", "System"),
                           purchase_transactions=purchase_transactions,
                           sales_transactions=sales_transactions,
                           total_purchase_qty=total_purchase_qty,
                           total_purchase_weight=total_purchase_weight,
                           total_purchase_amount=total_purchase_amount,
                           total_sale_qty=total_sale_qty,
                           total_sale_weight=total_sale_weight,
                           total_sale_amount=total_sale_amount,
                           stock_remaining_qty=stock_remaining_qty,
                           stock_remaining_weight=stock_remaining_weight)
    

def generate_monthly_summary():
    selected_month = request.values.get("report_month")

    if not selected_month:
        flash("Please select a valid month.", "danger")
        return redirect(url_for('reports.report_form'))

    try:
        year, month = map(int, selected_month.split("-"))
    except ValueError:
        flash("Invalid month format. Please use YYYY-MM.", "danger")
        return redirect(url_for('reports.report_form'))

    start_date = datetime(year, month, 1).date()
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day).date()
    report_month_display = start_date.strftime("%B %Y")

    # --- Sales Transactions
    sales = SalesTransaction.query.filter(SalesTransaction.transaction_date.between(start_date, end_date)).all()
    sales_transactions = []
    total_sales_qty = total_sales_weight = total_sales_amount = Decimal('0.00')
    for s in sales:
        qty = sum(i.quantity for i in s.items)
        wt = sum(Decimal(i.total_weight or 0) for i in s.items)
        amt = s.total_amount or 0
        sales_transactions.append({
            'transaction_date': s.transaction_date,
            'party': s.party,
            'bill_number': s.bill_number,
            'quantity': qty,
            'weight': wt,
            'total_amount': amt
        })
        total_sales_qty += qty
        total_sales_weight += wt
        total_sales_amount += Decimal(amt)

    # --- Purchase Transactions
    purchases = PurchaseTransaction.query.filter(PurchaseTransaction.transaction_date.between(start_date, end_date)).all()
    purchase_transactions = []
    total_purchase_qty = total_purchase_weight = total_purchase_amount = Decimal('0.00')
    for p in purchases:
        qty = sum(i.quantity for i in p.items)
        wt = sum(Decimal(i.weight or 0) for i in p.items)
        amt = p.total_amount or 0
        purchase_transactions.append({
            'transaction_date': p.transaction_date,
            'party': p.party,
            'bill_number': p.bill_number,
            'quantity': qty,
            'weight': wt,
            'total_amount': amt
        })
        total_purchase_qty += qty
        total_purchase_weight += wt
        total_purchase_amount += Decimal(amt)

    # --- Payments
    payments = Payment.query.filter(Payment.payment_date.between(start_date, end_date)).all()
    payments_received_list = [p for p in payments if p.payment_type == PaymentType.Received]
    payments_paid_list = [p for p in payments if p.payment_type == PaymentType.Paid]
    total_payments_received = sum(Decimal(p.amount or 0) for p in payments_received_list)
    total_payments_paid = sum(Decimal(p.amount or 0) for p in payments_paid_list)

    # --- Expenses
    expenses_list = Expense.query.filter(Expense.expense_date.between(start_date, end_date)).all()
    total_expenses = sum(Decimal(exp.amount or 0) for exp in expenses_list)

    # --- Stock Summary
    stock_remaining_qty = total_purchase_qty - total_sales_qty
    stock_remaining_weight = total_purchase_weight - total_sales_weight

    # --- Final Calculations
    operating_income = total_sales_amount - total_purchase_amount - total_expenses
    net_payment_flow = total_payments_received - total_payments_paid - total_expenses

    return render_template("reports/monthly_summary.html",
        report_month_display=report_month_display,
        generated_on=datetime.now(),
        generated_by=session.get("user_name", "System"),

        sales_transactions=sales_transactions,
        total_sales_qty=total_sales_qty,
        total_sales_weight=total_sales_weight,
        total_sales_amount=total_sales_amount,

        purchase_transactions=purchase_transactions,
        total_purchase_qty=total_purchase_qty,
        total_purchase_weight=total_purchase_weight,
        total_purchase_amount=total_purchase_amount,

        payments_received_list=payments_received_list,
        payments_paid_list=payments_paid_list,
        total_payments_received=total_payments_received,
        total_payments_paid=total_payments_paid,

        expenses_list=expenses_list,
        total_expenses=total_expenses,

        stock_remaining_qty=stock_remaining_qty,
        stock_remaining_weight=stock_remaining_weight,

        operating_income=operating_income,
        net_payment_flow=net_payment_flow
    )
    
def generate_outstanding_report():
    flash("🚧 Outstanding report coming soon.", "info")
    return redirect(url_for('reports.report_form'))
