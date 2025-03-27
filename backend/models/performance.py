# backend/models/performance.py

from datetime import datetime

class PerformanceLog:
    def __init__(self, goals=0, assists=0, tackles=0, saves=0, rating=0, match_id=None):
        self.goals = goals
        self.assists = assists
        self.tackles = tackles
        self.saves = saves
        self.rating = rating
        self.match_id = match_id or datetime.now().isoformat()

    def to_dict(self):
        return {
            "goals": self.goals,
            "assists": self.assists,
            "tackles": self.tackles,
            "saves": self.saves,
            "rating": self.rating,
            "match_id": self.match_id
        }

    @staticmethod
    def from_dict(data):
        return PerformanceLog(
            goals=data.get("goals", 0),
            assists=data.get("assists", 0),
            tackles=data.get("tackles", 0),
            saves=data.get("saves", 0),
            rating=data.get("rating", 0),
            match_id=data.get("match_id")
        )

def update_skill_rating(current_rating, match_history):
    if not match_history:
        return current_rating
    recent_logs = match_history[-5:]
    avg_rating = sum(log.rating for log in recent_logs) / len(recent_logs)
    new_rating = round((current_rating * 0.6 + avg_rating * 0.4), 2)
    return max(1, min(10, new_rating))

def recent_form(match_history, fallback_rating):
    if not match_history:
        return fallback_rating
    recent = match_history[-3:]
    return sum(p.rating for p in recent) / len(recent)
