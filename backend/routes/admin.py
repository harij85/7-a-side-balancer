
import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from backend.models.player import Player
from backend.models.match import Match
from backend.utils.match_manager import load_matches, save_matches
from backend.utils.data_manager import load_players, save_players, generate_unique_code
from backend.utils.team_generator import generate_balanced_teams
from dotenv import load_dotenv

load_dotenv()

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session['is_admin'] = True
            session.pop('player_id', None)
            return redirect(url_for('home_bp.index'))

        else:
            return render_template('admin_login.html', error="Invalid password")
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home_bp.index'))

@admin_bp.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    if request.method == 'POST':
        players = load_players()
        name = request.form['name']
        position = request.form['position']
        skill_rating = 5.0
        age = int(request.form['age'])
        
        existing_codes = {p.access_code for p in players}
        access_code = generate_unique_code(existing_codes)
        
        player = Player(name=name, position=position, skill_rating=skill_rating)
        player.access_code = access_code
        player.age = age
        player.inbox = []
        
        players.append(player)
        save_players(players)
        return redirect(url_for('home_bp.index'))
    return render_template('add_player.html')

@admin_bp.route('/remove_player/<player_id>', methods=['POST'])
def remove_player(player_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    players = [p for p in players if p.id != player_id]
    save_players(players)
    return redirect(url_for('home_bp.index'))



@admin_bp.route('/assign_captain/<player_id>', methods=['POST'], endpoint='assign_captain')
def assign_captain(player_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403

    players = load_players()
    captain_count = sum(1 for p in players if p.is_captain)
    
    for player in players:
        if player.id == player_id:
            if not player.is_captain and captain_count >= 2:
                return "Only two captains can be assigned.", 400
            player.is_captain = not player.is_captain

            if player.is_captain:
                if not any("assigned as a captain" in note["message"] for note in player.notifications):
                    message = {
                        "message": "You've been assigned as a captain! Go to your dashboard when the draft begins.",
                        "timestamp": datetime.now().isoformat()
                    }
                    player.notifications.append(message)
                    player.inbox.append(message)
            break

    save_players(players)
    return redirect(url_for('home_bp.index'))

@admin_bp.route('/generate_teams')
def generate_teams():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    team1, team2 = generate_balanced_teams(players)
    return render_template('team_generator.html', team1=team1, team2=team2)

@admin_bp.route('/admin/ratings')
def admin_rating():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    all_ratings = []
    for player in players:
        for entry in player.ratings_received:
            all_ratings.append({
                'to': player.name,
                'from': next((p.name for p in players if p.id == entry['from']), 'Unknown'),
                'comment': entry['comment'],
                'rating': entry['rating'],
                'match_id': entry['match_id'],
                'player_id': player.id,
                'index': player.ratings_received.index(entry)
            })
    return render_template('admin_ratings.html', ratings=all_ratings)

@admin_bp.route('/admin/view_players', methods=['GET'], endpoint='view_players')
def view_players():
    if not session.get('is_admin'):
        return "Unauthorized", 403

    players = load_players()
    for player in players:
        if len(player.match_history) >= 2:
            last = player.match_history[-1].rating
            second_last = player.match_history[-2].rating
            player.rating_diff = round(last - second_last, 2)
        else:
            player.rating_diff = 0
            
    players = sorted(players, key=lambda x: x.skill_rating, reverse=True)

    # Get query parameters
    search = request.args.get('search', '').lower()
    position = request.args.get('position', '')
    availability = request.args.get('availability', '')

    # Filter by name
    if search:
        players = [p for p in players if search in p.name.lower()]

    # Filter by position
    if position:
        players = [p for p in players if p.position.lower() == position.lower()]

    # Filter by availability
    if availability == 'available':
        players = [p for p in players if p.available]
    elif availability == 'unavailable':
        players = [p for p in players if not p.available]

    return render_template('view_players.html', players=players, search=search, position=position, availability=availability)

@admin_bp.route('/create_match', methods=['GET', 'POST'])
def create_match():
    players = load_players()
    if request.method == 'POST':
        date = request.form['date']
        start_time = request.form['start_time']
        duration = int(request.form['duration'])
        selected_players = request.form.getlist('players')

        match = Match(
            date=date,
            start_time=start_time,
            duration_minutes=duration,
            players=selected_players,
            is_completed=False
        )

        matches = load_matches()
        matches.append(match)
        save_matches(matches)

        flash("✅ Match created successfully", "success")
        return redirect(url_for('home_bp.index'))

    return render_template('create_match.html', players=players)

