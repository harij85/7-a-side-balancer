# backend/routes/admin.py

import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from backend.models.player import Player
from backend.models.match import Match
# Use the match manager functions for loading/saving Match objects
from backend.utils.match_manager import load_matches, save_matches, get_match_by_id
from backend.utils.data_manager import load_players, save_players, generate_unique_code, save_draft_state
from backend.utils.team_generator import generate_balanced_teams
from backend.utils.invite_manager import (generate_invite_link, generate_invite_code, get_all_invites, revoke_invite, validate_invite)



from dotenv import load_dotenv

load_dotenv()

admin_bp = Blueprint('admin', __name__) # url_prefix is set in app_factory

# --- Authentication (Moved primary logic to auth.py) ---
# Keep placeholder routes if needed, or remove if auth_bp handles /admin/login fully
# @admin_bp.route('/login', methods=['GET', 'POST']) ...
# @admin_bp.route('/logout') ...


# --- Decorator for Admin Check ---
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Admin access required.", "danger")
            return redirect(url_for('auth.admin_login')) # Redirect to admin login
        return f(*args, **kwargs)
    return decorated_function

# --- Player Management ---

@admin_bp.route('/generate_invite', methods=['GET', 'POST'])
@admin_required
def generate_invite():
    if request.method == 'POST':
        max_uses = int(request.form.get('max_uses', 1))
        expires_in_days = int(request.form.get('expires_in_days', 7))

        invite_code = generate_invite_link(
            created_by='admin',
            max_uses=max_uses,
            days_valid=expires_in_days
        )

        invite_link = f"{request.host_url}join/{invite_code}"
        flash(f"Invite link created below.", "success")

        invites = get_all_invites()
        return render_template('generate_invite.html', invite_link=invite_link, invites=invites)

    # GET request
    invites = get_all_invites()
    return render_template('generate_invite.html', invites=invites)


@admin_bp.route('/add_player', methods=['GET', 'POST'])
@admin_required
def add_player():
    if request.method == 'POST':
        players = load_players()
        name = request.form.get('name', '').strip()
        position = request.form.get('position')
        age_str = request.form.get('age', '').strip()

        if not name or not position or not age_str:
             flash("Name, position, and age are required.", "warning")
             return render_template('add_player.html')

        try:
            age = int(age_str)
            if not (10 <= age <= 90): # Example age range validation
                 raise ValueError("Age must be between 10 and 90.")
        except ValueError as e:
            flash(f"Invalid age: {e}", "danger")
            return render_template('add_player.html')

        # Consider adding checks for duplicate names
        if any(p.name.lower() == name.lower() for p in players):
            flash(f"Player with name '{name}' already exists.", "warning")
            return render_template('add_player.html', current_name=name, current_pos=position, current_age=age)

        skill_rating = 5.0 # Default rating for new players
        existing_codes = {p.access_code for p in players if p.access_code}
        access_code = generate_unique_code(existing_codes)

        player = Player(
            name=name,
            position=position,
            skill_rating=skill_rating,
            age=age, # Pass age here
            access_code=access_code
            # inbox/notifications/etc handled by default constructor
        )

        players.append(player)
        save_players(players)
        flash(f"Player '{player.name}' added successfully.", "success")
        return redirect(url_for('home_bp.index')) # Redirect to home/dashboard after adding

    return render_template('add_player.html')

@admin_bp.route('/remove_player/<player_id>', methods=['POST'])
@admin_required
def remove_player(player_id):
    players = load_players()
    initial_length = len(players)
    players = [p for p in players if p.id != player_id]

    if len(players) < initial_length:
        save_players(players)
        flash("Player removed successfully.", "success")
    else:
        flash("Player not found.", "warning")
    return redirect(url_for('home_bp.index')) # Redirect to home/dashboard

