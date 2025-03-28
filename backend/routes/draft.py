from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from datetime import datetime, timedelta
from backend.utils.data_manager import load_players, save_players, load_draft_state, save_draft_state
draft_bp = Blueprint('draft_bp', __name__)


def is_draft_window_open():
    now = datetime.now()
    #Draft window: Tuesday 00:00 to Saturday 23:59
    #Future logic make draft window customisable by Team Admin
    start = now - timedelta(days=now.weekday() - 1)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=4, hours=23, minutes=59, seconds=59)
    return start <= now <= end

def can_start_draft(draft_state):
    if not is_draft_window_open():
        flash("Drafting is only allowed between Tuesday and Saturday!", "danger")
        return redirect(url_for('admin.view_players'))

    return is_draft_window_open() and not draft_state.get("complete", False)

@draft_bp.route('/draft/start', methods=['POST'])
def start_draft():
    if not session.get('is_admin'):
        return "Unauthorized", 403

    session.pop('draft_state', None)
    players = load_players()
    captains = [p for p in players if p.is_captain]

    if len(captains) != 2:
        return "Exactly 2 captains must be assigned.", 400

    captains = sorted(captains, key=lambda p: p.skill_rating, reverse=True)
    captain1, captain2 = captains
    draft_pool = [p for p in players if p.available and not p.is_captain]

    state = {
        'captain1_id': captain1.id,
        'captain2_id': captain2.id,
        'team1': [],
        'team2': [],
        'remaining_ids': [p.id for p in draft_pool],
        'turn': captain1.id
    }

    save_draft_state(state)
    session['draft_state'] = state

    return redirect(url_for('draft_bp.draft_observer_view'))


@draft_bp.route('/draft/view')
def draft_observer_view():
    state = session.get('draft_state')
    if not state:
        return "Draft not started", 400

    players = load_players()
    get_player = lambda pid: next((p for p in players if p.id == pid), None)

    captain1 = get_player(state['captain1_id'])
    captain2 = get_player(state['captain2_id'])

    if not captain1 or not captain2:
        return "One or more captains are missing", 400

    context = {
        'captain1': captain1,
        'captain2': captain2,
        'team1': [p for pid in state['team1'] if (p := get_player(pid))],
        'team2': [p for pid in state['team2'] if (p := get_player(pid))],
        'remaining': [p for pid in state['remaining_ids'] if (p := get_player(pid))],
        'turn': get_player(state['turn']),
    }

    return render_template('draft_observer.html', **context)


@draft_bp.route('/draft/captain/<captain_id>')
def captain_draft_view(captain_id):
    state = session.get('draft_state')
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




@draft_bp.route('/draft/pick/<player_id>', methods=['POST'])
def draft_pick(player_id):
    state = load_draft_state()
    captain_id = request.form.get('captain_id')

    if not state or player_id not in state['remaining_ids']:
        return "Invalid pick", 400

    if captain_id != state['turn']:
        return "It's not your turn!", 403

    # Assign player to team
    if state['turn'] == state['captain1_id']:
        state['team1'].append(player_id)
        next_turn = state['captain2_id']
    else:
        state['team2'].append(player_id)
        next_turn = state['captain1_id']

    # Remove player from pool
    state['remaining_ids'].remove(player_id)

    # Check if draft is complete
    if not state['remaining_ids']:
        state['complete'] = True
        state['turn'] = None

        # Notify both captains
        players = load_players()
        for cap_id in [state['captain1_id'], state['captain2_id']]:
            captain = next((p for p in players if p.id == cap_id), None)
            if captain:
                message = {
                    "type": "draft_complete",
                    "message": "✅ Draft is complete. Check your team below.",
                    "timestamp": datetime.now().isoformat()
                }
                captain.notifications.append(message)
                captain.inbox.append(message)
        save_players(players)
    else:
        state['turn'] = next_turn

    # Save state
    save_draft_state(state)

    # Always redirect captains to their portal to see live draft status
    return redirect(url_for('player_bp.player_page', player_id=captain_id))


@draft_bp.route('/draft/final/<captain_id>')
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


@draft_bp.route('/message_team/<captain_id>', methods=['GET', 'POST'])
def message_team(captain_id):
    players = load_players()
    captain = next((p for p in players if p.id == captain_id and p.is_captain), None)

    if not captain or session.get('player_id') != captain_id:
        return "Unauthorized", 403

    draft = load_draft_state()
    team_ids = draft['team1'] if draft['captain1_id'] == captain_id else draft['team2']
    team_players = [p for p in players if p.id in team_ids]

    if request.method == 'POST':
        message = request.form.get('message')
        timestamp = datetime.now().isoformat()

        for teammate in team_players:
            note = {
                "message": f"Captain {captain.name} says: {message}",
                "timestamp": timestamp
            }
            teammate.notifications.append(note)
            teammate.inbox.append(note)

        save_players(players)
        return render_template('thanks.html', player=captain, message="Team notified successfully!", rating_diff=0)

    return render_template('message_team.html', captain=captain, teammates=team_players)
