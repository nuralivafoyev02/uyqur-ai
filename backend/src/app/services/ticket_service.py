from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.models.enums import ActorType, TicketEventType, TicketStatus
from app.repositories.customer_repository import CustomerRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.audit_service import AuditService
from app.utils.text import normalize_text
from app.utils.time import isoformat, parse_datetime, utc_now


class TicketService:
    def __init__(
        self,
        ticket_repository: TicketRepository,
        message_repository: MessageRepository,
        customer_repository: CustomerRepository,
        audit_service: AuditService,
    ):
        self.ticket_repository = ticket_repository
        self.message_repository = message_repository
        self.customer_repository = customer_repository
        self.audit_service = audit_service

    async def _create_ticket_message(
        self,
        *,
        ticket_id: str,
        sender_type: str,
        sender_agent_id: str | None,
        chat_id: int,
        telegram_message_id: int,
        user_id: int | None,
        username: str | None,
        full_name: str,
        text: str,
        normalized_text: str,
        reply_to_message_id: int | None,
        topic_id: int | None,
        created_at,
        raw_payload: dict[str, Any],
    ) -> dict | None:
        return await self.message_repository.create_message(
            {
                "ticket_id": ticket_id,
                "chat_id": chat_id,
                "telegram_message_id": telegram_message_id,
                "sender_type": sender_type,
                "sender_agent_id": sender_agent_id,
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "text_content": text,
                "normalized_text": normalized_text,
                "message_type": "text",
                "reply_to_message_id": reply_to_message_id,
                "topic_id": topic_id,
                "created_at": isoformat(created_at),
                "raw_payload": raw_payload,
            }
        )

    async def ingest_customer_message(self, group: dict, ctx, runtime_settings: dict[str, object]) -> dict:
        customer = await self.customer_repository.upsert_customer(
            telegram_user_id=ctx.identity.telegram_user_id or 0,
            username=ctx.identity.username,
            full_name=ctx.identity.full_name,
            language=str(runtime_settings.get("default_language", "uz")),
        )
        latest = await self.ticket_repository.get_latest_customer_ticket(
            group_id=group["id"],
            customer_id=customer["id"],
            topic_id=ctx.thread_id,
        )
        merge_window = timedelta(minutes=int(runtime_settings.get("response_merge_window_minutes", 30)))
        reopen_window = timedelta(minutes=int(runtime_settings.get("reopen_window_minutes", 60)))

        action = "created"
        if latest:
            latest_customer_at = parse_datetime(latest.get("last_customer_message_at")) or parse_datetime(
                latest.get("created_at")
            )
            closed_at = parse_datetime(latest.get("closed_at"))
            if latest["status"] != TicketStatus.CLOSED.value and latest_customer_at and (
                ctx.created_at - latest_customer_at
            ) <= merge_window:
                action = "appended"
                ticket = await self.ticket_repository.update_ticket(
                    latest["id"],
                    {
                        "status": TicketStatus.OPEN.value,
                        "last_customer_message_at": isoformat(ctx.created_at),
                        "latest_customer_message_id": ctx.message_id,
                        "latest_customer_message_text": ctx.text,
                    },
                )
            elif latest["status"] == TicketStatus.CLOSED.value and closed_at and (
                ctx.created_at - closed_at
            ) <= reopen_window:
                action = "reopened"
                ticket = await self.ticket_repository.update_ticket(
                    latest["id"],
                    {
                        "status": TicketStatus.REOPENED.value,
                        "closed_at": None,
                        "closed_reason": None,
                        "closed_by_agent_id": None,
                        "last_customer_message_at": isoformat(ctx.created_at),
                        "latest_customer_message_id": ctx.message_id,
                        "latest_customer_message_text": ctx.text,
                        "reopened_count": int(latest.get("reopened_count", 0)) + 1,
                    },
                )
                await self.ticket_repository.create_event(
                    {
                        "ticket_id": latest["id"],
                        "event_type": TicketEventType.REOPENED.value,
                        "actor_type": ActorType.CUSTOMER.value,
                        "actor_id": str(customer["id"]),
                        "summary": "Mijoz qayta yozdi va ticket qayta ochildi",
                        "metadata": {"message_id": ctx.message_id},
                    }
                )
            else:
                latest = None
        if not latest:
            ticket = await self.ticket_repository.create_ticket(
                {
                    "group_id": group["id"],
                    "topic_id": ctx.thread_id,
                    "customer_id": customer["id"],
                    "status": TicketStatus.OPEN.value,
                    "source_message_id": ctx.message_id,
                    "source_chat_id": ctx.chat_id,
                    "source_message_at": isoformat(ctx.created_at),
                    "last_customer_message_at": isoformat(ctx.created_at),
                    "latest_customer_message_id": ctx.message_id,
                    "latest_customer_message_text": ctx.text,
                }
            )
            await self.ticket_repository.create_event(
                {
                    "ticket_id": ticket["id"],
                    "event_type": TicketEventType.CREATED.value,
                    "actor_type": ActorType.CUSTOMER.value,
                    "actor_id": str(customer["id"]),
                    "summary": "Yangi ticket yaratildi",
                    "metadata": {"message_id": ctx.message_id, "chat_id": ctx.chat_id},
                }
            )
        else:
            await self.ticket_repository.create_event(
                {
                    "ticket_id": ticket["id"],
                    "event_type": TicketEventType.CUSTOMER_MESSAGE.value,
                    "actor_type": ActorType.CUSTOMER.value,
                    "actor_id": str(customer["id"]),
                    "summary": "Mijoz xabari ticketga qo'shildi",
                    "metadata": {"message_id": ctx.message_id, "action": action},
                }
            )
        await self._create_ticket_message(
            ticket_id=ticket["id"],
            sender_type=ActorType.CUSTOMER.value,
            sender_agent_id=None,
            chat_id=ctx.chat_id,
            telegram_message_id=ctx.message_id,
            user_id=ctx.identity.telegram_user_id,
            username=ctx.identity.username,
            full_name=ctx.identity.full_name,
            text=ctx.text,
            normalized_text=ctx.normalized_text,
            reply_to_message_id=ctx.reply_to_message_id,
            topic_id=ctx.thread_id,
            created_at=ctx.created_at,
            raw_payload=ctx.raw_message,
        )
        return ticket

    async def ingest_agent_message(self, group: dict, agent: dict, ctx) -> dict | None:
        if ctx.reply_to_message_id is None:
            return None
        replied = await self.message_repository.get_by_chat_message(ctx.chat_id, ctx.reply_to_message_id)
        if not replied:
            return None
        ticket = await self.ticket_repository.get_ticket(replied["ticket_id"])
        if not ticket:
            return None
        await self._create_ticket_message(
            ticket_id=ticket["id"],
            sender_type=ActorType.AGENT.value,
            sender_agent_id=agent["id"],
            chat_id=ctx.chat_id,
            telegram_message_id=ctx.message_id,
            user_id=ctx.identity.telegram_user_id,
            username=ctx.identity.username,
            full_name=ctx.identity.full_name,
            text=ctx.text,
            normalized_text=ctx.normalized_text,
            reply_to_message_id=ctx.reply_to_message_id,
            topic_id=ctx.thread_id,
            created_at=ctx.created_at,
            raw_payload=ctx.raw_message,
        )
        if replied["sender_type"] != ActorType.CUSTOMER.value:
            return ticket
        first_response_at = parse_datetime(ticket.get("first_response_at")) or ctx.created_at
        first_response_seconds = ticket.get("first_response_seconds") or int(
            (ctx.created_at - parse_datetime(ticket["created_at"])).total_seconds()
        )
        updated = await self.ticket_repository.update_ticket(
            ticket["id"],
            {
                "status": TicketStatus.CLOSED.value,
                "first_response_at": isoformat(first_response_at),
                "first_response_seconds": first_response_seconds,
                "closed_at": isoformat(ctx.created_at),
                "closed_reason": "agent_reply",
                "closed_by_agent_id": agent["id"],
                "last_agent_reply_at": isoformat(ctx.created_at),
            },
        )
        await self.ticket_repository.create_event(
            {
                "ticket_id": ticket["id"],
                "event_type": TicketEventType.AGENT_REPLIED.value,
                "actor_type": ActorType.AGENT.value,
                "actor_id": agent["id"],
                "summary": "Agent reply orqali ticket yopildi",
                "metadata": {"message_id": ctx.message_id, "reply_to_message_id": ctx.reply_to_message_id},
            }
        )
        return updated

    async def list_tickets(self, filters: dict[str, Any]) -> list[dict]:
        query_filters: dict[str, str] = {}
        if filters.get("group_id"):
            query_filters["group_id"] = f"eq.{filters['group_id']}"
        if filters.get("status"):
            query_filters["status"] = f"eq.{filters['status']}"
        elif not filters.get("include_closed", True):
            query_filters["status"] = "in.(open,reopened,auto_replied)"
        if filters.get("from_date"):
            query_filters["created_at"] = f"gte.{isoformat(filters['from_date'])}"
        if filters.get("to_date"):
            query_filters["updated_at"] = f"lte.{isoformat(filters['to_date'])}"
        if filters.get("search"):
            query_filters["or"] = (
                f"(latest_customer_message_text.ilike.*{normalize_text(filters['search'])}*,"
                f"id.eq.{filters['search']})"
            )
        rows = await self.ticket_repository.list_tickets(filters=query_filters)
        return rows

    async def get_ticket_detail(self, ticket_id: str) -> dict | None:
        ticket = await self.ticket_repository.get_ticket(ticket_id)
        if not ticket:
            return None
        ticket["messages"] = await self.message_repository.list_by_ticket(ticket_id)
        ticket["group_title"] = ticket.get("telegram_groups", {}).get("title")
        ticket["customer_name"] = ticket.get("customers", {}).get("full_name")
        ticket["customer_username"] = ticket.get("customers", {}).get("username")
        return ticket

    async def update_status(self, ticket_id: str, status: str, note: str | None, actor_id: str) -> dict:
        payload: dict[str, Any] = {"status": status}
        if status == TicketStatus.CLOSED.value:
            payload["closed_at"] = isoformat(utc_now())
            payload["closed_reason"] = "manual_status_change"
        if status == TicketStatus.REOPENED.value:
            payload.update({"closed_at": None, "closed_reason": None, "closed_by_agent_id": None})
        ticket = await self.ticket_repository.update_ticket(ticket_id, payload)
        await self.ticket_repository.create_event(
            {
                "ticket_id": ticket_id,
                "event_type": TicketEventType.STATUS_CHANGED.value,
                "actor_type": ActorType.AGENT.value,
                "actor_id": actor_id,
                "summary": "Ticket statusi admin tomonidan o'zgartirildi",
                "metadata": {"status": status, "note": note},
            }
        )
        return ticket

    async def reopen_ticket(self, ticket_id: str, actor_id: str) -> dict:
        return await self.update_status(ticket_id, TicketStatus.REOPENED.value, "Manual reopen", actor_id)

    async def manual_reply_log(self, ticket_id: str, agent_id: str, replied_at, note: str | None) -> dict:
        ticket = await self.ticket_repository.get_ticket(ticket_id)
        first_response_at = parse_datetime(ticket.get("first_response_at")) or replied_at
        first_response_seconds = ticket.get("first_response_seconds") or int(
            (replied_at - parse_datetime(ticket["created_at"])).total_seconds()
        )
        updated = await self.ticket_repository.update_ticket(
            ticket_id,
            {
                "status": TicketStatus.CLOSED.value,
                "first_response_at": isoformat(first_response_at),
                "first_response_seconds": first_response_seconds,
                "closed_at": isoformat(replied_at),
                "closed_reason": "manual_reply_log",
                "closed_by_agent_id": agent_id,
                "last_agent_reply_at": isoformat(replied_at),
            },
        )
        await self.ticket_repository.create_event(
            {
                "ticket_id": ticket_id,
                "event_type": TicketEventType.MANUAL_REPLY_LOGGED.value,
                "actor_type": ActorType.AGENT.value,
                "actor_id": agent_id,
                "summary": "Manual reply log yozildi",
                "metadata": {"note": note, "replied_at": isoformat(replied_at)},
            }
        )
        return updated

    async def open_ticket_summaries(self, limit: int = 10) -> list[dict]:
        rows = await self.ticket_repository.list_tickets(
            filters={"status": "in.(open,reopened,auto_replied)"},
            limit=limit,
        )
        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "group_title": row.get("telegram_groups", {}).get("title"),
                    "customer_name": row.get("customers", {}).get("full_name"),
                    "status": row["status"],
                    "created_at": row["created_at"],
                }
            )
        return result
