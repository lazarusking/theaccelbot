from datetime import datetime, timezone


def format_time_left(scheduled_time: datetime):
    time_left = scheduled_time - datetime.now(timezone.utc)
    days, seconds = time_left.days, time_left.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    time_message = ""
    if hours > 0:
        time_message += f"{hours} hours "
    if minutes > 0 or hours > 0:
        time_message += f"{minutes} minutes "
    time_message += f"{seconds} seconds"

    return time_message
