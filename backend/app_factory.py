import os
from flask import Flask
from backend.routes.player_routes import player_bp
from backend.routes.admin import admin_bp
from backend.routes.draft import draft_bp
from backend.routes.auth import auth_bp
from backend.routes.captains import captains_bp
from backend.routes.home import home_bp

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_path = os.path.join(base_dir, '..', 'frontend', 'templates')  # adjust if needed

    app = Flask(__name__, template_folder=templates_path)
    app.secret_key = 'your-secret-key'  # You can use a secure random key here

    # ✅ Register Blueprints (do this BEFORE returning)
    app.register_blueprint(player_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(draft_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(captains_bp)
    app.register_blueprint(home_bp)

    return app  # ✅ Final return