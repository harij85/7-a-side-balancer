from flask import Flask, render_template, redirect, url_for, request
from player import Player, PerformanceLog
from data_manager import load_players, save_players
from team_generator import generate_balanced_teams
import os

app = Flask(__name__)

@app.route('/')
def index():
    players = load_players()
    return render_template('index.html', players=players)

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        players = load_players()
        name = request.form['name']
        position = request.form['position']
        skill_rating = float(request.form['skill_rating'])
        age = int(request.form['age'])
        player = Player(name=name, position=position, skill_rating=skill_rating)
        player.age = age
        players.append(player)
        save_players(players)
        return redirect(url_for('index'))
    return render_template('add_player.html')

@app.route('/remove_player/<player_id>', methods=['POST'])
def remove_player(player_id):
    players = load_players()
    players = [p for p in players if p.id != player_id]
    save_players(players)
    return redirect(url_for('index'))

@app.route('/toggle_availability/<player_id>', methods=['POST'])
def toggle_availability(player_id):
    players = load_players()
    for player in players:
        if player.id == player_id:
            player.available = not player.available
            save_players(players)
            return redirect(url_for('index'))
    return "player not found", 404

@app.route('/player/<player_id>', methods=['GET', 'POST'])
def player_page(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if not player:
        return "Player not found", 404
    
    if request.method == 'POST':
        
        goals = int(request.form['goals'])
        assists = int(request.form['assists'])
        tackles = int(request.form['tackles'])
        saves = int(request.form['saves'])
        rating = float(request.form['rating'])
        
        log = PerformanceLog(goals=goals, assists=assists, tackles=tackles, saves=saves, rating=rating)
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)
        return render_template('thanks.html', player=player)
    
    return render_template('player_portal.html', player=player)
    
@app.route('/log_performance/<player_id>', methods=['GET', 'POST'])
def log_performance(player_id):
    players = load_players()
    player = next((p for p in players if p.id == player_id), None)
    if not player:
        return "Player not found", 404
    
    if request.method == 'POST':
        goals = int(request.form['goals'])
        assists = int(request.form['assists'])
        tackles = int(request.form['tackles'])
        saves = int(request.form['saves'])
        rating = float(request.form['rating'])
        
        log = PerformanceLog(goals=goals, assists=assists, tackles=tackles, saves=saves, rating=rating)
        player.update_performance(log)
        player.update_skill_rating()
        save_players(players)
        return redirect(url_for('index'))
    
    return render_template('log_performance.html', player=player)

@app.route('/generate_teams')
def generate_teams():
    players = load_players()
    team1, team2 = generate_balanced_teams(players)
    return render_template('team_generator.html', team1=team1, team2=team2)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)  