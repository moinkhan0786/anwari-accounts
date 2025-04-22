# routes/purchase.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import db, PurchaseTransaction, Party, Item, PartyType, PurchaseItem
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import joinedload

purchase_bp = Blueprint('purchase', __name__, template_folder='../templates/purchase')

@purchase_bp.route('/add', methods=['GET', 'POST'])
def add_purchase():
    if request.method == 'POST':
        try:
            data = request.form
            party_id = data.get('party_id')
            transaction_date_str = data.get('transaction_date')

            if not party_id or not transaction_date_str:
                flash('❌ Please select a date and party.', 'danger')
                raise ValueError("Missing main form data")

            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()

            item_ids = request.form.getlist('item_id[]')
            quantities = request.form.getlist('quantity[]')
            weights = request.form.getlist('weight[]')
            prices = request.form.getlist('price[]')

            if not item_ids or not quantities or not prices:
                flash('❌ No purchase items found.', 'danger')
                raise ValueError("Missing item details")

            bill_number = data.get('bill_number')
            notes = data.get('notes')
            tag_number = data.get('tag_number')
            generated_by = data.get('generated_by')
            counted_by = data.get('counted_by')

            # Calculate grand total
            grand_total = Decimal(0)
            for i in range(len(item_ids)):
                quantity = int(quantities[i])
                price = Decimal(prices[i])
                grand_total += quantity * price

            # Create main PurchaseTransaction
            purchase = PurchaseTransaction(
                transaction_date=transaction_date,
                party_id=int(party_id),
                total_amount=grand_total,
                bill_number=bill_number,
                notes=notes,
                generated_by=generated_by,
                counted_by=counted_by
            )
            db.session.add(purchase)
            db.session.flush()  # Get purchase.id before committing

            # Create PurchaseItems
            for i in range(len(item_ids)):
                item_id = int(item_ids[i])
                quantity = int(quantities[i])
                price = Decimal(prices[i])
                weight = Decimal(weights[i]) if weights[i] else None
                amount = quantity * price

                item_entry = PurchaseItem(
                    purchase_id=purchase.id,
                    item_id=item_id,
                    quantity=quantity,
                    weight=weight,
                    price=price,
                    amount=amount,
                    tag_number=tag_number
                )
                db.session.add(item_entry)

            db.session.commit()
            flash('✅ Purchase bill saved successfully!', 'success')
            return redirect(url_for('purchase.list_purchases'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')

    parties = Party.query.order_by(Party.name).all()
    items = Item.query.order_by(Item.name).all()
    return render_template('purchase/add_purchase.html',
                           parties=parties,
                           items=items,
                           active_page='add_purchase',
                           PartyType=PartyType)

@purchase_bp.route('/list')
def list_purchases():
    purchases = PurchaseTransaction.query.options(
        joinedload(PurchaseTransaction.party)
    ).order_by(PurchaseTransaction.transaction_date.desc()).all()
    return render_template('purchase/list_purchases.html',
                           purchases=purchases,
                           active_page='list_purchases')

@purchase_bp.route('/delete/<int:purchase_id>', methods=['POST'])
def delete_purchase(purchase_id):
    purchase = PurchaseTransaction.query.get_or_404(purchase_id)
    try:
        db.session.delete(purchase)
        db.session.commit()
        flash('🗑️ Purchase deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error deleting purchase: {str(e)}', 'danger')
    return redirect(url_for('purchase.list_purchases'))

@purchase_bp.route('/view/<int:purchase_id>')
def view_purchase(purchase_id):
    purchase = PurchaseTransaction.query.options(
        joinedload(PurchaseTransaction.party),
        joinedload(PurchaseTransaction.items).joinedload(PurchaseItem.item)
    ).get_or_404(purchase_id)

    item_details = [
        {
            "item": i.item,
            "quantity": i.quantity,
            "weight": i.weight,
            "price": i.price,
            "amount": i.amount,
            "tag_number": i.tag_number
        }
        for i in purchase.items
    ]

    grand_total = sum(i['amount'] for i in item_details)

    bill = {
        "id": purchase.id,
        "transaction_date": purchase.transaction_date,
        "bill_number": purchase.bill_number,
        "party": purchase.party,
        "items": item_details,
        "notes": purchase.notes,
        "generated_by": purchase.generated_by,
        "counted_by": purchase.counted_by,
        "grand_total": grand_total,
        "amount_in_words": None  # Implement num2words if needed
    }

    return render_template("purchase/view_purchase.html", bill=bill)