@admin_bp.route('/assign_captain/<player_id>', methods=['POST'])
@admin_required
def assign_captain(player_id):
    players = load_players()
    target_player = next((p for p in players if p.id == player_id), None)

    if not target_player:
        flash("Player not found.", "danger")
        return redirect(url_for('home_bp.index'))

    captain_count = sum(1 for p in players if p.is_captain)

    if target_player.is_captain:
        # Unassigning
        target_player.is_captain = False
        flash(f"{target_player.name} is no longer a captain.", "info")
        # Optionally remove the captain notification (or leave it for history)
    else:
        # Assigning
        if captain_count >= 2:
            flash("Cannot assign more than two captains.", "warning")
            return redirect(url_for('home_bp.index'))
        target_player.is_captain = True
        flash(f"{target_player.name} assigned as captain.", "success")
        # Add notification and inbox message
        message = {
            "type": "captain_assignment",
            "message": "You've been assigned as a captain! Access the draft via your player portal when it opens.",
            "timestamp": datetime.now().isoformat()
        }
        target_player.add_notification(message) # Use helper method

    save_players(players)
    return redirect(url_for('home_bp.index'))

@admin_bp.route('/assign_captains/<match_id>', methods=['GET', 'POST'])
@admin_required
def assign_captains(match_id):
    players = load_players()
    match = get_match_by_id(match_id)

    if not match:
        flash("Match not found.", "danger")
        return redirect(url_for('home_bp.index'))

    # Only use available players
    available_players = [p for p in players if p.available]

    if len(available_players) < 4:
        flash("At least 4 available players are required to assign captains.", "warning")
        return redirect(url_for('home_bp.index'))

    if request.method == 'POST':
        captain1_id = request.form.get('captain1')
        captain2_id = request.form.get('captain2')

        if not captain1_id or not captain2_id or captain1_id == captain2_id:
            flash("Please select two different captains.", "warning")
            return render_template('assign_captains.html', players=available_players, match=match)

        for p in players:
            p.is_captain = p.id in [captain1_id, captain2_id]
            if p.is_captain:
                p.add_notification({
                    "type": "captain_assignment",
                    "message": "You've been assigned as a captain! Access the draft via your player portal when it opens.",
                    "timestamp": datetime.now().isoformat()
                })
                
        match.captains = [captain1_id, captain2_id]
        matches = load_matches()
        for i, m in enumerate(matches):
            if m.match_id == match.match_id:
                matches[i] = match
                break
        save_matches(matches)

        save_players(players)
        flash("Captains assigned successfully.", "success")
        return redirect(url_for('home_bp.index'))  # Optional: redirect to draft lobby

    return render_template('assign_captains.html', players=available_players, match=match)

# --- Team Generation ---
@admin_bp.route('/generate_teams')
@admin_required
def generate_teams():
    match_id = request.args.get('match_id')
    if not match_id:
        flash("Match ID is required.", "danger")
        return redirect(url_for('home_bp.index'))

    match = get_match_by_id(match_id)
    if not match:
        flash("Match not found.", "danger")
        return redirect(url_for('home_bp.index'))

    players = load_players()
    available_players = [p for p in players if p.available]
    if len(available_players) < 2:
        flash("Not enough available players to generate teams.", "warning")
        return redirect(url_for('home_bp.index'))

    team1, team2 = generate_balanced_teams(available_players)
    return render_template('team_generator.html', team1=team1, team2=team2)

# ----- Create Draft -----
@admin_bp.route('/create_draft/<match_id>', methods=['POST'])
@admin_required
def create_draft(match_id):
    matches = load_matches()
    match = get_match_by_id(match_id)
    if not match:
        flash("Match not found.", "danger")
        return redirect(url_for('home_bp.index'))
    
    if match.draft_created:
        flash("Draft has already been created for this match.", "danger")
        return redirect(url_for('home_bp.index'))
    
    if len(match.captains) != 2:
        flash("exactly 2 captains must be assigned before creating the draft.", "warning")
        return redirect(url_for('admin.assign_captains', match_id=match_id))
    
    
    all_players = load_players()
    remaining = [p.id for p in all_players if p.available and p.id not in match.captains]
    
    draft_state = {
        "match_id": match.match_id,
        "captain1_id": match.captains[0],
        "captain2_id": match.captains[1],
        "team1_ids": [],
        "team2_ids": [],
        "remaining_ids": remaining,
        "turn": match.captains[0],
        "complete": False
    }
    
    save_draft_state(draft_state)
    
    # Mark draft as created
    match.draft_created = True
    for i, m in enumerate(matches):
        if m.match_id == match.match_id:
            matches[i] = match
            break
    save_matches(matches)
    
    flash("Draft created successfully. Captains can now begin picking teams.", "success")
    return redirect(url_for('home_bp.index'))

