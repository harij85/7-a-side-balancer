import json 
import os
from player import Player

DATA_PATH = "data/players.json"

def load_players():
    if not os.path.exists(DATA_PATH):
        return []
    
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
        return [Player.from_dict(p) for p in data]
    
def save_players(players):
    with open(DATA_PATH, "w") as f:
        json.dump([p.to_dict() for p in players], f, indent=4)