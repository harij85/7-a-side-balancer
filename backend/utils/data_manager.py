import uuid
import json 
import os
from backend.models.player import Player

DATA_PATH = "data/players.json"
CONFIG_FILE = 'config.json'
DRAFT_FILE = 'draft_state.json'

def load_draft_state():
    if os.path.exists(DRAFT_FILE):
        with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
         try:
            return json.load(f)
         except json.JSONDecodeError:
            return None

def save_draft_state(state):
    with open(DRAFT_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"ratings_enabled": True}
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def load_players():
    if not os.path.exists(DATA_PATH):
        return []
    
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        players = [Player.from_dict(p) for p in data]
    
        for player in players:
            if not hasattr(player, 'inbox'):
                player.inbox = []
        return players

    
def save_players(players):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in players], f, indent=4)
        
def generate_unique_code(existing_codes):
    """Generate a short unique code not in existing_codes"""
    while True:
        new_code = str(uuid.uuid4())[:6]
        if new_code not in existing_codes:
            return new_code

