# backend/app_factory.py
import os
from dotenv import load_dotenv
from flask import Flask
from backend.routes.player_routes import player_bp
from backend.routes.admin import admin_bp
from backend.routes.draft import draft_bp  # Consolidated draft logic here
from backend.routes.auth import auth_bp
from backend.routes.home import home_bp
from backend.utils.data_manager import ensure_data_dir_exists

load_dotenv()

def create_app():
    ensure_data_dir_exists() # Ensure data directory exists on startup

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # Assuming 'frontend' is at the same level as 'backend' in the project root
    templates_path = os.path.join(project_root, 'frontend', 'templates')
    static_path = os.path.join(project_root, 'frontend', 'static')

    app = Flask(__name__,
                template_folder=templates_path,
                static_folder=static_path)

    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key') # Provide a default for dev
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production' # Secure only in prod
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Register Blueprints
    app.register_blueprint(player_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(draft_bp) # Single draft blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    # Removed captains_bp registration

    # You might want to add context processors here later
    # Example: To make 'is_admin' available globally in templates
    # @app.context_processor
    # def inject_user_status():
    #     from flask import session
    #     return dict(is_admin=session.get('is_admin', False),
    #                 player_id=session.get('player_id'))


    return app