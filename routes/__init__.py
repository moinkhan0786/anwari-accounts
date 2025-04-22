# routes/__init__.py

from .sales import sales_bp
from .purchase import purchase_bp
from .parties import parties_bp
from .reports import reports_bp

def register_routes(app):
    """
    Register all route blueprints to the Flask app.
    """
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(purchase_bp, url_prefix='/purchase')
    app.register_blueprint(parties_bp, url_prefix='/parties')
    app.register_blueprint(reports_bp, url_prefix='/reports')
