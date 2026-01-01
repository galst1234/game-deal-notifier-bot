import datetime


def get_next_time(time: datetime.time) -> datetime.datetime:
    """
    Get the next occurrence of the given time.
    """
    now = datetime.datetime.now(tz=datetime.UTC)
    next_time = datetime.datetime.combine(now.date(), time, tzinfo=datetime.UTC)
    if now.time() > time:
        next_time += datetime.timedelta(days=1)
    return next_time
