from __future__ import annotations

from app.repositories.base import SupabaseRepository


class SettingRepository(SupabaseRepository):
    async def get_all(self) -> dict[str, object]:
        rows = await self.select("bot_settings", order="key.asc")
        return {row["key"]: row["value_json"] for row in rows}

    async def set_values(self, values: dict[str, object], admin_user_id: str | None = None) -> list[dict]:
        payload = [
            {
                "key": key,
                "value_json": value,
                "updated_by_admin_user_id": admin_user_id,
            }
            for key, value in values.items()
        ]
        if not payload:
            return []
        return await self.insert(
            "bot_settings",
            payload,
            upsert=True,
            on_conflict="key",
        )
