
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, session
from player import Player, PerformanceLog
from data_manager import load_players, save_players, generate_unique_code, load_draft_state, save_draft_state
from team_generator import generate_balanced_teams
import os

app = Flask(__name__)
app.secret_key = '1234'

# -----------------------
#main dashboard view only 

@app.route('/')
def index():
    # Redirect players who are logged in
    #if session.get('player_id') and not session.get('is_admin'):
     #   return redirect(url_for('player_page', player_id=session['player_id']))
    if session.get('is_admin') and session.get('player_id'):
        session.pop('player_id') 
    players = load_players()
    is_admin = session.get('is_admin', False)
    #config = load_config()
    #ratings_enabled = config.get("ratings_enabled", True)
    return render_template('index.html', players=players, is_admin=is_admin,) 

#admin log in

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':
            session['is_admin'] = True
            session.pop('player_id', None)
            return redirect(url_for('index'))
        else:
            return render_template('admin_login.html', error="Invalid password")
    return render_template('admin_login.html')

#admin logout 

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

#player log in

@app.route('/player_login', methods=['GET', 'POST'])
def player_login():
    if request.method == 'POST':
        entered_name = request.form['name'].strip().lower()
        entered_code = request.form['access_code'].strip()
        
        players = load_players()
        player = next((p for p in players if p.name.strip().lower() == entered_name and p.access_code == entered_code), None)
        
        if player:
            session['player_id'] = player.id  # ✅ Ensure we set the correct session
            session.pop('is_admin', None)     # ✅ Clear admin session
            return redirect(url_for('player_page', player_id=player.id))
        return render_template('player_login.html', error='Invalid name or access code.')
    return render_template('player_login.html')
#-----------------------------------------------------
#ADMIN ONLY add player logic

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
        
        player = Player(
            name=name, 
            position=position, 
            skill_rating=skill_rating
        )
        player.inbox = []
        
        player.access_code = access_code
        player.age = age
        
        players.append(player)
        save_players(players)
        
        return redirect(url_for('index'))
    return render_template('add_player.html')

#ADMIN Only Remove Player Logic 
 
@app.route('/remove_player/<player_id>', methods=['POST'])
def remove_player(player_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    players = [p for p in players if p.id != player_id]
    save_players(players)
    return redirect(url_for('index'))

# ADMIN ONLY assign captain logic


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
            if player.is_captain:
                if not any("assigned as a captain" in note["message"] for note in player.notifications):
                    message = ({
                        "message": "You've been assigned as a captain! Go to your dashboard when the draft begins.",
                        "timestamp": datetime.now().isoformat()
                     })
                    player.notifications.append(message)
                    player.inbox.append(message)
            break

    save_players(players)
    return redirect(url_for('index'))

#ADMIN ONLY start draft 




# --------------------------------------------

#ADMIN and PLAYER ONLY Toggle availability

@app.route('/toggle_availability/<player_id>', methods=['POST'])
def toggle_availability(player_id):
    players = load_players()
    user_id = session.get('player_id')
    print("SESSION STATE →", session)

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

    # Redirect based on role
    if user_id == player_id:
        return redirect(url_for('player_page', player_id=player_id))  # ✅ Player stays on portal
    elif is_admin:
        return redirect(url_for('index'))  # ✅ Admin goes to dashboard
    else:
        return redirect(request.referrer or url_for('index'))

    
#ADMIN and PLAYER - LOG PERFORMANCE
    
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
        
        match_id = datetime.now().isoformat()
        log = PerformanceLog(
            goals=goals, 
            assists=assists, 
            tackles=tackles, 
            saves=saves, 
            rating=rating,
            match_id=match_id
            )
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)

        rating_diff = round(player.skill_rating - previous_rating, 2)

        session['player_id'] = player.id
        
     

        return render_template(
            "thanks.html",
            player=player,
            current_rating=player.skill_rating,
            rating_diff=0,
            #next_url=next_url,
            message="Stats submitted successfully!"
        )

    return render_template('log_performance.html', player=player)


#PLAYER ONLY Player Profile 

@app.route('/player_profile/<target_id>', methods=['GET', 'POST'])
def player_profile(target_id):
    players = load_players()
    
    viewer_id = session.get('player_id')
    target_player = next((p for p in players if p.id == target_id), None)
    is_admin = session.get('is_admin', False)
    viewer = next((p for p in players if p.id == viewer_id), None)

    if not target_player:
        return "Player not found", 403
    
    # Allow admin access without being a player
    if not viewer and not is_admin:
        return "Unauthorized", 403

    if target_id == viewer_id:
        return "You cannot rate yourself", 403

    # Get most recent match
    recent_log = target_player.match_history[-1] if target_player.match_history else None
    match_id = recent_log.match_id if recent_log else None

    # Prevent rating more than once per match
    has_already_rated = any(
        rating['from'] == viewer_id and rating['match_id'] == match_id
        for rating in target_player.ratings_received
    )

    if request.method == 'POST' and match_id and not has_already_rated:
        rating = int(request.form['rating'])
        comment = request.form.get('comment', '')

        # Save the rating
        target_player.ratings_received.append({
            "from": viewer_id,
            "match_id": match_id,
            "rating": rating,
            "comment": comment
        })

        # Optional: Add a basic notification system
        if not hasattr(target_player, 'notifications'):
            target_player.notifications = []

        message = {
            "type": "rating_received",
            "from": viewer.name,
            "rating": rating,
            "comment": comment,
            "match_id": match_id,
            "timestamp": datetime.now().isoformat()
             }

        target_player.notifications.append(message)
        target_player.inbox.append(message)

        save_players(players)

        return render_template(
            'thanks.html',
            player=viewer,
            message="Rating submitted successfully!",
            rating_diff=0
        )

    return render_template(
        'player_profile.html',
        target=target_player,
        recent_log=recent_log,
        viewer_id=viewer_id,
        has_already_rated=has_already_rated
    )


