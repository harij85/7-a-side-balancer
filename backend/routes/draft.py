# backend/routes/draft.py
# Consolidated draft logic including captain actions

from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from datetime import datetime, timedelta
from backend.utils.data_manager import (
    load_players, save_players, load_draft_state, save_draft_state, load_matches_data
)
from backend.utils.draft_timer import get_draft_window # Use shared function
from backend.models.player import Player # Import Player model
from backend.utils.match_manager import get_current_draft_match

draft_bp = Blueprint('draft_bp', __name__)

# --- Helper Function ---
def get_player(players, player_id):
    """Safely get a player by ID from a list."""
    return next((p for p in players if p.id == player_id), None)

# --- Admin Draft Control ---
@draft_bp.route('/draft/start', methods=['POST'])
def start_draft():
    # Add admin check decorator if using one
    # @admin_required
    if not session.get('is_admin'):
        flash("Admin access required to start the draft.", "danger")
        return redirect(url_for('home_bp.index'))

    # Check draft window (optional for admin start, but good practice)
    # if not is_draft_window_open():
    #     start_dt, end_dt = get_draft_window()
    #     flash(f"Draft can only be started between {start_dt.strftime('%a %H:%M')} and {end_dt.strftime('%a %H:%M')}", "warning")
    #     return redirect(url_for('home_bp.index'))

    # Clear previous state from session and file
    session.pop('draft_state', None)
    save_draft_state({}) # Clear file state

    players = load_players()
    captains = [p for p in players if p.is_captain]

    if len(captains) != 2:
        flash("Exactly 2 captains must be assigned before starting the draft.", "warning")
        return redirect(url_for('home_bp.index')) # Redirect back to player list/dashboard

    # Sort captains (e.g., by skill, could be random or other criteria)
    captains.sort(key=lambda p: p.skill_rating, reverse=True)
    captain1, captain2 = captains

    # Get available, non-captain players for the draft pool
    draft_pool = [p for p in players if p.available and not p.is_captain]
    if not draft_pool:
        flash("No available players (non-captains) to draft.", "warning")
        return redirect(url_for('home_bp.index'))


    # Initialize draft state
    state = {
        'captain1_id': captain1.id,
        'captain2_id': captain2.id,
        'team1_ids': [], # Store IDs
        'team2_ids': [], # Store IDs
        'remaining_ids': [p.id for p in draft_pool],
        'turn': captain1.id, # Highest rated captain starts
        'complete': False,
        'start_time': datetime.now().isoformat() # Record start time
    }

    save_draft_state(state)
    # Optionally store in session for quick access, but file is source of truth
    # session['draft_state'] = state

    flash("Draft started successfully!", "success")
    # Notify captains
    cap1_notify = get_player(players, captain1.id)
    cap2_notify = get_player(players, captain2.id)
    if cap1_notify:
         cap1_notify.add_notification({"type": "draft_start", "message": "The draft has started! It's your turn to pick."})
    if cap2_notify:
         cap2_notify.add_notification({"type": "draft_start", "message": "The draft has started! Waiting for the first pick."})
    save_players(players)


    # Redirect admin to an observer view or dashboard
    return redirect(url_for('draft_bp.draft_observer_view'))


# --- Observer View (for Admins or Public) ---
@draft_bp.route('/draft/view')
def draft_observer_view():
    state = load_draft_state()
    if not state or 'captain1_id' not in state: # Basic check if draft has started
        flash("Draft has not been started yet.", "info")
        return redirect(url_for('home_bp.index'))

    players = load_players() # Load players to resolve IDs to names/objects

    captain1 = get_player(players, state['captain1_id'])
    captain2 = get_player(players, state['captain2_id'])
    turn_player = get_player(players, state.get('turn')) # Use get for turn, might be None if complete

    # Check if captains exist (could have been deleted)
    if not captain1 or not captain2:
         flash("Error: One or both captains associated with the draft no longer exist.", "danger")
         # Consider resetting draft state or handling differently
         save_draft_state({}) # Simple reset for now
         return redirect(url_for('home_bp.index'))


    context = {
        'captain1': captain1,
        'captain2': captain2,
        'team1': [p for pid in state.get('team1_ids', []) if (p := get_player(players, pid))],
        'team2': [p for pid in state.get('team2_ids', []) if (p := get_player(players, pid))],
        'remaining': [p for pid in state.get('remaining_ids', []) if (p := get_player(players, pid))],
        'turn': turn_player,
        'is_complete': state.get('complete', False),
        'state': state # Pass full state if needed by template
    }

    # Pass admin/player status for navbar/template logic
    context['is_admin'] = session.get('is_admin', False)
    context['player_id'] = session.get('player_id')
    current_player = get_player(players, context['player_id'])
    context['player'] = current_player


    return render_template('draft_observer.html', **context)


