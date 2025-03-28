# backend/routes/home.py
from flask import Blueprint, render_template, session
from backend.utils.data_manager import load_players, load_draft_state
from datetime import datetime, timedelta
from backend.utils.draft_timer import get_draft_window


home_bp = Blueprint('home_bp', __name__)

def is_draft_window_open():
    now = datetime.now()
    start = now - timedelta(days=now.weekday() - 1)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=4, hours=23, minutes=59, seconds=59)
    return start <= now <= end



@home_bp.route('/')
def index():
    # Clear player session if admin is active
    
        
    is_admin = session.get('is_admin', False)
    draft_state = load_draft_state()
    draft_window_open = is_draft_window_open()

    players = load_players()
    for player in players:
        if len(player.match_history) >= 2:
            last = player.match_history[-1].rating
            second_last = player.match_history[-2].rating
            player.rating_diff = round(last - second_last, 2)
        else:
            player.rating_diff = 0
            
    players = sorted(players, key=lambda x: x.skill_rating, reverse=True)
    
    is_admin = session.get('is_admin', False)
    
    # ✅ Add this logic
    captain_count = sum(1 for p in players if p.is_captain)
    can_assign_more = captain_count < 2
    
    draft_start, draft_end = get_draft_window()


    return render_template(
        'index.html',
        players=players,
        is_admin=is_admin,
        draft_state=draft_state,
        draft_window_open=draft_window_open,
        can_assign_more=can_assign_more,# ✅ Include this
        draft_start=draft_start,
        draft_end=draft_end  
    )
