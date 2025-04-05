# backend/routes/home.py
from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from backend.utils.data_manager import load_players, load_draft_state, get_player, is_public_visibility_enabled, load_config  # Import helper
from backend.utils.draft_timer import get_draft_window, is_draft_window_open
from backend.models.player import Player # Import Player model
from backend.utils.match_manager import load_matches



home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/')
def index():
    """Renders the main dashboard/homepage."""
    config = load_config()
    is_admin = session.get('is_admin', False)
    player_id = session.get('player_id')

    # If admin is logged in, ensure no player session confusion
    # if is_admin and player_id:
    #     session.pop('player_id', None)
    #     flash("Admin session active. Player session cleared.", "info")
    #     player_id = None # Update local variable

    players = load_players()
    draft_state = load_draft_state()
    draft_window_open = is_draft_window_open()
    draft_start, draft_end = get_draft_window()

    # Get current player object if logged in as player
    current_player = get_player(players, player_id) if player_id else None

    # Sort players for display (e.g., by rating)
    players.sort(key=lambda x: x.skill_rating, reverse=True)

    # Determine captain assignment possibility
    captain_count = sum(1 for p in players if p.is_captain)
    can_assign_more_captains = captain_count < 2
    
    matches = load_matches()
    
    draft_ready_match = next(
        (m for m in matches if len(getattr(m, 'captains', [])) == 2 and not getattr(m, 'darft_created', False)),
        None 
    )
    
    manually_selected_captains = [p for p in players if p.is_captain]
    is_sandbox_draft_possible = len(manually_selected_captains) == 2 and not draft_ready_match

    return render_template(
        'index.html',
        players=players,
        is_admin=is_admin,
        player_id=player_id, # Pass player_id for template logic
        player=current_player, # Pass player object for navbar/greeting
        draft_state=draft_state,
        draft_window_open=draft_window_open,
        can_assign_more=can_assign_more_captains,
        draft_start=draft_start.isoformat(), # Pass as ISO string for JS
        draft_end=draft_end.isoformat(),
        next_draft_start=draft_start, # Pass datetime object for display
        next_draft_end=draft_end,
        draft_ready_match=draft_ready_match,
        is_sandbox_draft_possible=is_sandbox_draft_possible,
        show_public_draft=config.get('public_draft_view_enabled', False),
        show_public_players=config.get('public_player_view_enabled', False)
    )

@home_bp.route('/players')  # Changed route to '/players' for clarity
def view_players():
    """Displays a filterable list of all players."""
    players = load_players()
    is_admin = session.get('is_admin', False)
    player_id = session.get('player_id')
    user_role = session.get('role')

    # --- Public Access Restriction ---
    if not player_id and not is_admin:
        # Not logged in as admin or player
        if not is_public_visibility_enabled():
            return redirect(url_for('home_bp.index'))

    # Get current player object for navbar/context
    current_player = get_player(players, player_id) if player_id else None

    # If public view is enabled but individual player consent is required (future-proof)
    if not is_admin and not current_player and is_public_visibility_enabled():
        players = [p for p in players if getattr(p, 'has_consented_public_view', False)]

    # --- Filtering Logic ---
    search = request.args.get('search', '').strip().lower()
    position = request.args.get('position', '').upper()
    availability = request.args.get('availability', '')  # 'available', 'unavailable', ''

    filtered_players = players  # Start with all players

    if search:
        filtered_players = [p for p in filtered_players if search in p.name.lower()]
    if position:
        filtered_players = [p for p in filtered_players if p.position == position]
    if availability == 'available':
        filtered_players = [p for p in filtered_players if p.available]
    elif availability == 'unavailable':
        filtered_players = [p for p in filtered_players if not p.available]

    # Sort final list
    filtered_players.sort(key=lambda p: p.skill_rating, reverse=True)

    # --- Render Template ---
    return render_template(
        'view_players.html',  # Use the dedicated template
        players=filtered_players,
        is_admin=is_admin,
        player_id=player_id,
        player=current_player,
        search_term=request.args.get('search', ''),  # Pass original case back
        selected_position=request.args.get('position', ''),
        selected_availability=availability
    )

# Removed view_player_stats - Admin/Player profile viewing is handled by player_routes.player_profile
# If a separate admin-only detailed stats view is needed, it could be added back in admin.py


# START OF REFACTORED FILE: backend/routes/player_routes.py ---

#python
# backend/routes/player_routes.py

