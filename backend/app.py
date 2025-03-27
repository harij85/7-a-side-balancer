import os
from flask import Flask
from backend.routes import register_routes

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_path = os.path.join(base_dir, '..', 'frontend', 'templates')

    app = Flask(__name__, template_folder=templates_path)
    app.secret_key = '1234'

    register_routes(app)
    return app
