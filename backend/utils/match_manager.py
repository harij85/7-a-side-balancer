import os
import json
from backend.models.match import Match

MATCH_FILE = 'backend/data/matches.json'

def ensure_match_file_exists():
    os.makedirs(os.path.dirname(MATCH_FILE), exist_ok=True)
    if not os.path.exists(MATCH_FILE):
        with open(MATCH_FILE, 'w', encoding='utf8') as f:
            json.dump([], f)

def load_matches():
    ensure_match_file_exists()
    with open(MATCH_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
        return [Match.from_dict(d) for d in data]

def save_matches(matches):
    ensure_match_file_exists()
    with open(MATCH_FILE, 'w', encoding='utf8') as f:
        json.dump([m.to_dict() for m in matches], f, indent=2)