# --- Captain Draft Actions (Merged from captains.py) ---

# This route is now handled by the Player Portal/Dashboard logic in player_routes.py
# The player portal will show the draft panel if the player is a captain and draft is active.
# @draft_bp.route('/draft/captain/<captain_id>') ... REMOVED ...


@draft_bp.route('/draft/pick', methods=['POST'])
def draft_pick():
    # Check if logged in as a player
    player_id = request.form.get('player_id')
    captain_id_session = session.get('player_id')
    if not captain_id_session:
        flash("You must be logged in as a player (captain) to make a pick.", "warning")
        return redirect(url_for('auth.player_login'))

    # Load current state and players
    state = load_draft_state()
    players = load_players()
    captain = get_player(players, captain_id_session)

    # --- Validations ---
    if not state or state.get('complete'):
        flash("Draft is not active or already completed.", "warning")
        return redirect(url_for('player_bp.player_page', player_id=captain_id_session))

    if not captain or not captain.is_captain:
         flash("Only designated captains can make picks.", "danger")
         return redirect(url_for('player_bp.player_page', player_id=captain_id_session))

    # Check if it's this captain's turn
    if state.get('turn') != captain_id_session:
        flash("It's not your turn to pick.", "warning")
        return redirect(url_for('player_bp.player_page', player_id=captain_id_session))

    # Check if the selected player is valid and available in the pool
    picked_player = get_player(players, player_id)
    if not picked_player or player_id not in state.get('remaining_ids', []):
        flash("Invalid player selected or player already picked.", "danger")
        return redirect(url_for('player_bp.player_page', player_id=captain_id_session))

    # --- Perform Pick ---
    current_turn_captain_id = state['turn']
    next_turn_captain_id = None

    if current_turn_captain_id == state['captain1_id']:
        state['team1_ids'].append(player_id)
        next_turn_captain_id = state['captain2_id']
    elif current_turn_captain_id == state['captain2_id']:
        state['team2_ids'].append(player_id)
        next_turn_captain_id = state['captain1_id']
        
    match = get_current_draft_match()
        
    if match:
        picked_player.add_notification({
            "type": "draft_pick",
            "message": (
                f"Congratulations! You have been chosen by Captain {captain.name} " 
                f"for the match on {match.date} at {match.location}. "
                f"Please arrive at least 15 minutes before the {match.start_time} kick-off!"
            ),
            "timestamp": datetime.now().isoformat()
        })
            
        picked_player.upcoming_match = {
            "match_id": match.match_id,
            "date": match.date,
            "start_time": match.start_time,
            "location": match.location
            }
        
    else:
        # Should not happen if validation is correct
        flash("Internal error: Invalid turn state.", "danger")
        return redirect(url_for('player_bp.player_page', player_id=captain_id_session))

    # Remove player from remaining pool
    state['remaining_ids'].remove(player_id)

    # --- Update State and Notify ---
    if not state['remaining_ids']:
        # Draft Complete
        state['complete'] = True
        state['turn'] = None
        state['end_time'] = datetime.now().isoformat()
        flash("Draft pick successful! Draft is now complete.", "success")

        # Notify both captains
        cap1 = get_player(players, state['captain1_id'])
        cap2 = get_player(players, state['captain2_id'])
        completion_message = {
            "type": "draft_complete",
            "message": "✅ Draft is complete! Check the final teams.",
            "timestamp": state['end_time']
        }
        if cap1: cap1.add_notification(completion_message)
        if cap2: cap2.add_notification(completion_message)
        save_players(players) # Save updated notifications

    else:
        # Draft Continues
        state['turn'] = next_turn_captain_id
        flash(f"Successfully picked {picked_player.name}.", "success")
        # Notify the *next* captain it's their turn
        next_captain = get_player(players, next_turn_captain_id)
        if next_captain:
             turn_message = {
                "type": "draft_turn",
                "message": "It's your turn to pick in the draft!",
                "timestamp": datetime.now().isoformat()
             }
             next_captain.add_notification(turn_message)
             save_players(players)


    # Save the updated draft state
    save_draft_state(state)
    # Optionally update session state if using it for quick access
    # session['draft_state'] = state


    # Redirect the captain back to their portal to see the updated state
    return redirect(url_for('player_bp.player_page', player_id=captain_id_session))


