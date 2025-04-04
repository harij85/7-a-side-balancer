# backend/routes/settings.py


from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, session

from backend.routes.admin import admin_required
from backend.utils.match_manager import get_match_by_id, save_matches, load_matches
from backend.utils.data_manager import load_players, save_players, save_matches_data, save_draft_state, get_config_value, set_config_value, load_config, save_config



settings_bp = Blueprint('settings_bp', __name__, url_prefix='/settings')

def sudo_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin') or not session.get('is_sudo_admin'):
            flash("Sudo admin access required.", "danger")
            return redirect(url_for('home_bp.index'))
        return f(*args, **kwargs)
    return decorated

@settings_bp.route('/')
def settings_home():
    config = load_config()
    matches = load_matches()
    players = load_players()
    return render_template('settings_dashboard.html', matches=matches, players=players, config=config)

@settings_bp.route('/toggle_sandbox', methods=['POST'])
def toggle_sandbox():
    enabled = request.form.get('enable_sandbox') == 'on'
    set_config_value('sandbox_enabled', enabled)
    flash(f"Sandbox draft mode {'enabled' if enabled else 'disabled'}.", "success")
    return redirect(url_for('settings_bp.settings_home'))

@settings_bp.route('/reset_draft/<match_id>', methods=['POST'])
def reset_draft(match_id):
    matches = load_matches()
    match = get_match_by_id(match_id)
    players = load_players()
    
    if not match:
        flash("Match not found.", "danger")
        return redirect(url_for('settings_bp.settings_home'))
    
    match.draft_created = False
    match.captains = []  

    # Remove captain status from all players
    for p in players:
        p.is_captain = False
        
    save_players(players)

    # Update match in list
    for i, m in enumerate(matches):
        if m.match_id == match.match_id:
            matches[i] = match
            break
        
    save_matches(matches)
    flash("Draft reset successfully.", "success")
    return redirect(url_for('settings_bp.settings_home'))

@settings_bp.route('/reset_app_data', methods=['POST'])
@admin_required
def reset_app_data():
    save_draft_state({})
    save_matches_data([])
    
    players = load_players()
    for p in players:
        p.is_captain = False
        p.notifications = [n for n in p.notifications if n.get("type" != "captain_assignment")]
    save_players(players)
    
    save_config({
        "rating_enabled": True,
        "public_visibility_enabled": False,
        "sandbox_enabled": False
    })
    
    flash("App data reset: matches, draft, captains, and config cleared. Players preserved.", "success" )
    return redirect(url_for('settings_bp.settings_home'))
    
