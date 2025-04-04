import os
import json
import uuid
from datetime import datetime, timedelta

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INVITE_FILE = os.path.join(DATA_DIR, 'invite_links.json')

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

# ---- Load & Save Helpers ----
def _load_json():
    ensure_data_dir()
    if not os.path.exists(INVITE_FILE):
        return []
    with open(INVITE_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _save_json(data):
    ensure_data_dir()
    with open(INVITE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ---- Invite Generation ----
def generate_invite_code():
    return str(uuid.uuid4())[:8].upper()

def generate_invite_link(created_by='admin', max_uses=5, days_valid=7):
    code = generate_invite_code()
    created_at = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
    invite = {
        'code': code,
        'created_by': created_by,
        'created_at': created_at,
        'expires_at': expires_at,
        'max_uses': max_uses,
        'uses': 0
    }
    invites = _load_json()
    invites.append(invite)
    _save_json(invites)
    return code

# ---- Validation & Usage ----
def validate_invite(code):
    invites = _load_json()
    for invite in invites:
        if invite['code'] == code:
            try:
                if invite['uses'] < invite['max_uses'] and datetime.now() < datetime.fromisoformat(invite['expires_at']):
                    return True
            except Exception:
                return False
    return False

def increment_invite_use(code):
    invites = _load_json()
    for invite in invites:
        if invite['code'] == code:
            invite['uses'] += 1
            break
    _save_json(invites)

def get_invite_data(code):
    invites = _load_json()
    for invite in invites:
        if invite['code'] == code:
            return invite
    return None

def revoke_invite(code):
    """Revoke invite by setting uses = max_uses"""
    invites = _load_json()
    for invite in invites:
        if invite['code'] == code:
            invite['uses'] = invite['max_uses']
            break
    _save_json(invites)

def get_all_invites():
    return _load_json()
