from flask import Flask, redirect, url_for, session, request, render_template
from datetime import timedelta, date
from sqlalchemy import func
import os
import sys

# Models & DB
from models import db, User, Party, Item, PurchaseTransaction, PurchaseItem, SalesTransaction, SalesItem

# Blueprints
from routes.login import login_bp
from routes.parties import parties_bp
from routes.purchase import purchase_bp
from routes.sales import sales_bp
from routes.reports import reports_bp
from routes.payments import payments_bp
from routes.expense import expense_bp

# ------------------- Determine Environment & Safe DB Path -------------------

def get_safe_db_path():
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable (PyInstaller / Inno Setup)
        appdata_path = os.getenv('APPDATA') or os.path.expanduser("~\\AppData\\Roaming")
        safe_dir = os.path.join(appdata_path, "AnwariAccounts")
    else:
        # Running in dev mode (Python script)
        safe_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
    os.makedirs(safe_dir, exist_ok=True)
    return os.path.join(safe_dir, "anwari_local.db")

# ------------------- Flask App Setup -------------------

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.permanent_session_lifetime = timedelta(days=30)

# ------------------- Database Configuration -------------------

db_path = get_safe_db_path()
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ------------------- Create Tables -------------------

with app.app_context():
    db.create_all()

# ------------------- Register Blueprints -------------------

app.register_blueprint(login_bp)
app.register_blueprint(parties_bp, url_prefix='/parties')
app.register_blueprint(purchase_bp, url_prefix='/purchase')
app.register_blueprint(sales_bp, url_prefix='/sales')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(payments_bp, url_prefix='/payments')
app.register_blueprint(expense_bp, url_prefix='/expense')

# ------------------- Authentication Middleware -------------------

@app.before_request
def require_login():
    allowed_routes = ['login_bp.login_page', 'login_bp.login_submit', 'static']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login_bp.login_page'))

# ------------------- Dashboard Route -------------------

@app.route('/')
def home():
    today = date.today()

    total_purchased = db.session.query(func.sum(PurchaseItem.quantity)) \
        .join(PurchaseTransaction) \
        .filter(PurchaseTransaction.transaction_date == today).scalar() or 0

    total_sold = db.session.query(func.sum(SalesItem.quantity)) \
        .join(SalesTransaction) \
        .filter(SalesTransaction.transaction_date == today).scalar() or 0

    total_revenue = db.session.query(func.sum(SalesItem.total_amount)) \
        .join(SalesTransaction) \
        .filter(SalesTransaction.transaction_date == today).scalar() or 0

    profit = round(total_revenue * 0.25, 2)

    recent_sales = SalesTransaction.query.options(
        db.joinedload(SalesTransaction.items).joinedload(SalesItem.item),
        db.joinedload(SalesTransaction.party)
    ).order_by(SalesTransaction.transaction_date.desc()).limit(3).all()

    recent_purchases = PurchaseTransaction.query.options(
        db.joinedload(PurchaseTransaction.items).joinedload(PurchaseItem.item),
        db.joinedload(PurchaseTransaction.party)
    ).order_by(PurchaseTransaction.transaction_date.desc()).limit(3).all()

    return render_template(
        'dashboard.html',
        user_name=session.get('user_name'),
        total_purchased=total_purchased,
        total_sold=total_sold,
        total_revenue=total_revenue,
        profit=profit,
        recent_sales=recent_sales,
        recent_purchases=recent_purchases,
        active_page='dashboard'
    )

# ------------------- Run Server -------------------

if __name__ == '__main__':
    app.run(debug=True)
