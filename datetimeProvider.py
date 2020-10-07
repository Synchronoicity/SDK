import datetime
import rfc3339
import iso8601


def get_current_time() -> datetime.datetime:
    return datetime.datetime.utcnow()


def hours_in_future(hours) -> datetime.datetime:
    return get_current_time() + datetime.timedelta(hours=hours)


def to_rfc3339_string(datetimeObj: datetime.datetime) -> str:
    return rfc3339.rfc3339(datetimeObj, utc=True, use_system_timezone=False)


def from_rfc3339_string(rfc3339String: str) -> datetime.datetime:
    return iso8601.parse_date(rfc3339String)
