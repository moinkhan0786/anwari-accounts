# routes/login.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User
from datetime import datetime
import hashlib

login_bp = Blueprint('login_bp', __name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@login_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@login_bp.route('/login', methods=['POST'])
def login_submit():
    phone_number = request.form.get('phoneNumber')
    password = request.form.get('password')

    # Validation
    if not phone_number or not password:
        flash("📱 Phone number and password are required.", "danger")
        return redirect(url_for('login_bp.login_page'))

    # User lookup
    user = User.query.filter_by(phone_number=phone_number).first()

    if not user:
        flash("❌ No user found with this phone number.", "danger")
        return redirect(url_for('login_bp.login_page'))

    if user.password != hash_password(password):
        flash("🔒 Incorrect password. Please try again.", "danger")
        return redirect(url_for('login_bp.login_page'))

    # Login Success
    session['user_id'] = user.id
    session['user_name'] = user.name
    flash(f"👋 Welcome back, {user.name}!", "success")
    return redirect(url_for('home'))  # 🔁 Make sure this route exists

@login_bp.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for('login_bp.login_page'))