# --- Final Draft View (Can be part of Observer or a separate simple page) ---
# This might not be strictly necessary if the player portal/observer view shows the final teams well.
# If kept, it should be accessible by captains after completion.
@draft_bp.route('/draft/final/<viewing_player_id>')
def draft_final_view(viewing_player_id):
    state = load_draft_state()
    players = load_players()
    viewer = get_player(players, viewing_player_id)

    # Validation
    if not state or not state.get('complete'):
        flash("Draft is not complete.", "warning")
        # Redirect based on role
        if viewer and viewer.is_captain:
            return redirect(url_for('player_bp.player_page', player_id=viewing_player_id))
        else: # Admin or other player
            return redirect(url_for('draft_bp.draft_observer_view'))

    # Check if viewer was a captain in *this* draft (optional but good)
    # is_viewer_captain = viewing_player_id in [state.get('captain1_id'), state.get('captain2_id')]
    # if not is_viewer_captain and not session.get('is_admin'): # Allow admins to view
    #     flash("Only captains from this draft can view this page.", "warning")
    #     return redirect(url_for('home_bp.index'))

    captain1 = get_player(players, state['captain1_id'])
    captain2 = get_player(players, state['captain2_id'])

    if not captain1 or not captain2:
         flash("Error retrieving captain data for the completed draft.", "danger")
         return redirect(url_for('home_bp.index'))


    context = {
        'viewer': viewer, # Pass the viewing player
        'captain1': captain1,
        'captain2': captain2,
        'team1': [p for pid in state.get('team1_ids', []) if (p := get_player(players, pid))],
        'team2': [p for pid in state.get('team2_ids', []) if (p := get_player(players, pid))],
        'is_admin': session.get('is_admin', False), # For navbar/template logic
        'player_id': viewing_player_id, # For navbar
        'player': viewer # Pass player object for navbar
    }

    return render_template('final_draft.html', **context)


# --- Captain Messaging Team ---
@draft_bp.route('/message_team/<captain_id>', methods=['GET', 'POST'])
def message_team(captain_id):
    # --- Authorization & Data Loading ---
    session_player_id = session.get('player_id')
    if not session_player_id or session_player_id != captain_id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('home_bp.index'))

    players = load_players()
    captain = get_player(players, captain_id)
    if not captain or not captain.is_captain:
        flash("Only captains can message their team.", "warning")
        return redirect(url_for('player_bp.player_page', player_id=captain_id))

    # Determine the captain's team from the latest completed draft state
    draft_state = load_draft_state()
    if not draft_state or not draft_state.get('complete'):
        flash("Draft is not complete. Cannot message team yet.", "info")
        return redirect(url_for('player_bp.player_page', player_id=captain_id))

    team_ids = []
    if draft_state.get('captain1_id') == captain_id:
        team_ids = draft_state.get('team1_ids', [])
    elif draft_state.get('captain2_id') == captain_id:
        team_ids = draft_state.get('team2_ids', [])
    else:
        # This captain might not have been part of the last draft
        flash("You were not a captain in the last completed draft.", "warning")
        return redirect(url_for('player_bp.player_page', player_id=captain_id))

    # Include the captain themself in the team list? Decide based on requirements.
    # team_ids.append(captain_id) # Uncomment to include captain

    team_players = [p for p in players if p.id in team_ids] # Get player objects for teammates

    # --- Handle POST Request (Sending Message) ---
    if request.method == 'POST':
        message_content = request.form.get('message', '').strip()
        if not message_content:
            flash("Message cannot be empty.", "warning")
            return render_template('message_team.html', captain=captain, teammates=team_players)

        timestamp = datetime.now().isoformat()
        message_data = {
            "type": "captain_message", # Use a specific type
            "message": f"📢 Captain {captain.name}: {message_content}",
            "from_captain_id": captain_id,
            "timestamp": timestamp
        }

        # Send to each teammate (excluding self if not included in team_players)
        for teammate in team_players:
            teammate.add_notification(message_data.copy()) # Use helper

        save_players(players)
        flash("Message sent to your team successfully!", "success")
        # Redirect back to player portal after sending
        return redirect(url_for('player_bp.player_page', player_id=captain_id))

    # --- Handle GET Request (Show Form) ---
    return render_template('message_team.html', captain=captain, teammates=team_players)
