from __future__ import annotations

from app.repositories.base import SupabaseRepository


class TicketRepository(SupabaseRepository):
    async def get_ticket(self, ticket_id: str) -> dict | None:
        return await self.select(
            "tickets",
            select="*,telegram_groups(title,chat_id),customers(full_name,username)",
            filters={"id": f"eq.{ticket_id}"},
            single=True,
        )

    async def get_latest_customer_ticket(
        self,
        *,
        group_id: str,
        customer_id: str,
        topic_id: int | None,
    ) -> dict | None:
        filters = {
            "group_id": f"eq.{group_id}",
            "customer_id": f"eq.{customer_id}",
        }
        filters["topic_id"] = "is.null" if topic_id is None else f"eq.{topic_id}"
        rows = await self.select("tickets", filters=filters, order="created_at.desc", limit=1)
        return rows[0] if rows else None

    async def create_ticket(self, payload: dict) -> dict:
        result = await self.insert("tickets", payload)
        return result[0]

    async def update_ticket(self, ticket_id: str, payload: dict) -> dict:
        result = await self.update("tickets", payload, filters={"id": f"eq.{ticket_id}"})
        return result[0]

    async def list_tickets(
        self,
        *,
        filters: dict[str, str] | None = None,
        order: str = "created_at.desc",
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        return await self.select(
            "tickets",
            select="*,telegram_groups(title,chat_id),customers(full_name,username)",
            filters=filters,
            order=order,
            limit=limit,
            offset=offset,
        )

    async def create_event(self, payload: dict) -> dict:
        result = await self.insert("ticket_events", payload)
        return result[0]
