import uuid

class PerformanceLog:
    def __init__(self, goals=0, assists=0, tackles=0, saves=0, rating=0):
        self.goals = goals
        self.assists = assists
        self.tackles = tackles
        self.saves = saves
        self.rating = rating

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return PerformanceLog(**data)

class Player:
    def __init__(self, name, position, skill_rating, player_id=None, available=True, role='player', is_captain=False, match_history=None, access_code=None):
        self.id = player_id or str(uuid.uuid4())
        self.name = name
        self.position = position
        self.skill_rating = skill_rating
        self.available = available
        self.role = role
        self.access_code = access_code or str(uuid.uuid4())[:6]
        self.is_captain = is_captain
        self.match_history = match_history or []

    def update_performance(self, performance):
        self.match_history.append(performance)

    def recent_form(self):
        if not self.match_history:
            return self.skill_rating
        recent = self.match_history[-3:]
        return sum(p.rating for p in recent) / len(recent)

    def update_skill_rating(self):
        if not self.match_history:
            return
        recent_logs = self.match_history[-5:]
        avg_rating = sum(log.rating for log in recent_logs) / len(recent_logs)
        self.skill_rating = round((self.skill_rating * 0.6 + avg_rating * 0.4), 2)
        self.skill_rating = max(1, min(10, self.skill_rating))

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
            'match_history': [p.to_dict() for p in self.match_history]
        }

    @staticmethod
    def from_dict(data):
        match_history = [PerformanceLog.from_dict(p) for p in data.get('match_history', [])]
        return Player(
            name=data['name'],
            position=data['position'],
            skill_rating=data['skill_rating'],
            player_id=data['id'],
            available=data.get('available', True),
            role=data.get('role', 'player'),
            access_code=data.get('access_code'),
            is_captain=data.get('is_captain', False),
            match_history=match_history
        )
