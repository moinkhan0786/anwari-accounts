from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

# ------------------- Enum Definitions -------------------
class PartyType(enum.Enum):
    Supplier = 'Supplier'
    Customer = 'Customer'

class PaymentType(enum.Enum):
    Received = 'Received'
    Paid = 'Paid'

# ------------------- User Table -------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ------------------- Party Table -------------------
class Party(db.Model):
    __tablename__ = 'party'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    party_type = db.Column(db.Enum(PartyType), nullable=False)
    address = db.Column(db.Text)
    contact_info = db.Column(db.String(255))
    pan_number = db.Column(db.String(15))
    gstin_number = db.Column(db.String(20))
    bank_account_name = db.Column(db.String(255))
    bank_account_number = db.Column(db.String(50))
    bank_ifsc_code = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_transactions = db.relationship('PurchaseTransaction', backref='party', lazy=True)
    sales_transactions = db.relationship('SalesTransaction', back_populates='party', cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='party', lazy=True)

# ------------------- Item Table -------------------
class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_items = db.relationship('PurchaseItem', back_populates='item')
    sales_items = db.relationship('SalesItem', back_populates='item')

# ------------------- Purchase Transactions -------------------
class PurchaseTransaction(db.Model):
    __tablename__ = 'purchase_transaction'
    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.Date, nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey('party.id'), nullable=False)

    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    bill_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    tag_number = db.Column(db.String(100), nullable=True)
    generated_by = db.Column(db.String(100), nullable=True)
    counted_by = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('PurchaseItem', back_populates='purchase', cascade="all, delete-orphan")

# ------------------- Purchase Item Table -------------------
class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase_transaction.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Numeric(10, 2), nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    tag_number = db.Column(db.String(100), nullable=True)

    # Relationships
    purchase = db.relationship('PurchaseTransaction', back_populates='items')
    item = db.relationship('Item', back_populates='purchase_items')

# ------------------- Sales Transactions -------------------
class SalesTransaction(db.Model):
    __tablename__ = 'sales_transaction'
    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.Date, nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey('party.id'), nullable=False)

    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    bill_number = db.Column(db.String(100))
    sales_period_start = db.Column(db.Date)
    sales_period_end = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    party = db.relationship('Party', back_populates='sales_transactions')
    items = db.relationship('SalesItem', back_populates='sale', cascade="all, delete-orphan")

# ------------------- Sales Item Table -------------------
class SalesItem(db.Model):
    __tablename__ = 'sales_items'
    id = db.Column(db.Integer, primary_key=True)
    sales_transaction_id = db.Column(db.Integer, db.ForeignKey('sales_transaction.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    average_weight = db.Column(db.Float, nullable=False)
    total_weight = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)

    # Relationships
    sale = db.relationship('SalesTransaction', back_populates='items')
    item = db.relationship('Item', back_populates='sales_items')

# ------------------- Payments -------------------
class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('party.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.Enum(PaymentType), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_mode = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_mode = db.Column(db.String(50), nullable=True)
    reference = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('ExpenseCategory')
