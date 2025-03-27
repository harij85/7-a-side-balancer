from collections import defaultdict
import random

TEAM_SIZE = 7
POSITION_QUOTA = {
    "GK": 1,
    "DEF": 1,
    "MID": 1,
    "ATT": 1
}

def get_best_fallback_player(pos, candidates):
    if not candidates:
        return None

    def fallback_score(p):
        last = p.match_history[-1] if p.match_history else None
        if not last:
            return 0

        if pos == "GK":
            return last.saves + 0.5 * last.rating
        elif pos == "DEF":
            return last.tackles + 0.5 * last.rating
        elif pos == "MID":
            return last.rating  # general all-rounder
        elif pos == "ATT":
            return last.goals + last.assists + 0.5 * last.rating
        return 0

    # Return player with best "fit" for that position
    return max(candidates, key=fallback_score)


def generate_balanced_teams(players):
    available = [p for p in players if p.available]
    if len(available) < 2:
        return [], []

    # Normalize positions
    for p in available:
        p.position = p.position.upper()

    # Group by position
    position_groups = defaultdict(list)
    for p in available:
        position_groups[p.position].append(p)

    # Sort each group by form
    for group in position_groups.values():
        group.sort(key=lambda p: p.recent_form(), reverse=True)

    team1, team2 = [], []
    score1, score2 = 0, 0
    used_ids = set()

    # Step 1: Fill each team with required roles
    for pos, quota in POSITION_QUOTA.items():
        for _ in range(quota):
            for team, score in [(team1, score1), (team2, score2)]:
                # Try primary position first
                primary_candidates = [p for p in position_groups.get(pos, []) if p.id not in used_ids]
                if primary_candidates:
                    player = primary_candidates.pop(0)
                else:
                    # No player in this position → fallback logic
                    fallback_candidates = [p for p in available if p.id not in used_ids]
                    player = get_best_fallback_player(pos, fallback_candidates)

                if player:
                    team.append(player)
                    used_ids.add(player.id)
                    if team is team1:
                        score1 += player.recent_form()
                    else:
                        score2 += player.recent_form()

    # Step 2: Fill remaining spots
    remaining = [p for p in available if p.id not in used_ids]
    remaining.sort(key=lambda p: p.recent_form(), reverse=True)

    for p in remaining:
        if len(team1) < TEAM_SIZE and (score1 <= score2 or len(team2) >= TEAM_SIZE):
            team1.append(p)
            score1 += p.recent_form()
            used_ids.add(p.id)
        elif len(team2) < TEAM_SIZE:
            team2.append(p)
            score2 += p.recent_form()
            used_ids.add(p.id)

        if len(team1) >= TEAM_SIZE and len(team2) >= TEAM_SIZE:
            break

    return team1, team2
