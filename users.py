from app import app
from models import db, User
import hashlib

with app.app_context():
    phone = "9105245101"
    existing = User.query.filter_by(phone_number=phone).first()
    if existing:
        print("🔁 Existing user found. Deleting for test reset.")
        db.session.delete(existing)
        db.session.commit()

    pwd = hashlib.sha256("admin@123".encode()).hexdigest()
    user = User(name="Moin Khan", phone_number=phone, password=pwd)
    db.session.add(user)
    db.session.commit()
    print("✅ Test user inserted.")
