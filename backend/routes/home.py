# backend/routes/home.py
from flask import Blueprint, render_template, session, request
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

@home_bp.route('/view_players')
def view_players():
    players = load_players()

    # Role check
    is_admin = session.get('is_admin', False)
    player_id = session.get('player_id', None)

    # Find current player (for navbar notifications)
    current_player = next((p for p in players if p.id == player_id), None)

    # Filter Logic
    search = request.args.get('search', '').lower()
    position = request.args.get('position', '')
    availability = request.args.get('availability', '')

    filtered_players = []
    for player in players:
        if search and search not in player.name.lower():
            continue
        if position and player.position != position:
            continue
        if availability:
            if availability == 'available' and not player.available:
                continue
            if availability == 'unavailable' and player.available:
                continue
        filtered_players.append(player)

    # Sort by skill_rating (descending)
    filtered_players.sort(key=lambda p: p.skill_rating, reverse=True)

    return render_template(
        'view_players.html',
        players=filtered_players,
        is_admin=is_admin,
        player_id=player_id,
        player=current_player  # 🟢 Add this
    )


@home_bp.route('/view_player_stats/<player_id>')
def view_player_stats(player_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403

    players = load_players()
    target_player = next((p for p in players if p.id == player_id), None)
    if not target_player:
        return "Player not found", 404

    return render_template('view_player_stats.html', player=target_player)
