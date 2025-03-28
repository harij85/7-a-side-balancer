from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from backend.utils.data_manager import load_players, save_players, load_draft_state, save_draft_state
from backend.models.player import Player

captains_bp = Blueprint('captains_bp', __name__)

@captains_bp.route('/draft/captain/<captain_id>')
def captain_draft_view(captain_id):
    state = load_draft_state()
    if not state or captain_id not in [state['captain1_id'], state['captain2_id']]:
        return "Unauthorized", 403

    players = load_players()
    get_player = lambda pid: next(p for p in players if p.id == pid)

    context = {
        'captain_id': captain_id,
        'this_captain': get_player(captain_id),
        'captain1': get_player(state['captain1_id']),
        'captain2': get_player(state['captain2_id']),
        'team1': [get_player(pid) for pid in state['team1']],
        'team2': [get_player(pid) for pid in state['team2']],
        'remaining': [get_player(pid) for pid in state['remaining_ids']],
        'turn': get_player(state['turn']),
        'is_my_turn': state['turn'] == captain_id
    }

    return render_template('captain_draft.html', **context)

@captains_bp.route('/draft/pick/<player_id>', methods=['POST'])
def draft_pick(player_id):
    state = load_draft_state()
    captain_id = request.form.get('captain_id')

    if not state or player_id not in state['remaining_ids']:
        return "Invalid pick", 400

    if captain_id != state['turn']:
        return "It's not your turn!", 403

    if state['turn'] == state['captain1_id']:
        state['team1'].append(player_id)
        next_turn = state['captain2_id']
    else:
        state['team2'].append(player_id)
        next_turn = state['captain1_id']

    state['remaining_ids'].remove(player_id)

    if not state['remaining_ids']:
        players = load_players()
        complete_message = "Draft is complete."
        for cap_id in [state['captain1_id'], state['captain2_id']]:
            captain = next((p for p in players if p.id == cap_id), None)
            if captain:
                captain.notifications.append({
                    "message": complete_message,
                    "timestamp": datetime.now().isoformat()
                })
        save_players(players)
        state['complete'] = True
        state['turn'] = None
    else:
        state['turn'] = next_turn

    save_draft_state(state)
    session['draft_state'] = state

    if state.get('complete'):
        return redirect(url_for('captains.draft_final_view', captain_id=captain_id))
    else:
        return redirect(url_for('players.player_page', player_id=captain_id))

@captains_bp.route('/draft/final/<captain_id>')
def draft_final_view(captain_id):
    state = session.get('draft_state')
    if not state or not state.get('complete') or captain_id not in [state['captain1_id'], state['captain2_id']]:
        return "Draft is not complete or Unauthorized", 403

    players = load_players()
    get_player = lambda pid: next(p for p in players if p.id == pid)

    context = {
        'captain_id': captain_id,
        'this_captain': get_player(captain_id),
        'captain1': get_player(state['captain1_id']),
        'captain2': get_player(state['captain2_id']),
        'team1': [get_player(pid) for pid in state['team1']],
        'team2': [get_player(pid) for pid in state['team2']],
    }

    return render_template('final_draft.html', **context)
