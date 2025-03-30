import uuid
from datetime import datetime, timedelta

class Match:
    def __init__(
        self,
        match_id=None,
        date=None,
        start_time=None,
        duration_minutes=60,
        players=None,
        is_completed=False
    ):
        self.match_id = match_id or str(uuid.uuid4())
        self.date = date or datetime.now().date().isoformat()
        self.start_time = start_time or datetime.now().time().isoformat()
        self.duration_minutes = duration_minutes
        self.players = players or []  # list of player IDs
        self.is_completed = is_completed

    def has_player(self, player_id):
        return player_id in self.players

    def end_time(self):
        start = datetime.fromisoformat(f"{self.date}T{self.start_time}")
        return start + timedelta(minutes=self.duration_minutes)

    def to_dict(self):
        return {
            "match_id": self.match_id,
            "date": self.date,
            "start_time": self.start_time,
            "duration_minutes": self.duration_minutes,
            "players": self.players,
            "is_completed": self.is_completed
        }

    @staticmethod
    def from_dict(data):
        return Match(
            match_id=data.get("match_id"),
            date=data.get("date"),
            start_time=data.get("start_time"),
            duration_minutes=data.get("duration_minutes", 60),
            players=data.get("players", []),
            is_completed=data.get("is_completed", False)
        )
