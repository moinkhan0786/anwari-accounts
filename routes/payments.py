from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import db, Payment, Party, PaymentType, PartyType

payments_bp = Blueprint('payments', __name__, template_folder='../templates/payments')

# ------------------- List All Payments -------------------
@payments_bp.route('/list', methods=['GET'])
def list_payments():
    payments = db.session.query(Payment).join(Party).order_by(Payment.payment_date.desc()).all()
    return render_template(
        'payments/payments_list.html',
        payments=payments,
        active_page='payments'
    )

# ------------------- Add New Payment -------------------
@payments_bp.route('/add', methods=['GET', 'POST'])
def add_payment():
    parties = Party.query.order_by(Party.name).all()
    payment_modes = ["Cash", "Bank Transfer", "Cheque", "UPI", "RTGS"]

    if request.method == 'POST':
        form_data = request.form
        try:
            # Extract form data
            party_id = int(form_data.get("party_id"))
            payment_date = datetime.strptime(form_data.get("payment_date"), "%Y-%m-%d").date()
            payment_type = form_data.get("payment_type")
            amount = float(form_data.get("amount"))
            payment_mode = form_data.get("payment_mode")
            reference = form_data.get("reference", "").strip()
            notes = form_data.get("notes", "").strip()

            # Validate payment type
            if payment_type not in ['Paid', 'Received']:
                raise ValueError("Invalid payment type selected.")

            # Save to database
            new_payment = Payment(
                party_id=party_id,
                payment_date=payment_date,
                payment_type=PaymentType(payment_type),
                amount=amount,
                payment_mode=payment_mode,
                reference=reference,
                notes=notes
            )
            db.session.add(new_payment)
            db.session.commit()

            flash("✅ Payment saved successfully!", "success")
            return redirect(url_for("payments.list_payments"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error saving payment: {str(e)}", "danger")
            return render_template(
                "payments/add_payment.html",
                parties=parties,
                form_data=form_data,
                payment_modes=payment_modes,
                PaymentType=PaymentType,
                PartyType=PartyType,
                active_page="add_payment"
            )

    # GET request
    return render_template(
        "payments/add_payment.html",
        parties=parties,
        form_data=None,
        payment_modes=payment_modes,
        PaymentType=PaymentType,
        PartyType=PartyType,
        active_page="add_payment"
    )
