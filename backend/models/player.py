import uuid
from backend.models.performance import update_skill_rating, recent_form, PerformanceLog

class Player:
    def __init__(
        self,
        name,
        position,
        skill_rating,
        player_id=None,
        available=True,
        role='player',
        is_captain=False,
        match_history=None,
        access_code=None,
        ratings_received=None,
        notifications=None
    ):
        self.id = player_id or str(uuid.uuid4())
        self.name = name
        self.position = position
        self.skill_rating = skill_rating
        self.available = available
        self.role = role
        self.access_code = access_code or str(uuid.uuid4())[:6]
        self.ratings_received = ratings_received or []
        self.notifications = notifications or []
        self.inbox = []
        self.is_captain = is_captain
        self.match_history = match_history or []

    def update_performance(self, performance):
        self.match_history.append(performance)

    def update_skill_rating(self):
        self.skill_rating = update_skill_rating(self.skill_rating, self.match_history)

    def recent_form(self):
        return recent_form(self.match_history, self.skill_rating)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'skill_rating': self.skill_rating,
            'available': self.available,
            'role': self.role,
            'access_code': self.access_code,
            'is_captain': self.is_captain,
            'match_history': [p.to_dict() for p in self.match_history],
            'ratings_received': self.ratings_received,
            'notifications': getattr(self, 'notifications', []),
            'inbox': self.inbox
        }

    @staticmethod
    def from_dict(data):
        match_history = [PerformanceLog.from_dict(p) for p in data.get('match_history', [])]
        player = Player(
            name=data['name'],
            position=data['position'],
            skill_rating=data['skill_rating'],
            player_id=data['id'],
            available=data.get('available', True),
            role=data.get('role', 'player'),
            access_code=data.get('access_code'),
            is_captain=data.get('is_captain', False),
            match_history=match_history,
            ratings_received=data.get('ratings_received', []),
            notifications=data.get('notifications', [])
        )
        player.inbox = data.get("inbox", [])
        return player
