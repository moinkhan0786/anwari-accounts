from models import db, Item
from flask import Flask
import os

# --- Setup Flask app ---
app = Flask(__name__)

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
db_path = os.path.join(DB_DIR, 'anwari_local.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- Add Items ---
with app.app_context():
    items_to_add = ['Sheep', 'Goat']
    added_count = 0

    for item_name in items_to_add:
        existing = Item.query.filter_by(name=item_name).first()
        if not existing:
            new_item = Item(name=item_name, description=f'{item_name} livestock')
            db.session.add(new_item)
            added_count += 1
        else:
            print(f"⚠️ Item '{item_name}' already exists.")

    if added_count:
        db.session.commit()
        print(f"✅ Added {added_count} new item(s).")
    else:
        print("✅ No new items to add.")
