# backend/app.py
import os
from flask import Flask
from backend.routes import register_routes

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, '..'))
    templates_path = os.path.join(project_root, 'frontend', 'templates')
    static_path = os.path.join(project_root, 'frontend', 'static')

    app = Flask(__name__, static_folder=static_path, template_folder=templates_path)
    app.secret_key = '1234'

    register_routes(app)
    return app
