from flask import Blueprint, render_template, redirect, url_for, session, request
from datetime import datetime, timedelta
from backend.utils.data_manager import load_players, save_players, generate_unique_code, load_draft_state
from backend.models.player import PerformanceLog
from backend.utils.draft_timer import get_draft_window


player_bp = Blueprint('player_bp', __name__)



@player_bp.route('/player/<player_id>', methods=['GET', 'POST'])
def player_page(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if not player:
        return "Player not found", 404

    session['player_id'] = player_id

    if request.method == 'POST':
        goals = int(request.form['goals'])
        assists = int(request.form['assists'])
        tackles = int(request.form['tackles'])
        saves = int(request.form['saves'])

        rating = (goals * 2.5 + assists * 1.5 + tackles * 1.0 + saves * 1.5) / 2.0
        rating = max(1.0, min(round(rating, 2), 10.0))

        log = PerformanceLog(goals=goals, assists=assists, tackles=tackles, saves=saves, rating=rating)
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)
        return render_template('thanks.html', player=player)

    draft_state = load_draft_state()
    show_draft_panel = False
    draft_context = {}

    if draft_state and player.is_captain:
        get_player = lambda pid: next((p for p in players if p.id == pid), None)
        if draft_state.get("complete"):
            show_draft_panel = False 
            draft_context = {
                'captain_id': player.id,
                'this_captain': player,
                'is_my_turn': False,
                'remaining': [],
                'team1': [p for pid in draft_state['team1'] if (p := get_player(pid))],
                'team2': [p for pid in draft_state['team2'] if (p := get_player(pid))],
                'captain1': get_player(draft_state['captain1_id']),
                'captain2': get_player(draft_state['captain2_id']),
                'turn': None
            }
        else:
            show_draft_panel = True
            draft_context = {
                'captain_id': player.id,
                'this_captain': player,
                'is_my_turn': draft_state['turn'] == player_id,
                'remaining': [p for pid in draft_state['remaining_ids'] if (p := get_player(pid))],
                'team1': [p for pid in draft_state['team1'] if (p := get_player(pid))],
                'team2': [p for pid in draft_state['team2'] if (p := get_player(pid))],
                'captain1': get_player(draft_state['captain1_id']),
                'captain2': get_player(draft_state['captain2_id']),
                'turn': get_player(draft_state['turn'])
            }

    ratings = [log.rating for log in player.match_history]
    
    draft_start, draft_end = get_draft_window()
    
    return render_template(
        'player_portal.html',
        player=player,
        ratings=ratings,
        show_draft_panel=show_draft_panel,
        draft_context=draft_context,
        draft_state=draft_state,
        draft_start=draft_start.isoformat(),
        draft_end=draft_end.isoformat(),
        is_admin=session.get('is_admin', False)
    )

@player_bp.route('/player_profile/<target_id>', methods=['GET', 'POST'])
def player_profile(target_id):
    players = load_players()
    viewer_id = session.get('player_id')
    is_admin = session.get('is_admin', False)

    target_player = next((p for p in players if p.id == target_id), None)
    viewer = next((p for p in players if p.id == viewer_id), None)

    if not target_player:
        return "Player not found", 403

    if not viewer and not is_admin:
        return "Unauthorized", 403

    if target_id == viewer_id:
        return "You cannot rate yourself", 403

    recent_log = target_player.match_history[-1] if target_player.match_history else None
    match_id = recent_log.match_id if recent_log else None

    has_already_rated = any(
        r['from'] == viewer_id and r['match_id'] == match_id
        for r in target_player.ratings_received
    )

    if request.method == 'POST' and match_id and not has_already_rated:
        rating = int(request.form['rating'])
        comment = request.form.get('comment', '')

        target_player.ratings_received.append({
            "from": viewer_id,
            "match_id": match_id,
            "rating": rating,
            "comment": comment
        })

        message = {
            "type": "rating_received",
            "from": viewer.name,
            "rating": rating,
            "comment": comment,
            "match_id": match_id,
            "timestamp": datetime.now().isoformat()
        }

        target_player.notifications.append(message)
        target_player.inbox.append(message)
        
        previous_rating = target_player.skill_rating
        save_players(players)
        rating_diff = round(target_player.skill_rating - previous_rating, 2)
        return render_template('thanks.html', 
                               player=viewer, 
                               message="Rating submitted!", 
                               rating_diff=rating_diff)

    return render_template('player_profile.html', 
                           target=target_player, 
                           recent_log=recent_log, 
                           viewer_id=viewer_id, 
                           has_already_rated=has_already_rated,
                           is_admin=is_admin)

@player_bp.route('/log_performance/<player_id>', methods=['GET', 'POST'])
def log_performance(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if not player:
        return "Player not found", 404

    user_id = session.get('player_id')
    is_admin = session.get('is_admin', False)
    if user_id != player_id and not is_admin:
        return "Unauthorized", 403

    if request.method == 'POST':
        goals = int(request.form['goals'])
        assists = int(request.form['assists'])
        tackles = int(request.form['tackles'])
        saves = int(request.form['saves'])
        
        previous_rating = player.skill_rating
        
        rating = (goals * 2.5 + assists * 1.5 + tackles * 1.0 + saves * 1.5) / 2.0
        rating = max(1.0, min(round(rating, 2), 10.0))

        log = PerformanceLog(goals=goals, 
                             assists=assists, 
                             tackles=tackles, 
                             saves=saves, 
                             rating=rating
                             )
        
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)
        
        rating_diff = round(player.skill_rating - previous_rating, 2)

        return render_template('thanks.html', 
                               player=player, 
                               current_rating=player.skill_rating, 
                               rating_diff=rating_diff, 
                               message="Stats submitted!")

    return render_template('log_performance.html', player=player)

@player_bp.route('/regenerate_code/<player_id>', methods=['POST'])
def regenerate_code(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if not player or session.get('player_id') != player_id:
        return "Unauthorized", 403

    existing_codes = {p.access_code for p in players if p.id != player_id}
    player.access_code = generate_unique_code(existing_codes)
    save_players(players)

    return redirect(url_for('player_bp.player_page', player_id=player_id))


@player_bp.route('/toggle_availability/<player_id>', methods=['POST'])
def toggle_availability(player_id):
    players = load_players()
    user_id = session.get('player_id')
    is_admin = session.get('is_admin', False)

    updated_player = None

    if user_id != player_id and not is_admin:
        return "Unauthorized", 403

    for player in players:
        if player.id == player_id:
            player.available = not player.available
            updated_player = player
            break

    if updated_player:
        save_players(players)

    if user_id == player_id:
        return redirect(url_for('player_bp.player_page', player_id=player_id))
    elif is_admin:
        return redirect(url_for('home_bp.index'))
    else:
        return redirect(request.referrer or url_for('home_bp.index'))


@player_bp.route('/inbox/<player_id>')
def player_inbox(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if session.get('player_id') != player_id and not session.get('is_admin'):
        return "Unauthorized", 403


    return render_template('player_inbox.html', player=player, inbox=player.inbox)

@player_bp.route('/clear_notifications/<player_id>', methods=['POST'])
def clear_notifications(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if player and session.get('player_id') == player_id:
        player.notifications = []
        save_players(players)
    return redirect(url_for('player_bp.player_page', player_id=player_id))
