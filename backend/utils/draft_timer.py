from datetime import datetime, timedelta

def get_draft_window():
    now = datetime.now()
    today = now.weekday()
    days_until_tuesday = (1 - today) % 7
    tuesday = (now + timedelta(days=days_until_tuesday)).replace(hour=0, minute=0, second=0, microsecond=0)
    saturday = tuesday + timedelta(days=4, hours=23, minutes=59, seconds=59)
    return tuesday, saturday
        
