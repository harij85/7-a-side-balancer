from flask import Blueprint, jsonify, request
from backend.utils.data_manager import load_players, save_players, get_player

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

@api_bp.route('/players')
def get_players():
    players = load_players()
    players.sort(key=lambda x: x.skill_rating, reverse=True)
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 14))
    
    start = (page - 1) * per_page
    end = start + per_page
    sliced = players[start:end]
    
    return jsonify({
        "players": [{
            "id": p.id,
            "name": p.name,
            "position": p.position,
            "skill_rating": p.skill_rating,
            "is_captain": p.is_captain,
            "access_code": p.access_code,
            "available": p.available
        } for p in sliced],
        "has_more": end < len(players)
    })
    
@api_bp.route('/inbox/<player_id>')
def get_inbox(player_id):
        player = get_player(load_players(), player_id)
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        return jsonify({
            "inbox": sorted(player.inbox, key=lambda x: x.get('timestamp', ''), reverse=True)
        })
        
@api_bp.route('/notifications/<player_id>')
def get_notifications(player_id):
    player = get_player(load_players(), player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    
    return jsonify({
        "notifications": [n for n in player.notifications if not n.get('read', False)]
    })
    
@api_bp.route('/notifications/<player_id>/read', methods=['POST'])
def mark_all_notifications_read(player_id):
    player = get_player(load_players(), player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    
    for n in player.notifications:
        n['read'] = True
        
    save_players(load_players()) 
    return jsonify({"message": "Marked as read"})

