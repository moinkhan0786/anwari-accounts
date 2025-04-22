# routes/expense.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from sqlalchemy import func
from models import db, Expense, ExpenseCategory
from datetime import datetime, timedelta

expense_bp = Blueprint('expense', __name__, url_prefix='/expenses')

@expense_bp.route('/')
def list_expenses():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    period_filter = request.args.get('period_filter', 'custom')

    # Default period - this month
    today = date.today()
    start_date = end_date = None

    if period_filter == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif period_filter == 'last_month':
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period_filter == 'this_fy':
        fy_start = date(today.year if today.month > 3 else today.year - 1, 4, 1)
        start_date = fy_start
        end_date = today
    elif period_filter == 'custom':
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    expenses_query = Expense.query
    if start_date:
        expenses_query = expenses_query.filter(Expense.expense_date >= start_date)
    if end_date:
        expenses_query = expenses_query.filter(Expense.expense_date <= end_date)

    expenses_query = expenses_query.order_by(Expense.expense_date.desc())
    expenses = expenses_query.all()

    total_expenses = sum([float(exp.amount) for exp in expenses])

    return render_template("expense/list_expenses.html",
                           expenses=expenses,
                           total_expenses=total_expenses,
                           active_page="expenses")

@expense_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    payment_modes = ['Cash', 'Bank Transfer', 'UPI', 'Cheque', 'Card', 'Other']
    form_data = {}
    error = None

    if request.method == 'POST':
        try:
            # Capture and store form inputs in case of validation failure
            form_data = {
                'expense_date': request.form.get('expense_date'),
                'category_id': request.form.get('category_id'),
                'amount': request.form.get('amount'),
                'payment_mode': request.form.get('payment_mode'),
                'reference': request.form.get('reference'),
                'notes': request.form.get('notes'),
            }

            # Validate and convert inputs
            expense_date = datetime.strptime(form_data['expense_date'], '%Y-%m-%d').date()
            category_id = int(form_data['category_id'])
            amount = float(form_data['amount'])

            new_exp = Expense(
                expense_date=expense_date,
                category_id=category_id,
                amount=amount,
                payment_mode=form_data['payment_mode'],
                reference=form_data['reference'],
                notes=form_data['notes']
            )

            db.session.add(new_exp)
            db.session.commit()

            flash("✅ Expense added successfully.", "success")
            return redirect(url_for('expense.list_expenses'))

        except Exception as e:
            db.session.rollback()
            error = f"❌ Failed to add expense: {str(e)}"
            flash(error, "danger")

    return render_template("expense/add_expense.html",
                           categories=categories,
                           payment_modes=payment_modes,
                           form_data=form_data,
                           error=error,
                           active_page="add_expense")


@expense_bp.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    try:
        db.session.delete(expense)
        db.session.commit()
        flash("✅ Expense deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Could not delete expense: {str(e)}", "danger")
    return redirect(url_for('expense.list_expenses'))

@expense_bp.route('/category/add', methods=['GET', 'POST'])
def add_category():
    error = None
    form_data = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        form_data['name'] = name

        if not name:
            error = "Category name is required."
        elif ExpenseCategory.query.filter_by(name=name).first():
            error = f"Category '{name}' already exists."
        else:
            try:
                new_cat = ExpenseCategory(name=name)
                db.session.add(new_cat)
                db.session.commit()
                flash("✅ Category created successfully.", "success")
                return redirect(url_for('expense.list_expenses'))
            except Exception as e:
                db.session.rollback()
                error = f"❌ Failed to save category: {str(e)}"

    return render_template("expense/add_category.html",
                           error=error,
                           form_data=form_data,
                           active_page="expenses")
