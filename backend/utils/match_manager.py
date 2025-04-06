# backend/utils/match_manager.py
# Now primarily focuses on converting data to/from Match objects
import os
from datetime import datetime
from backend.models.match import Match
# Import the data loading/saving functions from data_manager
from backend.utils.data_manager import load_matches_data, save_matches_data

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
    
    
    

   # Finds the next upcoming match that hasn't started yet.
   # This can be used to associate a draft with the next scheduled match.
   
    
def get_current_draft_match():
    matches = load_matches()
    now = datetime.now()
    
    future_matches = []
    for m in matches:
        try:
            match_date = datetime.strptime(m.date, "%Y-%m-%d").date()
            if match_date >= now.date():
                future_matches.append((match_date, m))
        except Exception as e:
            print(f"Skipping invalid match date: {m.date}, error: {e}")
            
    future_matches.sort(key=lambda tup: tup[0])
    return future_matches[0][1] if future_matches else None
                