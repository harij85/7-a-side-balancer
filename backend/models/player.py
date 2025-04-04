# backend/models/player.py
import uuid
from backend.models.performance import update_skill_rating, recent_form, PerformanceLog


class Player:
    def __init__(
        self,
        name,
        position,
        skill_rating,
        age=None, # Added age, default to None
        player_id=None,
        available=True,
        role='player',
        preferred_foot=None,
        preferred_days=None,
        preferred_times=None,
        preferred_locations=None,
        is_captain=False,
        match_history=None,
        access_code=None,
        ratings_received=None,
        notifications=None,
        inbox=None, # Explicitly added inbox
        players_player_ratings=None # Explicitly added players_player_ratings
        
    ):
        self.id = player_id or str(uuid.uuid4())
        self.name = name
        self.position = position.upper() # Store position consistently
        self.skill_rating = skill_rating
        self.age = age # Store age
        self.available = available
        self.role = role
        self.preferred_foot = preferred_foot
        self.preferred_days = preferred_days
        self.preferred_times = preferred_times
        self.preferred_locations = preferred_locations
        self.access_code = access_code or str(uuid.uuid4())[:6].upper() # Ensure unique code is generated if None
        self.is_captain = is_captain
        self.match_history = match_history or []
        # Ensure lists are initialized properly if None
        self.ratings_received = ratings_received if ratings_received is not None else []
        self.notifications = notifications if notifications is not None else []
        self.inbox = inbox if inbox is not None else []
        self.players_player_ratings = players_player_ratings if players_player_ratings is not None else []

        # Attribute for calculating rating difference in views
        self.rating_diff = 0
        self._calculate_rating_diff()

    def _calculate_rating_diff(self):
        """Helper to calculate rating difference from last two matches."""
        if len(self.match_history) >= 2:
            last = self.match_history[-1].rating
            second_last = self.match_history[-2].rating
            self.rating_diff = round(last - second_last, 2)
        else:
            self.rating_diff = 0

    def update_performance(self, performance: PerformanceLog):
        self.match_history.append(performance)
        self._calculate_rating_diff() # Recalculate difference after adding performance

    def update_skill_rating(self):
        # Avoid mutation if no history
        if not self.match_history:
            return
        self.skill_rating = update_skill_rating(self.skill_rating, self.match_history)
        # Optionally, round the skill rating here if desired
        # self.skill_rating = round(self.skill_rating, 2)

    def recent_form(self):
        return recent_form(self.match_history, self.skill_rating)

    def has_rated_player(self, target_player, match_id):
        # This method checked 'ratings_received', which is for ratings *of* the target player.
        # It seems intended to check if *this* player has rated the target.
        # Let's assume it checks the target's players_player_ratings list.
        return any(
            r['from'] == self.id and r['match_id'] == match_id
            for r in target_player.players_player_ratings # Check the correct list
        )

    def add_notification(self, notification_data):
        """Adds a notification and mirrors it to the inbox."""
        # Ensure timestamp if not provided
        if "timestamp" not in notification_data:
            from datetime import datetime
            notification_data["timestamp"] = datetime.now().isoformat()
        self.notifications.append(notification_data)
        self.inbox.append(notification_data) # Mirror to inbox

    def clear_notifications(self):
        """Clears only the notifications list, leaving inbox intact."""
        self.notifications = []

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'skill_rating': self.skill_rating,
            'age': self.age, # Added age
            'available': self.available,
            'role': self.role,
            'preferred_foot': self.preferred_foot,
            'preferred_days': self.preferred_days,
            'preferred_times': self.preferred_times,
            'preferred_locations': self.preferred_locations,
            'access_code': self.access_code,
            'is_captain': self.is_captain,
            'match_history': [p.to_dict() for p in self.match_history],
            'ratings_received': self.ratings_received,
            'notifications': self.notifications, # Use the property directly
            'inbox': self.inbox, # Use the property directly
            'players_player_ratings': self.players_player_ratings # Use the property
        }

    @staticmethod
    def from_dict(data):
        # Ensure match history is parsed correctly
        match_history_data = data.get('match_history', [])
        match_history = [PerformanceLog.from_dict(p) for p in match_history_data if isinstance(p, dict)]

        player = Player(
            name=data['name'],
            position=data.get('position', 'Unknown'), # Default position
            skill_rating=data.get('skill_rating', 5.0), # Default rating
            age=data.get('age'), # Get age
            player_id=data.get('id'), # Use get for id
            available=data.get('available', True),
            role=data.get('role', 'player'),
            preferred_foot=data.get('preferred_foot'),
            preferred_days=data.get('preferred_days'),
            preferred_times=data.get('preferred_times'),
            preferred_locations=data.get('preferred_locations'),
            access_code=data.get('access_code'),
            is_captain=data.get('is_captain', False),
            match_history=match_history,
            ratings_received=data.get('ratings_received'), # Let constructor handle None
            notifications=data.get('notifications'), # Let constructor handle None
            inbox=data.get('inbox'), # Let constructor handle None
            players_player_ratings=data.get('players_player_ratings') # Let constructor handle None
        )
        # Note: rating_diff is calculated dynamically, no need to load/save
        return player