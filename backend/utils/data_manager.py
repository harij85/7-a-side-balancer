# backend/utils/data_manager.py
import uuid
import json
import os
from backend.models.player import Player # Corrected import path if needed


# Define paths relative to this file's directory or use absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # backend directory
DATA_DIR = os.path.join(BASE_DIR, 'data')
PLAYER_FILE = os.path.join(DATA_DIR, 'players.json')
DRAFT_FILE = os.path.join(DATA_DIR, 'draft_state.json')
CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), 'config.json') # config.json at project root
MATCH_FILE = os.path.join(DATA_DIR, 'matches.json') # Moved match file path definition here


def ensure_data_dir_exists():
    """Creates the data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)

def _load_json(filepath, default=None):
    """Helper function to load JSON data from a file."""
    ensure_data_dir_exists()
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Log error or handle appropriately
        print(f"Error reading or decoding JSON from {filepath}")
        return default

def _save_json(filepath, data):
    """Helper function to save data to a JSON file."""
    ensure_data_dir_exists()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4) # Use indent 4 for consistency
    except IOError:
        # Log error or handle appropriately
        print(f"Error writing JSON to {filepath}")


# --- Draft State ---
def load_draft_state():
    return _load_json(DRAFT_FILE, default={}) # Return empty dict if file missing/invalid

def save_draft_state(state):
    _save_json(DRAFT_FILE, state)

# --- Config ---
def load_config():
    return _load_json(CONFIG_FILE, default={"ratings_enabled": True})

def save_config(config):
    _save_json(CONFIG_FILE, config)

# --- Players ---
def load_players():
    players_data = _load_json(PLAYER_FILE, default=[])
    # Ensure data is a list
    if not isinstance(players_data, list):
        print(f"Warning: {PLAYER_FILE} does not contain a valid list. Returning empty list.")
        return []
    players = []
    for p_data in players_data:
         # Add basic validation
        if isinstance(p_data, dict) and 'name' in p_data and 'id' in p_data:
             try:
                players.append(Player.from_dict(p_data))
             except Exception as e:
                 print(f"Error loading player data: {p_data}. Error: {e}")
        else:
            print(f"Skipping invalid player data entry: {p_data}")

    # Recalculate rating differences after loading
    for player in players:
        player._calculate_rating_diff()
    return players

def save_players(players):
    if not isinstance(players, list) or not all(isinstance(p, Player) for p in players):
         raise ValueError("save_players expects a list of Player objects.")
    _save_json(PLAYER_FILE, [p.to_dict() for p in players])

# --- Matches (Moved from match_manager.py for consistency) ---
def load_matches_data():
    """Loads raw match data from JSON."""
    return _load_json(MATCH_FILE, default=[])

def save_matches_data(matches_data):
    """Saves raw match data to JSON."""
    _save_json(MATCH_FILE, matches_data)


# --- Utility ---
def generate_unique_code(existing_codes):
    """Generate a short unique uppercase code not in existing_codes set."""
    while True:
        new_code = str(uuid.uuid4())[:6].upper() # Make codes uppercase
        if new_code not in existing_codes:
            return new_code
        
# --- Lookup ---
def get_player(players, player_id):
    """Safely retrieves a Player object by ID from a list of Player instances."""
    for p in players:
        if isinstance(p, Player) and p.id == player_id:
            return p
    print(f"[DEBUG] get_player: Player ID '{player_id}' not found in list.")
    return None