from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.repositories.stats_repository import StatsRepository
from app.utils.time import floor_to_hour, start_of_day, start_of_week, to_tz, utc_now


class StatsService:
    def __init__(self, repository: StatsRepository):
        self.repository = repository

    @staticmethod
    def resolve_window(label: str, tz_name: str) -> tuple[datetime, datetime]:
        now = utc_now()
        if label == "today":
            return start_of_day(now, tz_name), now
        if label == "yesterday":
            end = start_of_day(now, tz_name)
            return end - timedelta(days=1), end
        if label in {"week", "this_week"}:
            return start_of_week(now, tz_name), now
        if label in {"month", "this_month"}:
            local = to_tz(now, tz_name)
            start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start.astimezone(timezone.utc), now
        raise ValueError(f"Qo'llab-quvvatlanmaydigan davr: {label}")

    async def overview(self, from_at: datetime, to_at: datetime) -> dict:
        return await self.repository.overview(from_at, to_at)

    async def group_stats(self, from_at: datetime, to_at: datetime) -> list[dict]:
        return await self.repository.groups(from_at, to_at)

    async def agent_stats(self, from_at: datetime, to_at: datetime) -> list[dict]:
        return await self.repository.agents(from_at, to_at)

    async def timeline(self, from_at: datetime, to_at: datetime, bucket: str = "day") -> list[dict]:
        return await self.repository.timeline(from_at, to_at, bucket)

    async def management_summary_payload(self, from_at: datetime, to_at: datetime) -> dict:
        return await self.repository.management_summary(from_at, to_at)

    @staticmethod
    def format_duration(seconds: float | int | None) -> str:
        if seconds is None:
            return "-"
        total = int(seconds)
        minutes, sec = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours} soat {minutes} daqiqa"
        if minutes:
            return f"{minutes} daqiqa {sec} soniya"
        return f"{sec} soniya"

    def render_overview_text(self, label: str, payload: dict) -> str:
        return (
            f"{label}\n"
            f"Jami murojaatlar: {payload.get('total_requests', 0)}\n"
            f"Ochiq: {payload.get('open_requests', 0)}\n"
            f"Yopilgan: {payload.get('closed_requests', 0)}\n"
            f"Javob olingan: {payload.get('answered_requests', 0)}\n"
            f"Javobsiz: {payload.get('unanswered_requests', 0)}\n"
            f"Avto-javob: {payload.get('auto_replied_requests', 0)}\n"
            f"Javob berish foizi: {payload.get('response_rate', 0)}%\n"
            f"O'rtacha ilk javob vaqti: {self.format_duration(payload.get('average_first_response_seconds'))}"
        )

    def render_group_stats_text(self, rows: list[dict]) -> str:
        if not rows:
            return "Hozircha guruh statistikasi mavjud emas."
        lines = ["Guruhlar kesimida statistikalar:"]
        for row in rows[:10]:
            lines.append(
                f"- {row['title']}: jami {row['total_requests']}, ochiq {row['open_requests']}, "
                f"yopilgan {row['closed_requests']}, javob foizi {row['response_rate']}%"
            )
        return "\n".join(lines)

    def render_agent_stats_text(self, rows: list[dict]) -> str:
        if not rows:
            return "Hozircha agent statistikasi mavjud emas."
        lines = ["Agentlar kesimida:"]
        for row in rows[:10]:
            lines.append(
                f"- {row['display_name']}: {row['handled_tickets']} ta ticket, "
                f"o'rtacha ilk javob {self.format_duration(row.get('avg_first_response_seconds'))}"
            )
        return "\n".join(lines)

    def render_open_tickets_text(self, tickets: list[dict]) -> str:
        if not tickets:
            return "Ochiq murojaatlar yo'q."
        lines = ["Ochiq murojaatlar:"]
        for ticket in tickets[:10]:
            lines.append(
                f"- {ticket.get('group_title', 'Guruh')}: {ticket.get('customer_name', 'Mijoz')} "
                f"({ticket.get('status')})"
            )
        return "\n".join(lines)

    def previous_hour_window(self) -> tuple[datetime, datetime]:
        end = floor_to_hour(utc_now())
        return end - timedelta(hours=1), end

    def previous_day_window(self, tz_name: str) -> tuple[datetime, datetime]:
        end = start_of_day(utc_now(), tz_name)
        return end - timedelta(days=1), end
