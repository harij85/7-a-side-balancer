import json
from backend.utils.data_manager import load_players, save_players

def migrate_players_player_ratings():
    players = load_players()
    changes = 0

    for player in players:
        if not player.players_player_ratings:
            continue

        # Get latest match_id if available
        if not player.match_history:
            continue  # No match data, skip

        latest_match_id = player.match_history[-1].match_id

        for rating in player.players_player_ratings:
            if 'match_id' not in rating:
                rating['match_id'] = latest_match_id
                changes += 1

    if changes > 0:
        save_players(players)
        print(f"✅ Migration complete. {changes} ratings updated with match_id.")
    else:
        print("ℹ️ No ratings needed updating.")

if __name__ == "__main__":
    migrate_players_player_ratings()

