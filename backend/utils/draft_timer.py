from datetime import datetime, timedelta

def get_draft_window():
    """Returns the start and end datetime objects for the draft window."""
    today = datetime.today()

    # Find the most recent Tuesday (weekday 1)
    days_since_tuesday = (today.weekday() - 1) % 7
    start = today - timedelta(days=days_since_tuesday)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Draft ends Saturday 23:59
    end = start + timedelta(days=4, hours=23, minutes=59)

    return start, end

def is_draft_window_open():
    """Check if current time is within the draft window."""
    start, end = get_draft_window()
    now = datetime.now()
    return start <= now <= end
