from flask import Blueprint, render_template, request, redirect, url_for, flash
from backend.utils.invite_manager import validate_invite, increment_invite_use
from backend.utils.data_manager import load_players, save_players, generate_unique_code
from backend.models.player import Player

invite_bp = Blueprint('invite_bp', __name__)

@invite_bp.route('/join/<code>', methods=['GET', 'POST'])
def join_team(code):
    if not validate_invite(code):
        flash("Invalid or expired invite code. Contact Team Admin to generate a new invite.", "danger")
        return redirect(url_for('home_bp.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        position = request.form.get('position')
        preferred_foot = request.form.get('preferred_foot')
        preferred_days = request.form.get('preferred_days')
        preferred_times = request.form.get('preferred_times')
        preferred_locations = request.form.get('preferred_locations')
        
        if not name or not position:
            flash("Name and position are required.", "warning")
            return redirect(request.url)
        
        players = load_players()
        existing_codes = {p.access_code for p in players if p.access_code}
        access_code = generate_unique_code(existing_codes)
        
        player = Player(
            name=name,
            position=position,
            skill_rating=5.0,
            preferred_foot=preferred_foot,
            preferred_days=preferred_days,
            preferred_times=preferred_times,
            preferred_locations=preferred_locations,
            access_code=access_code   
        )
        
        players = load_players()
        players.append(player)
        save_players(players)
        increment_invite_use(code)
        
        flash(f"Welcome to the team! Your access code is: {access_code}.", "success")
        return redirect(url_for('auth.player_login'))
    
    return render_template('join_team.html', invite_code=code)

@invite_bp.route('/join_team')
def join_team_landing():
    return render_template('join_landing.html')

@invite_bp.route('/join_redirect')
def join_redirect():
    code = request.args.get('code', '').strip()
    if not code:
        flash("Please enter a valid invite code.", "warning")
        return redirect(url_for('invite_bp.join_team_landing'))
    
    return redirect(url_for('invite_bp.join_team', code=code))

