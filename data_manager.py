import uuid
import json 
import os
from player import Player

DATA_PATH = "data/players.json"

def load_players():
    if not os.path.exists(DATA_PATH):
        return []
    
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Player.from_dict(p) for p in data]
    
def save_players(players):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in players], f, indent=4)
        
def generate_unique_code(existing_codes):
    """Generate a short unique code not in existing_codes"""
    while True:
        new_code = str(uuid.uuid4())[:6]
        if new_code not in existing_codes:
            return new_code