#PLAYER ONLY - Access Code Regenerator 

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




# Player rating logic - perfomance stats = overall rating

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
    
    # Check if this player is a captain and draft is ongoing
    
    
    show_draft_panel = False
    draft_context = {}
    
    draft_state = load_draft_state()
    if draft_state and player.is_captain:
        get_player = lambda pid: next((p for p in players if p.id == pid), None)
        
        if draft_state.get("complete"):
           # Show team directly in portal instead of redirecting
        
        
            draft_context = {
                'captain_id': player.id,
                'this_captain': player,
                'is_my_turn': False,
                'remaining': [],
                'team1': [p for pid in draft_state['team1'] if (p := get_player(pid))],
                'team2': [p for pid in draft_state['team2'] if (p := get_player(pid))],
                'captain1': get_player(draft_state['captain1_id']),
                'captain2': get_player(draft_state['captain2_id']),
                }
           
        else:

        
            show_draft_panel = True
            
       
            draft_context = {
                'captain_id': player_id,
                'this_captain': player,
                'is_my_turn': draft_state['turn'] == player_id,
                'remaining': [p for pid in draft_state['remaining_ids'] if (p := get_player(pid))],
                'team1': [p for pid in draft_state['team1'] if (p := get_player(pid))],
                'team2': [p for pid in draft_state['team2'] if (p := get_player(pid))],
                'captain1': get_player(draft_state['captain1_id']),
                'captain2': get_player(draft_state['captain2_id']),
                }
        
    ratings = [log.rating for log in player.match_history]
    return render_template(
        'player_portal.html',
        player=player,
        ratings=ratings,
        show_draft_panel=show_draft_panel,
        draft_context=draft_context,
        is_admin=session.get('is_admin', False)
    )
    
    
@app.route('/draft/start', methods=['POST'])
def start_draft():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    
    # Clear any previous draft state
    session.pop('draft_state', None)

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
    state = ({
        'captain1_id': captain1.id,
        'captain2_id': captain2.id,
        'team1': [],
        'team2': [],
        'remaining_ids': [p.id for p in draft_pool],
        'turn': captain1.id  # highest-rated goes first
    })
    
    save_draft_state(state)
    session['draft_state'] = state

    return redirect(url_for('draft_observer_view'))

@app.route('/admin/ratings')
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
   
    
    

#Players view 

@app.route('/players')
def view_players():
    if 'player_id' not in session:
        return redirect(url_for('player_login'))

    players = load_players()
    viewer_id = session['player_id']
    return render_template('view_players.html', players=players, viewer_id=viewer_id)

@app.route('/clear_notifications/<player_id>', methods=['POST'])
def clear_notifications(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if player and session.get('player_id') == player_id:
        player.notifications = []
        save_players(players)
    return redirect(url_for('player_page', player_id=player_id))

#Draft observer ADMIN and PLAYERS not CAPTAINS. Captains get their own interactive view.

@app.route('/draft/view')
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

#CAPTAIN Only Draft View 

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

#CAPTAIN ONLY Draft Pick logic 

@app.route('/draft/pick/<player_id>', methods=['POST'])
def draft_pick(player_id):
    state = load_draft_state()
    captain_id = request.form.get('captain_id')
    
    if not state or player_id not in state['remaining_ids']:
        return "Invalid pick", 400
    
    if captain_id != state['turn']:
        return "It's not your turn!", 403

    # Assign to current captain's team
    if state['turn'] == state['captain1_id']:
        state['team1'].append(player_id)
        next_turn = state.get('captain2_id')
    else:
        state['team2'].append(player_id)
        next_turn = state.get('captain1_id')

    state['remaining_ids'].remove(player_id)
    
    # Check if draft is complete 
    if not state['remaining_ids']:
        # Draft complete update both captains' notifications
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
        #Optionally, mark the draft state as complete
        state['complete'] = True
        state['turn'] = None
    else:
        #Set turn to next captain
         state['turn'] = next_turn
    
    save_draft_state(state)
    session['draft_state'] = state

    if state.get('complete'):
        return redirect(url_for('draft_final_view', captain_id=captain_id))
    else:
        return redirect(url_for('player_page', player_id=captain_id))



@app.route('/draft/final/<captain_id>')
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


#Team generator 

@app.route('/generate_teams')
def generate_teams():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    players = load_players()
    team1, team2 = generate_balanced_teams(players)
    return render_template('team_generator.html', team1=team1, team2=team2)


@app.route('/message_team/<captain_id>', methods=['GET', 'POST'])
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
            message = {
                "message": f"Captain {captain.name} says: {message}",
                "timestamp": timestamp
            }
            teammate.notifications.append(message)
            teammate.inbox.append(message)
            
        save_players(players)
        
        return render_template('thanks.html', player=captain, message="Team notified successfully!", rating_diff=0)
    
    return render_template('message_team.html', captain=captain, teammates=team_players)

@app.route('/inbox/<player_id>')
def player_inbox(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)

    if not player or session.get('player_id') != player_id:
        return "Unauthorized", 403
    
    print("DEBUG: Inbox contains →", player.inbox)
    print("DEBUG → inbox from file:", player.inbox)

    return render_template('player_inbox.html', player=player, inbox=player.inbox)


if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)
