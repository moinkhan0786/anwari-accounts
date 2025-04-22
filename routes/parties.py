# routes/parties.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from decimal import Decimal # USE DECIMAL
import re
from datetime import datetime

# Ensure all relevant models are imported
from models import db, Party, PartyType, PurchaseTransaction, PurchaseItem, SalesTransaction, SalesItem, Item, Payment, PaymentType

parties_bp = Blueprint('parties', __name__, template_folder='../templates')

def slugify(text):
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

# --- CORRECTED Statement Generation based on Accounting Principles ---
def generate_statement_entries(party):
    entries = []
    all_events = []

    purchases = PurchaseTransaction.query.options(
        joinedload(PurchaseTransaction.items).joinedload(PurchaseItem.item)
    ).filter_by(party_id=party.id).all()

    sales = SalesTransaction.query.options(
        joinedload(SalesTransaction.items).joinedload(SalesItem.item)
    ).filter_by(party_id=party.id).all()

    payments = Payment.query.filter_by(party_id=party.id).all()

    for p in purchases:
        total_purchase_amount = sum(Decimal(item.amount or '0.00') for item in p.items)
        all_events.append((p.transaction_date, 'Purchase', p, total_purchase_amount))

    for s in sales:
        total_sales_amount = sum(Decimal(item.total_amount or '0.00') for item in s.items)
        all_events.append((s.transaction_date, 'Sale', s, total_sales_amount))

    for p in payments:
        all_events.append((p.payment_date, 'Payment', p, Decimal(p.amount or '0.00')))

    all_events.sort(key=lambda x: x[0])

    running_balance = Decimal('0.00')
    for event_date, event_type, event_obj, amount in all_events:
        debit = Decimal('0.00')
        credit = Decimal('0.00')
        particulars = ""

        if event_type == 'Purchase':
            particulars = f"Purchase Bill: {event_obj.bill_number or 'N/A'}"
            if party.party_type == PartyType.Supplier:
                credit = amount
            elif party.party_type == PartyType.Customer:
                credit = amount
                particulars = f"Purchase/Return from Cust - Bill: {event_obj.bill_number or 'N/A'}"

        elif event_type == 'Sale':
            particulars = f"Sale Bill: {event_obj.bill_number or 'N/A'}"
            if party.party_type == PartyType.Customer:
                debit = amount
            elif party.party_type == PartyType.Supplier:
                debit = amount
                particulars = f"Sale to Supp - Bill: {event_obj.bill_number or 'N/A'}"

        elif event_type == 'Payment':
            if event_obj.payment_type == PaymentType.Received:
                particulars = f"Payment Received - Ref: {event_obj.reference or event_obj.payment_mode or 'N/A'}"
                credit = amount
            elif event_obj.payment_type == PaymentType.Paid:
                particulars = f"Payment Paid - Ref: {event_obj.reference or event_obj.payment_mode or 'N/A'}"
                debit = amount

        running_balance = running_balance + debit - credit

        entries.append({
            'date': event_date,
            'particulars': particulars,
            'debit': debit,
            'credit': credit,
            'running_balance': running_balance
        })

    current_balance = running_balance
    return entries, current_balance

@parties_bp.route('/view/<int:party_id>-<string:slug>', methods=['GET'])
def view_party_by_slug(party_id, slug):
    party = Party.query.get_or_404(party_id)

    expected_slug = slugify(party.name)
    if slug != expected_slug:
        return redirect(url_for('parties.view_party_by_slug', party_id=party.id, slug=expected_slug))

    statement_entries, current_balance = generate_statement_entries(party)

    balance_status_class = 'neutral'
    balance_label = ""
    specific_balance_label = ""

    if current_balance > Decimal('0.00'):
        balance_status_class = 'debit-balance'
        balance_label = f"{current_balance:,.2f} Dr"
        specific_balance_label = "Advance Paid" if party.party_type == PartyType.Supplier else "Receivable"
    elif current_balance < Decimal('0.00'):
        balance_status_class = 'credit-balance'
        balance_label = f"{abs(current_balance):,.2f} Cr"
        specific_balance_label = "Payable" if party.party_type == PartyType.Supplier else "Advance Received"
    else:
        balance_status_class = 'neutral'
        balance_label = "0.00"
        specific_balance_label = "Settled"

    return render_template(
        'party_detail.html',
        party=party,
        PartyType=PartyType,
        statement_entries=statement_entries,
        current_balance=current_balance,
        balance_status_class=balance_status_class,
        balance_label=balance_label,
        specific_balance_label=specific_balance_label,
        active_page='parties'
    )

@parties_bp.route('/list', methods=['GET'])
def list_parties():
    parties = Party.query.order_by(Party.name.asc()).all()
    return render_template('parties.html', parties=parties, PartyType=PartyType, active_page='parties')

@parties_bp.route('/add', methods=['GET', 'POST'])
def add_party():
    if request.method == 'POST':
        pass
    return render_template('add_party.html', form_data=None, party_types=[pt.value for pt in PartyType], active_page='parties')
