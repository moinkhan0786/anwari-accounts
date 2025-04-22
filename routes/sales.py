from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, SalesTransaction, SalesItem, Party, Item, PartyType
from datetime import datetime

sales_bp = Blueprint('sales', __name__, template_folder='../templates/sales')

# ------------------ Add New Sale ------------------ #
@sales_bp.route('/add', methods=['GET', 'POST'])
def add_sale():
    parties = Party.query.order_by(Party.name).all()
    items = Item.query.order_by(Item.name).all()

    if request.method == 'POST':
        form_data = request.form
        try:
            transaction_date = datetime.strptime(form_data.get('transaction_date'), "%Y-%m-%d")
            party_id = int(form_data.get('party_id'))
            bill_number = form_data.get('bill_number')
            notes = form_data.get('notes')

            item_ids = form_data.getlist('item_id[]')
            quantities = form_data.getlist('quantity[]')
            avg_weights = form_data.getlist('average_weight[]')
            total_weights = form_data.getlist('total_weight[]')
            rate_per_kgs = form_data.getlist('rate_per_kg[]')

            # Calculate grand total
            grand_total = 0
            for i in range(len(item_ids)):
                qty = int(quantities[i])
                avg_wt = float(avg_weights[i])
                rate = float(rate_per_kgs[i])
                total_wt = qty * avg_wt
                total_amt = total_wt * rate
                grand_total += total_amt

            # Create sale transaction
            sale = SalesTransaction(
                transaction_date=transaction_date,
                party_id=party_id,
                total_amount=grand_total,
                bill_number=bill_number,
                notes=notes
            )
            db.session.add(sale)
            db.session.flush()  # Get sale.id before committing

            # Add sale items
            for i in range(len(item_ids)):
                sale_item = SalesItem(
                    sales_transaction_id=sale.id,
                    item_id=int(item_ids[i]),
                    quantity=int(quantities[i]),
                    average_weight=float(avg_weights[i]),
                    total_weight=float(total_weights[i]) if total_weights[i] else (int(quantities[i]) * float(avg_weights[i])),
                    rate=float(rate_per_kgs[i]),
                    total_amount=float(rate_per_kgs[i]) * float(total_weights[i] if total_weights[i] else int(quantities[i]) * float(avg_weights[i])),
                    notes=None
                )
                db.session.add(sale_item)

            db.session.commit()
            flash("✅ Sale added successfully!", "success")
            return redirect(url_for('sales.list_sales'))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error adding sale: {str(e)}", "danger")
            return render_template(
                'sales/add_sale.html',
                parties=parties,
                items=items,
                form_data=form_data,
                PartyType=PartyType,
                active_page='add_sale'
            )

    # GET request
    return render_template(
        'sales/add_sale.html',
        parties=parties,
        items=items,
        form_data=None,
        PartyType=PartyType,
        active_page='add_sale'
    )

# ------------------ List Sales ------------------ #
@sales_bp.route('/list')
def list_sales():
    sales = SalesTransaction.query.order_by(SalesTransaction.transaction_date.desc()).all()
    return render_template('sales/list_sales.html', sales=sales, active_page='list_sales')

# ------------------ View Sale Invoice ------------------ #
@sales_bp.route('/view/<int:sale_id>')
def view_sale(sale_id):
    bill = SalesTransaction.query.get_or_404(sale_id)

    # Load related party and items
    bill.party = Party.query.get(bill.party_id)
    bill.items = SalesItem.query.filter_by(sales_transaction_id=sale_id).all()
    for item in bill.items:
        item.item = Item.query.get(item.item_id)

    # Optional: Calculate amount in words
    def number_to_words(n):
        from num2words import num2words
        try:
            return num2words(n, to='currency', lang='en_IN').replace('euro', 'Rupees').replace('cents', 'Paise')
        except:
            return ""

    bill.amount_in_words = number_to_words(float(bill.total_amount or 0))
    bill.grand_total = float(bill.total_amount or 0)

    return render_template('sales/view_sale.html', bill=bill, active_page='list_sales')

# ------------------ Delete Sale ------------------ #
@sales_bp.route('/delete/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    sale = SalesTransaction.query.get_or_404(sale_id)
    try:
        db.session.delete(sale)
        db.session.commit()
        flash("🗑️ Sale deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error deleting sale: {str(e)}", "danger")

    return redirect(url_for('sales.list_sales'))
