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
        is_completed=False,
        location=None,
        num_teams=2,
        players_per_team=7,
        team_selection_method='auto',
        draft_created=False, 
        captains=None# can be 'draft' or 'auto'
    ):
        self.match_id = match_id or str(uuid.uuid4())
        self.date = date or datetime.now().date().isoformat()
        self.start_time = start_time or datetime.now().time().isoformat()
        self.duration_minutes = duration_minutes
        self.players = players or []
        self.is_completed = is_completed
        self.location = location
        self.num_teams = num_teams
        self.players_per_team = players_per_team
        self.team_selection_method = team_selection_method
        self.draft_created = draft_created
        self.captains = captains if captains is not None else []

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
            "is_completed": self.is_completed,
            "location": self.location,
            "num_teams": self.num_teams,
            "players_per_team": self.players_per_team,
            "team_selection_method": self.team_selection_method,
            "draft_created": self.draft_created,
            "captains": self.captains
        }

    @staticmethod
    def from_dict(data):
        return Match(
            match_id=data.get("match_id"),
            date=data.get("date"),
            start_time=data.get("start_time"),
            duration_minutes=data.get("duration_minutes", 60),
            players=data.get("players", []),
            is_completed=data.get("is_completed", False),
            location=data.get("location"),
            num_teams=data.get("num_teams", 2),
            players_per_team=data.get("players_per_team", 7),
            team_selection_method=data.get("team_selection_method", 'auto'),
            draft_created=data.get("draft_created", False),
            captains=data.get("captains", None)
        )
