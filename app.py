from flask import Flask, render_template, redirect, url_for, request, session
from flask_socketio import SocketIO
from player import Player, PerformanceLog
from data_manager import load_players, save_players, generate_unique_code
from team_generator import generate_balanced_teams
import os

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = '1234'

@app.route('/')
def index():
    players = load_players()
    is_admin = session.get('is_admin', False)
    return render_template('index.html', players=players, is_admin=is_admin)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':
            session['is_admin'] = True
            return redirect(url_for('index'))
        else:
            return render_template('admin_login.html', error="Invalid password")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/player_login', methods=['GET', 'POST'])
def player_login():
    if request.method == 'POST':
        entered_name = request.form['name'].strip().lower()
        entered_code = request.form['access_code'].strip()
        
        players = load_players()
        player = next((p for p in players if p.name.strip().lower() == entered_name and p.access_code == entered_code), None)
        
        if player:
            return redirect(url_for('player_page', player_id=player.id))
        return render_template('player_login.html', error='Invalid name or access code.')
    return render_template('player_login.html')

@app.route('/add_player', methods=['GET', 'POST'])
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
        
        players.append(player)
        save_players(players)
        
        return redirect(url_for('index'))
    return render_template('add_player.html')

@app.route('/regenerate_code/<player_id>', methods=['POST'])
def regenerate_code(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)

    if not player:
        return "Player not found", 404

    if session.get('player_id') != player_id:
        return "Unauthorized", 403

    # Generate new unique code
    existing_codes = {p.access_code for p in players if p.id != player_id}
    
    player.access_code = generate_unique_code(existing_codes)

    save_players(players)
    return redirect(url_for('player_page', player_id=player_id))


@app.route('/remove_player/<player_id>', methods=['POST'])
def remove_player(player_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    players = [p for p in players if p.id != player_id]
    save_players(players)
    return redirect(url_for('index'))

@app.route('/toggle_availability/<player_id>', methods=['POST'])
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
        socketio.emit('availability_updated', {
            'player_id': updated_player.id,
            'available': updated_player.available
        }, to='/')

    # Redirect based on role
    if is_admin:
        return redirect(url_for('index'))
    elif user_id == player_id:
        return redirect(url_for('player_page', player_id=player_id))
    else:
        return "Unauthorized", 403

    

@app.route('/player/<player_id>', methods=['GET', 'POST'])
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
        rating = (
            goals * 2.5 +
            assists * 1.5 +
            tackles * 1.0 +
            saves * 1.5
        ) / 2.0

        # Clamp rating between 1 and 10
        rating = max(1.0, min(round(rating, 2), 10.0))

        
        log = PerformanceLog(goals=goals, assists=assists, tackles=tackles, saves=saves, rating=rating)
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)
        return render_template('thanks.html', player=player)
    
    ratings = [log.rating for log in player.match_history]
    return render_template('player_portal.html', player=player, ratings=ratings)
    
@app.route('/log_performance/<player_id>', methods=['GET', 'POST'])
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
        
        rating = (
            goals * 2.5 +
            assists * 1.5 +
            tackles * 1.0 +
            saves * 1.5
        ) / 2.0
        rating = max(1.0, min(round(rating, 2), 10.0))
        
        log = PerformanceLog(goals=goals, assists=assists, tackles=tackles, saves=saves, rating=rating)
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)
        
        
        rating_diff = round(player.skill_rating - previous_rating, 2)

        return render_template(
        'thanks.html',
         player=player,
         current_rating=player.skill_rating,
         rating_diff=rating_diff
        )
    
    return render_template('log_performance.html', player=player)


@app.route('/assign_captain/<player_id>', methods=['POST'])
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
            break

    save_players(players)
    return redirect(url_for('index'))


@app.route('/draft/start', methods=['POST'])
def start_draft():
    if not session.get('is_admin'):
        return "Unauthorized", 403

    players = load_players()

    # Get the 2 captains
    captains = [p for p in players if p.is_captain]
    if len(captains) != 2:
        return "Exactly 2 captains must be assigned.", 400

    # Sort by skill_rating
    captains = sorted(captains, key=lambda p: p.skill_rating, reverse=True)
    captain1, captain2 = captains

    # Get available non-captain players
    draft_pool = [p for p in players if p.available and not p.is_captain]

    # Initialize draft state in session
    session['draft_state'] = {
        'captain1_id': captain1.id,
        'captain2_id': captain2.id,
        'team1': [],
        'team2': [],
        'remaining_ids': [p.id for p in draft_pool],
        'turn': captain1.id  # highest-rated goes first
    }

    return redirect(url_for('draft_observer_view'))


@app.route('/draft/view')
def draft_observer_view():
    state = session.get('draft_state')
    if not state:
        return "Draft not started", 400

    players = load_players()
    get_player = lambda pid: next(p for p in players if p.id == pid)

    context = {
        'captain1': get_player(state['captain1_id']),
        'captain2': get_player(state['captain2_id']),
        'team1': [get_player(pid) for pid in state['team1']],
        'team2': [get_player(pid) for pid in state['team2']],
        'remaining': [get_player(pid) for pid in state['remaining_ids']],
        'turn': get_player(state['turn']),
    }

    return render_template('draft_observer.html', **context)


@app.route('/draft/captain/<captain_id>')
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


@app.route('/draft/pick/<player_id>', methods=['POST'])
def draft_pick(player_id):
    state = session.get('draft_state')
    captain_id = request.form.get('captain_id')
    
    if not state or player_id not in state['remaining_ids']:
        return "Invalid pick", 400
    
    if captain_id != state['turn']:
        return "It's not your turn!", 403

    # Assign to current captain's team
    if state['turn'] == state['captain1_id']:
        state['team1'].append(player_id)
        next_turn = state['captain2_id']
    else:
        state['team2'].append(player_id)
        next_turn = state['captain1_id']

    state['remaining_ids'].remove(player_id)
    state['turn'] = next_turn
    session['draft_state'] = state

    return redirect(url_for('captain_draft_view', captain_id=next_turn))




@app.route('/generate_teams')
def generate_teams():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    team1, team2 = generate_balanced_teams(players)
    return render_template('team_generator.html', team1=team1, team2=team2)



if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    socketio.run(app, debug=True)