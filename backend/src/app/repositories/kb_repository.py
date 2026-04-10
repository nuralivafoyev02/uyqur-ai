from __future__ import annotations

from app.repositories.base import SupabaseRepository


class KBRepository(SupabaseRepository):
    async def list_entries(self, only_active: bool = False) -> list[dict]:
        filters = {"is_active": "eq.true"} if only_active else None
        return await self.select(
            "kb_entries",
            select="*,kb_terms(*)",
            filters=filters,
            order="priority.desc,updated_at.desc",
        )

    async def get_entry(self, entry_id: str) -> dict | None:
        return await self.select(
            "kb_entries",
            select="*,kb_terms(*)",
            filters={"id": f"eq.{entry_id}"},
            single=True,
        )

    async def create_entry(self, payload: dict) -> dict:
        result = await self.insert("kb_entries", payload)
        return result[0]

    async def update_entry(self, entry_id: str, payload: dict) -> dict:
        result = await self.update("kb_entries", payload, filters={"id": f"eq.{entry_id}"})
        return result[0]

    async def delete_entry(self, entry_id: str) -> None:
        await self.delete("kb_entries", filters={"id": f"eq.{entry_id}"})

    async def replace_terms(self, entry_id: str, terms: list[dict]) -> list[dict]:
        await self.delete("kb_terms", filters={"kb_entry_id": f"eq.{entry_id}"})
        if not terms:
            return []
        return await self.insert("kb_terms", terms)
