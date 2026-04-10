from __future__ import annotations

from app.models.enums import GroupType
from app.repositories.base import SupabaseRepository
from app.utils.time import isoformat, utc_now


class GroupRepository(SupabaseRepository):
    async def list_groups(self) -> list[dict]:
        return await self.select("telegram_groups", order="updated_at.desc")

    async def get_group(self, group_id: str) -> dict | None:
        return await self.select(
            "telegram_groups",
            filters={"id": f"eq.{group_id}"},
            single=True,
        )

    async def get_by_chat_id(self, chat_id: int) -> dict | None:
        return await self.select(
            "telegram_groups",
            filters={"chat_id": f"eq.{chat_id}"},
            single=True,
        )

    async def upsert_group(
        self,
        *,
        chat_id: int,
        title: str,
        username: str | None,
        group_type: GroupType,
        is_forum: bool,
        is_active: bool = True,
    ) -> dict:
        payload = [
            {
                "chat_id": chat_id,
                "title": title,
                "username": username,
                "group_type": group_type.value,
                "is_forum": is_forum,
                "is_active": is_active,
                "last_seen_at": isoformat(utc_now()),
            }
        ]
        result = await self.insert(
            "telegram_groups",
            payload,
            upsert=True,
            on_conflict="chat_id",
        )
        return result[0]

    async def update_group(self, group_id: str, payload: dict) -> dict:
        result = await self.update(
            "telegram_groups",
            payload,
            filters={"id": f"eq.{group_id}"},
        )
        return result[0]
