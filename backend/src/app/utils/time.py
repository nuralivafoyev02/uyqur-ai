from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def to_tz(value: datetime, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    return value.astimezone(tz)


def floor_to_hour(value: datetime) -> datetime:
    return value.replace(minute=0, second=0, microsecond=0)


def start_of_day(value: datetime, tz_name: str) -> datetime:
    local = to_tz(value, tz_name)
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def start_of_week(value: datetime, tz_name: str) -> datetime:
    local = to_tz(value, tz_name)
    day_start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return (day_start - timedelta(days=day_start.weekday())).astimezone(timezone.utc)


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()
