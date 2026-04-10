from __future__ import annotations

from datetime import datetime


def require_not_blank(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} bo'sh bo'lishi mumkin emas")
    return cleaned


def coerce_optional_int(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def coerce_date_range(start: datetime | None, end: datetime | None) -> tuple[datetime | None, datetime | None]:
    if start and end and start > end:
        raise ValueError("Boshlanish sanasi tugash sanasidan keyin bo'lishi mumkin emas")
    return start, end
