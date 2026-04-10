from __future__ import annotations

from app.repositories.base import SupabaseRepository
from app.utils.time import isoformat


class StatsRepository(SupabaseRepository):
    async def overview(self, from_at, to_at) -> dict:
        return await self.rpc(
            "stats_overview",
            {"p_from": isoformat(from_at), "p_to": isoformat(to_at)},
        )

    async def groups(self, from_at, to_at) -> list[dict]:
        return await self.rpc(
            "stats_groups",
            {"p_from": isoformat(from_at), "p_to": isoformat(to_at)},
        )

    async def agents(self, from_at, to_at) -> list[dict]:
        return await self.rpc(
            "stats_agents",
            {"p_from": isoformat(from_at), "p_to": isoformat(to_at)},
        )

    async def timeline(self, from_at, to_at, bucket: str) -> list[dict]:
        return await self.rpc(
            "stats_timeline",
            {"p_from": isoformat(from_at), "p_to": isoformat(to_at), "p_bucket": bucket},
        )

    async def stale_tickets(self, cutoff_at) -> list[dict]:
        return await self.rpc("stale_open_tickets", {"p_cutoff": isoformat(cutoff_at)})

    async def management_summary(self, from_at, to_at) -> dict:
        return await self.rpc(
            "management_summary",
            {"p_from": isoformat(from_at), "p_to": isoformat(to_at)},
        )
