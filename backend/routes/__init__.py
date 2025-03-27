from flask import Flask
from backend.routes.player import player_bp
from backend.routes.admin import admin_bp
from backend.routes.draft import draft_bp
from backend.routes.auth import auth_bp
from backend.routes.captains import captains_bp
from backend.routes.home import home_bp


    
def register_routes(app):
    app.register_blueprint(player_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(draft_bp)
    app.register_blueprint(captains_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)

    return app

def create_app():
    app = Flask(__name__)
    app.secret_key = '1234'

    app.register_blueprint(player_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(draft_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(captains_bp)
    app.register_blueprint(home_bp)
    
    return app
