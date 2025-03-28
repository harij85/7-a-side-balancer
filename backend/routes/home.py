# backend/routes/home.py
from flask import Blueprint, render_template, session
from backend.utils.data_manager import load_players

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/')
def index():
    # Clear player session if admin is active
    if session.get('is_admin') and session.get('player_id'):
        session.pop('player_id')

    players = load_players()
    is_admin = session.get('is_admin', False)
    
    # ✅ Add this logic
    captain_count = sum(1 for p in players if p.is_captain)
    can_assign_more = captain_count < 2

    return render_template(
        'index.html',
        players=players,
        is_admin=is_admin,
        can_assign_more=can_assign_more  # ✅ Include this
    )
