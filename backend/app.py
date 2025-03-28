# backend/app.py
import os
from dotenv import load_dotenv
from flask import Flask
from backend.routes import register_routes

load_dotenv()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, '..'))
    templates_path = os.path.join(project_root, 'frontend', 'templates')
    static_path = os.path.join(project_root, 'frontend', 'static')

    app = Flask(__name__, static_folder=static_path, template_folder=templates_path)
    app.secret_key = os.getenv('SECRET_KEY')
    
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    register_routes(app)
    return app
