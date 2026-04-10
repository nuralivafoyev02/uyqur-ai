from __future__ import annotations

from datetime import timedelta

from app.models.enums import ActorType, TicketEventType, TicketStatus
from app.repositories.stats_repository import StatsRepository
from app.services.audit_service import AuditService
from app.services.knowledge_service import KnowledgeService
from app.services.setting_service import SettingService
from app.services.telegram_service import TelegramService
from app.services.ticket_service import TicketService
from app.utils.time import isoformat, utc_now


class AutoReplyService:
    def __init__(
        self,
        settings_service: SettingService,
        stats_repository: StatsRepository,
        knowledge_service: KnowledgeService,
        ticket_service: TicketService,
        telegram_service: TelegramService,
        audit_service: AuditService,
    ):
        self.settings_service = settings_service
        self.stats_repository = stats_repository
        self.knowledge_service = knowledge_service
        self.ticket_service = ticket_service
        self.telegram_service = telegram_service
        self.audit_service = audit_service

    async def run_due_auto_replies(self) -> dict:
        runtime = await self.settings_service.get_runtime_settings()
        if not runtime.get("auto_reply_enabled", True):
            return {"processed": 0, "low_confidence": 0}
        cutoff = utc_now().replace(second=0, microsecond=0)
        cutoff = cutoff - timedelta(minutes=int(runtime.get("auto_reply_delay_minutes", 5)))
        stale = await self.stats_repository.stale_tickets(cutoff)
        processed = 0
        low_confidence = 0
        for row in stale:
            match = await self.knowledge_service.match_message(
                row.get("latest_message_text", ""),
                language=str(runtime.get("default_language", "uz")),
                default_threshold=float(runtime.get("auto_reply_confidence_threshold", 0.62)),
                variables={
                    "customer_name": row.get("customer_name", ""),
                    "group_title": row.get("group_title", ""),
                },
            )
            reply = await self.telegram_service.send_message(
                chat_id=int(row["group_chat_id"]),
                text=match.answer_text,
                reply_to_message_id=row.get("latest_message_id"),
                thread_id=row.get("topic_id"),
            )
            await self.ticket_service.ticket_repository.update_ticket(
                row["ticket_id"],
                {
                    "status": TicketStatus.AUTO_REPLIED.value,
                    "auto_replied_at": isoformat(utc_now()),
                    "auto_reply_confidence": match.confidence,
                },
            )
            await self.ticket_service._create_ticket_message(
                ticket_id=row["ticket_id"],
                sender_type=ActorType.BOT.value,
                sender_agent_id=None,
                chat_id=int(row["group_chat_id"]),
                telegram_message_id=int(reply["message_id"]),
                user_id=None,
                username=None,
                full_name="Uyqur AI Bot",
                text=match.answer_text,
                normalized_text="",
                reply_to_message_id=row.get("latest_message_id"),
                topic_id=row.get("topic_id"),
                created_at=utc_now(),
                raw_payload=reply,
            )
            await self.ticket_service.ticket_repository.create_event(
                {
                    "ticket_id": row["ticket_id"],
                    "event_type": TicketEventType.AUTO_REPLIED.value,
                    "actor_type": ActorType.BOT.value,
                    "actor_id": None,
                    "summary": "SLA bo'yicha avtomatik javob yuborildi",
                    "metadata": {
                        "kb_entry_id": match.entry_id,
                        "confidence": match.confidence,
                        "match_reasons": match.match_reasons,
                    },
                }
            )
            await self.ticket_service.ticket_repository.insert(
                "auto_reply_logs",
                {
                    "ticket_id": row["ticket_id"],
                    "kb_entry_id": match.entry_id,
                    "confidence": match.confidence,
                    "response_text": match.answer_text,
                    "fallback_used": bool(match.requires_escalation),
                    "match_reasons": match.match_reasons,
                },
            )
            processed += 1
            if match.requires_escalation:
                low_confidence += 1
        return {"processed": processed, "low_confidence": low_confidence}

    async def simulate(self, text: str) -> dict:
        runtime = await self.settings_service.get_runtime_settings()
        return await self.knowledge_service.preview_match(
            text,
            language=str(runtime.get("default_language", "uz")),
            default_threshold=float(runtime.get("auto_reply_confidence_threshold", 0.62)),
        )
