from __future__ import annotations

from app.repositories.base import SupabaseRepository


class AgentRepository(SupabaseRepository):
    async def list_agents(self) -> list[dict]:
        return await self.select("agents", order="created_at.asc")

    async def get_agent(self, agent_id: str) -> dict | None:
        return await self.select("agents", filters={"id": f"eq.{agent_id}"}, single=True)

    async def get_by_chat_id(self, chat_id: int) -> dict | None:
        return await self.select(
            "agents",
            filters={"telegram_chat_id": f"eq.{chat_id}", "is_active": "eq.true"},
            single=True,
        )

    async def get_by_username(self, username: str) -> dict | None:
        return await self.select(
            "agents",
            filters={
                "telegram_username_normalized": f"eq.{username.lower()}",
                "is_active": "eq.true",
            },
            single=True,
        )

    async def find_agent(self, username: str | None, chat_id: int | None) -> dict | None:
        if chat_id is not None:
            by_chat = await self.get_by_chat_id(chat_id)
            if by_chat:
                return by_chat
        if username:
            return await self.get_by_username(username)
        return None

    async def create_agent(self, payload: dict) -> dict:
        result = await self.insert("agents", payload)
        return result[0]

    async def update_agent(self, agent_id: str, payload: dict) -> dict:
        result = await self.update("agents", payload, filters={"id": f"eq.{agent_id}"})
        return result[0]

    async def deactivate_agent(self, agent_id: str) -> dict:
        result = await self.update(
            "agents",
            {"is_active": False},
            filters={"id": f"eq.{agent_id}"},
        )
        return result[0]
