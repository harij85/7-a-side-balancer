# backend/utils/match_manager.py
# Now primarily focuses on converting data to/from Match objects
import os
from backend.models.match import Match
# Import the data loading/saving functions from data_manager
from .data_manager import load_matches_data, save_matches_data, MATCH_FILE

# No longer need ensure_match_file_exists, handled by data_manager helpers

def load_matches():
    """Loads matches from storage and returns them as Match objects."""
    matches_data = load_matches_data()
    matches = []
    for data in matches_data:
        if isinstance(data, dict):
            try:
                matches.append(Match.from_dict(data))
            except Exception as e:
                print(f"Error loading match data: {data}. Error: {e}")
        else:
            print(f"Skipping invalid match data entry: {data}")
    return matches

def save_matches(matches):
    """Saves a list of Match objects to storage."""
    if not isinstance(matches, list) or not all(isinstance(m, Match) for m in matches):
         raise ValueError("save_matches expects a list of Match objects.")
    save_matches_data([m.to_dict() for m in matches])

# Function to get a specific match (optional helper)
def get_match_by_id(match_id):
    matches = load_matches()
    return next((m for m in matches if m.match_id == match_id), None)