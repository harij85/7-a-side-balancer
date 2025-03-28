# wsgi.py
import sys
import os

# Add the backend folder to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app_factory import create_app  # now import works since backend is in path

app = create_app()