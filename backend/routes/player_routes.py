from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from datetime import datetime
from backend.utils.match_manager import load_matches, save_matches, get_match_by_id
from backend.utils.data_manager import load_players, save_players, generate_unique_code, load_draft_state, get_player # Import helper
from backend.models.player import Player, PerformanceLog # Import models
from backend.utils.draft_timer import get_draft_window, is_draft_window_open # Import timer utils

player_bp = Blueprint('player_bp', __name__)

# --- Decorator for Player Login Check ---
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'player_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.player_login'))
        # Optional: Check if player_id still exists in data
        player = get_player(load_players(), session['player_id'])
        if not player:
             flash("Your session is invalid. Please log in again.", "warning")
             session.pop('player_id', None)
             return redirect(url_for('auth.player_login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Player Portal/Dashboard ---
@player_bp.route('/player/<player_id>')
@login_required # Protect this route
def player_page(player_id):
    # Basic check: Ensure logged-in user matches the requested page
    if session.get('player_id') != player_id:
        # Admins shouldn't typically use this view directly
        if session.get('is_admin'):
             flash("Admins should use the main dashboard.", "info")
             return redirect(url_for('home_bp.index'))
        else:
             flash("Unauthorized access to player portal.", "danger")
             # Log out potentially compromised session
             session.pop('player_id', None)
             return redirect(url_for('auth.player_login'))

    players = load_players()
    player = get_player(players, player_id)

    if not player:
        flash("Player data not found. Please contact admin.", "danger")
        session.pop('player_id', None) # Clear invalid session
        return redirect(url_for('auth.player_login'))

    # --- Draft Logic for Captains ---
    draft_state = load_draft_state()
    draft_context = {}
    is_draft_active = draft_state and not draft_state.get('complete', False)
    show_draft_panel = False # Default to false

    if player.is_captain and draft_state and 'captain1_id' in draft_state:
        is_participant_captain = player_id in [draft_state.get('captain1_id'), draft_state.get('captain2_id')]

        if is_participant_captain:
            # Prepare context regardless of draft completion for viewing teams/status
            captain1 = get_player(players, draft_state['captain1_id'])
            captain2 = get_player(players, draft_state['captain2_id'])
            turn_player = get_player(players, draft_state.get('turn')) # May be None

            if not captain1 or not captain2:
                 # Handle cases where captain data might be missing (e.g., deleted player)
                 flash("Error loading draft captain data.", "warning")
                 draft_context = {"error": True}
            else:
                draft_context = {
                    'captain_id': player_id, # ID of the captain viewing the page
                    'this_captain': player,
                    'captain1': captain1,
                    'captain2': captain2,
                    'team1': [p for pid in draft_state.get('team1_ids', []) if (p := get_player(players, pid))],
                    'team2': [p for pid in draft_state.get('team2_ids', []) if (p := get_player(players, pid))],
                    'remaining': [p for pid in draft_state.get('remaining_ids', []) if (p := get_player(players, pid))],
                    'turn': turn_player,
                    'is_my_turn': draft_state.get('turn') == player_id,
                    'is_complete': draft_state.get('complete', False),
                    'error': False
                }
                # Show the panel only if the draft is active (not complete)
                show_draft_panel = not draft_context['is_complete']


    # --- Other Data for Portal ---
    # Get recent ratings for chart/display
    ratings_history = [log.rating for log in player.match_history if hasattr(log, 'rating')]

    draft_start_dt, draft_end_dt = get_draft_window()

    return render_template(
        'player_portal.html',
        player=player,
        ratings=ratings_history, # Pass performance ratings
        show_draft_panel=show_draft_panel,
        draft_context=draft_context, # Context for the draft panel section
        draft_state=draft_state, # Pass raw state if needed elsewhere
        # Pass draft window times as ISO strings for JS countdown
        draft_start=draft_start_dt.isoformat(),
        draft_end=draft_end_dt.isoformat(),
        is_admin=False # Player view is never admin
    )


# --- View Other Player Profiles (and Rate them) ---
@player_bp.route('/profile/<target_id>')
@login_required # Must be logged in to view profiles/rate
def player_profile(target_id):
    viewer_id = session.get('player_id')
    # is_admin = session.get('is_admin', False) # Admin uses separate view or gets redirected

    # Allow viewing own profile, but disable rating self
    # if viewer_id == target_id:
    #     flash("You are viewing your own profile.", "info")
        # Redirect to own portal? Or allow viewing static profile?
        # return redirect(url_for('player_bp.player_page', player_id=viewer_id))

    players = load_players()
    target_player = get_player(players, target_id)
    viewer = get_player(players, viewer_id) # Should always exist due to @login_required

    if not target_player or not viewer:
        flash("Player not found.", "danger")
        return redirect(url_for('home_bp.index')) # Redirect to a safe page

    # Determine if viewer can rate the target player for the *latest* match
    # Find the latest match the target player participated in
    matches = load_matches()
    target_matches = sorted(
        [m for m in matches if target_id in m.players],
        key=lambda m: (m.date, m.start_time), # Sort by date and time
        reverse=True
    )

    latest_match = target_matches[0] if target_matches else None
    match_id_for_rating = latest_match.match_id if latest_match else None

    can_rate_players_player = False
    already_rated_players_player = False

    if viewer_id != target_id and latest_match and viewer_id in latest_match.players:
        # Check if viewer participated in the same *latest* match as target
        already_rated_players_player = any(
            r['from'] == viewer_id and r['match_id'] == match_id_for_rating
            for r in target_player.players_player_ratings
        )
        can_rate_players_player = not already_rated_players_player

    # Get target's performance log for that latest match, if available
    recent_perf_log = None
    if match_id_for_rating:
        recent_perf_log = next((log for log in target_player.match_history if log.match_id == match_id_for_rating), None)


    return render_template(
        'player_profile.html',
        target=target_player,
        viewer=viewer, # Pass viewer object
        can_rate=can_rate_players_player, # Can they submit players' player rating?
        has_already_rated=already_rated_players_player, # Have they already rated?
        is_admin=False, # Not admin view
        match_context=latest_match, # Pass the match object if found
        recent_log=recent_perf_log # Pass performance log for that match
    )


# --- Log Performance ---
@player_bp.route('/log_performance', methods=['GET', 'POST']) # Removed player_id from URL, use session
@login_required
def log_performance():
    player_id = session['player_id']
    players = load_players()
    player = get_player(players, player_id)

    if not player: # Should not happen if @login_required works
        flash("Player data not found.", "danger")
        return redirect(url_for('auth.player_login'))

    # Find the most recent match the player was assigned to (could be upcoming or just finished)
    matches = load_matches()
    player_matches = sorted(
        [m for m in matches if player_id in m.players],
        key=lambda m: (m.date, m.start_time),
        reverse=True
    )

    # Find the latest match for which performance hasn't been logged yet
    logged_match_ids = {log.match_id for log in player.match_history if log.match_id}
    match_to_log = None
    for match in player_matches:
        if match.match_id not in logged_match_ids:
             # Check if match is reasonably recent (e.g., started in last 24 hours)? Optional.
             # end_time = match.end_time()
             # if datetime.now() > end_time and datetime.now() - end_time < timedelta(days=1):
            match_to_log = match
            break # Log performance for the most recent unlogged match

    if not match_to_log:
        flash("No recent, unlogged match found for you to submit performance.", "info")
        return redirect(url_for('player_bp.player_page', player_id=player_id))

    # --- Handle POST Request ---
    if request.method == 'POST':
        try:
            goals = int(request.form['goals'])
            assists = int(request.form['assists'])
            tackles = int(request.form['tackles'])
            saves = int(request.form['saves'])
            # Add validation (e.g., non-negative)
            if any(x < 0 for x in [goals, assists, tackles, saves]):
                raise ValueError("Stats cannot be negative.")
        except (ValueError, KeyError):
            flash("Invalid input. Please enter whole numbers for stats.", "danger")
            return render_template('log_performance.html', player=player, match=match_to_log)

        # Calculate rating based on submitted stats
        # This formula can be adjusted
        rating = (goals * 2.5 + assists * 1.5 + tackles * 1.0 + saves * 1.5) / 2.0
        rating = max(1.0, min(round(rating, 2), 10.0)) # Clamp between 1 and 10

        previous_rating = player.skill_rating # Store before update

        log = PerformanceLog(
            goals=goals, assists=assists, tackles=tackles, saves=saves,
            rating=rating,
            match_id=match_to_log.match_id # Associate with the specific match
        )

        player.update_performance(log)
        player.update_skill_rating() # Update skill based on history
        save_players(players)

        rating_diff = round(player.skill_rating - previous_rating, 2)

        # Redirect to a 'thanks' page showing the update
        flash("Performance logged successfully!", "success")
        return render_template('thanks.html',
                               player=player,
                               current_rating=player.skill_rating,
                               rating_diff=rating_diff,
                               message="Stats submitted!",
                               # Provide a clear link back
                               next_url=url_for('player_bp.player_page', player_id=player.id)
                               )

    # --- Handle GET Request ---
    return render_template('log_performance.html', player=player, match=match_to_log)


# --- Regenerate Access Code ---
@player_bp.route('/regenerate_code', methods=['POST']) # Use POST for action, removed player_id
@login_required
def regenerate_code():
    player_id = session['player_id']
    players = load_players()
    player = get_player(players, player_id)

    if not player: # Should not happen
        flash("Player not found.", "danger")
        return redirect(url_for('auth.player_login'))

    existing_codes = {p.access_code for p in players if p.access_code and p.id != player_id}
    player.access_code = generate_unique_code(existing_codes)
    save_players(players)
    flash(f"New access code generated: {player.access_code}", "success")

    return redirect(url_for('player_bp.player_page', player_id=player_id))


# --- Toggle Availability ---
@player_bp.route('/toggle_availability', methods=['POST']) # Use POST, removed player_id
@login_required # Only logged-in players can toggle their own
def toggle_availability():
    player_id = session['player_id']
    players = load_players()
    player = get_player(players, player_id)

    if not player:
        flash("Player not found.", "danger")
        return redirect(url_for('auth.player_login'))

    player.available = not player.available
    save_players(players)
    status = "Available" if player.available else "Unavailable"
    flash(f"Your availability has been set to: {status}", "success")

    # Admin toggle might need a separate route in admin.py if different logic/redirect needed
    # Or check role here:
    # if session.get('is_admin'):
    #    return redirect(url_for('home_bp.index')) # Or admin player list
    # else:
    return redirect(url_for('player_bp.player_page', player_id=player_id))


# --- Player Inbox ---
@player_bp.route('/inbox') # Removed player_id, use session
@login_required
def player_inbox():
    player_id = session['player_id']
    players = load_players()
    player = get_player(players, player_id)

    if not player:
        flash("Player not found.", "danger")
        return redirect(url_for('auth.player_login'))

    # Inbox items are assumed to be persistent, sort by timestamp descending
    inbox_items = sorted(player.inbox, key=lambda x: x.get('timestamp', ''), reverse=True)

    return render_template('player_inbox.html', player=player, inbox=inbox_items)

# --- Clear Notifications (keeps Inbox) ---
@player_bp.route('/clear_notifications', methods=['POST']) # Use POST, removed player_id
@login_required
def clear_notifications():
    player_id = session['player_id']
    players = load_players()
    player = get_player(players, player_id)

    if player:
        player.clear_notifications() # Use the model method
        save_players(players)
        flash("Notifications cleared.", "info")
    else:
        flash("Player not found.", "danger") # Should not happen

    return redirect(url_for('player_bp.player_page', player_id=player_id))


# --- Submit Players' Player Rating ---
@player_bp.route('/rate_player', methods=['POST']) # Renamed route for clarity
@login_required
def players_player_rating():
    rater_id = session['player_id']
    players = load_players()
    matches = load_matches()
    rater = get_player(players, rater_id)

    if not rater: # Should not happen
        flash("Rater data not found.", "danger")
        return redirect(url_for('home_bp.index'))

    # --- Get Form Data ---
    target_id = request.form.get('target_id')
    match_id = request.form.get('match_id') # Get match_id from the form
    comment = request.form.get('comment', '').strip()
    try:
        rating = int(request.form.get('rating', 0))
        if not (1 <= rating <= 5):
             raise ValueError("Rating must be between 1 and 5.")
    except ValueError as e:
        flash(f"Invalid rating: {e}", "danger")
        # Redirect back to the profile page where the form was
        return redirect(request.referrer or url_for('home_bp.view_players'))


    # --- Validations ---
    if target_id == rater_id:
        flash("❌ You cannot rate yourself.", "warning")
        return redirect(request.referrer or url_for('home_bp.view_players'))

    target_player = get_player(players, target_id)
    if not target_player:
        flash("Target player not found.", "danger")
        return redirect(request.referrer or url_for('home_bp.view_players'))

    match = get_match_by_id(match_id) # Use helper to find match
    if not match:
        flash("Match context not found for rating.", "danger")
        return redirect(request.referrer or url_for('home_bp.view_players'))

    # Check participation
    if rater_id not in match.players or target_id not in match.players:
        flash("❌ You and the target player must have participated in the same match to rate.", "warning")
        return redirect(request.referrer or url_for('home_bp.view_players'))

    # Check if already rated *for this specific match*
    already_rated = any(
        r.get('from') == rater_id and r.get('match_id') == match_id
        for r in target_player.players_player_ratings
    )
    if already_rated:
        flash(f"⚠️ You have already submitted a Players' Player rating for {target_player.name} for this match.", "warning")
        return redirect(request.referrer or url_for('home_bp.view_players'))

    # --- Save Rating and Notify ---
    rating_data = {
        "from": rater_id,
        "match_id": match_id,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now().isoformat() # Add timestamp to rating itself
    }
    target_player.players_player_ratings.append(rating_data)

    # Add notification for the rated player
    notification_data = {
        "type": "players_player_rating", # Specific type
        "from": rater.name, # Send rater's name
        "rating": rating,
        "comment": comment,
        "match_id": match_id,
        "timestamp": rating_data["timestamp"] # Use same timestamp
    }
    target_player.add_notification(notification_data) # Use helper

    save_players(players)

    flash(f"✅ You rated {target_player.name} {rating}/5 for Players' Player.", "success")
    # Redirect back to the general player list after rating
    return redirect(url_for('home_bp.view_players'))