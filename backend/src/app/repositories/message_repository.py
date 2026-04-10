from __future__ import annotations

from app.repositories.base import SupabaseRepository


class MessageRepository(SupabaseRepository):
    async def create_message(self, payload: dict) -> dict | None:
        result = await self.insert(
            "ticket_messages",
            [payload],
            upsert=True,
            on_conflict="chat_id,telegram_message_id",
        )
        return result[0] if result else None

    async def get_by_chat_message(self, chat_id: int, message_id: int) -> dict | None:
        return await self.select(
            "ticket_messages",
            filters={
                "chat_id": f"eq.{chat_id}",
                "telegram_message_id": f"eq.{message_id}",
            },
            single=True,
        )

    async def list_by_ticket(self, ticket_id: str) -> list[dict]:
        return await self.select(
            "ticket_messages",
            filters={"ticket_id": f"eq.{ticket_id}"},
            order="created_at.asc",
        )