# --- Ratings Management ---
@admin_bp.route('/ratings')
@admin_required
def admin_view_ratings(): # Renamed function slightly
    players = load_players()
    # Combine both types of ratings for admin view
    all_ratings_received = []
    all_players_player_ratings = []

    for player in players:
        # Standard Ratings Received (Placeholder if implemented)
        # for entry in player.ratings_received: ...

        # Players' Player Ratings Received
        for entry in player.players_player_ratings:
             rater = next((p.name for p in players if p.id == entry.get('from')), 'Unknown Rater')
             all_players_player_ratings.append({
                 'rated_player_name': player.name,
                 'rated_player_id': player.id,
                 'rater_name': rater,
                 'rater_id': entry.get('from'),
                 'rating': entry.get('rating'),
                 'comment': entry.get('comment', ''),
                 'match_id': entry.get('match_id'),
                 'timestamp': entry.get('timestamp') # Assuming timestamp exists
             })

    # Sort ratings, e.g., by timestamp descending if available
    # all_players_player_ratings.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Pass ratings to a template designed for viewing them
    return render_template('admin_ratings.html',
                           players_ratings=all_players_player_ratings)
                           # pass other rating types if needed

# --- Match Management ---
@admin_bp.route('/create_match', methods=['GET', 'POST'])
@admin_required
def create_match():
    players = load_players()
    available_players = [p for p in players if p.available]

    if request.method == 'POST':
        if len(available_players) < 4:
            flash("At least 4 players must be marked as available to create a match.", "warning")
            return render_template('create_match.html')

        date = request.form.get('date')
        start_time = request.form.get('start_time')
        duration_str = request.form.get('duration')
        location = request.form.get('location')
        num_teams = request.form.get('num_teams')
        players_per_team = request.form.get('players_per_team')
        selection_method = request.form.get('selection_method')  # 'draft' or 'auto'

        # Validation
        if not date or not start_time or not duration_str or not location or not num_teams or not players_per_team:
            flash("All fields are required.", "warning")
            return render_template('create_match.html')

        try:
            duration = int(duration_str)
            if duration < 10:
                raise ValueError("Duration must be at least 10 minutes.")
            num_teams = int(num_teams)
            players_per_team = int(players_per_team)
        except ValueError as e:
            flash(f"Invalid input: {e}", "danger")
            return render_template('create_match.html')
        
        # New: Check total player availability
        available_players = [p for p in load_players() if p.available]
        required_players = num_teams * players_per_team
        if len(available_players) < required_players:
            flash(f"Not enough available players. Required: {required_players}, Available: {len(available_players)}", "warning")
            return render_template('create_match.html')


        match = Match(
            date=date,
            start_time=start_time,
            duration_minutes=duration,
            location=location,
            num_teams=num_teams,
            players_per_team=players_per_team,
            team_selection_method=selection_method,
            players=[],  # Players assigned after draft or auto-generation
            is_completed=False
        )

        matches = load_matches()
        matches.append(match)
        save_matches(matches)

        flash("Match created successfully!", "success")
        flash(f"Match scheduled for {date} at {start_time} created successfully!", "success")

        if selection_method == "draft":
            return redirect(url_for('admin.assign_captains', match_id=match.match_id))
        else:
            return redirect(url_for('admin.generate_teams', match_id=match.match_id))

    # GET
    return render_template('create_match.html')


# Removed admin/view_players - Consolidated into home_bp.view_players