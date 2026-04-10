from __future__ import annotations

import hashlib
import inspect
from typing import Any

from app.config import Settings
from app.constants import DEFAULT_COMMAND_HELP
from app.models.enums import ActorType, AuditAction, GroupType
from app.repositories.group_repository import GroupRepository
from app.services.agent_service import AgentService
from app.services.audit_service import AuditService
from app.services.setting_service import SettingService
from app.services.stats_service import StatsService
from app.services.telegram_service import TelegramService
from app.services.ticket_service import TicketService
from app.utils.telegram import build_message_context, is_service_message


class BotOrchestrator:
    def __init__(
        self,
        *,
        settings: Settings,
        group_repository: GroupRepository,
        setting_service: SettingService,
        agent_service: AgentService,
        ticket_service: TicketService,
        stats_service: StatsService,
        telegram_service: TelegramService,
        audit_service: AuditService,
    ):
        self.settings = settings
        self.group_repository = group_repository
        self.setting_service = setting_service
        self.agent_service = agent_service
        self.ticket_service = ticket_service
        self.stats_service = stats_service
        self.telegram_service = telegram_service
        self.audit_service = audit_service

    async def process_update(self, update: dict[str, Any], claim_processed) -> dict[str, Any]:
        update_id = int(update.get("update_id", 0))
        update_hash = hashlib.sha256(repr(update).encode("utf-8")).hexdigest()
        claim_result = claim_processed(update_id, update_hash) if update_id else True
        if inspect.isawaitable(claim_result):
            claim_result = await claim_result
        if update_id and not claim_result:
            return {"status": "duplicate", "update_id": update_id}

        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"status": "ignored", "reason": "unsupported_update", "update_id": update_id}
        if is_service_message(message):
            return {"status": "ignored", "reason": "service_message", "update_id": update_id}

        ctx = build_message_context(update_id, message)
        if ctx.identity.is_bot:
            return {"status": "ignored", "reason": "bot_message", "update_id": update_id}

        runtime = await self.setting_service.get_runtime_settings()
        agent = await self.agent_service.find_agent(
            username=ctx.identity.username,
            chat_id=ctx.identity.telegram_user_id,
        )

        if ctx.chat_type == "private":
            return await self._handle_private_chat(ctx, agent)

        existing_group = await self.group_repository.get_by_chat_id(ctx.chat_id)
        group_type = (
            GroupType.MANAGEMENT
            if int(runtime.get("management_group_chat_id") or 0) == ctx.chat_id
            else GroupType(existing_group["group_type"]) if existing_group else GroupType.SUPPORT
        )
        group = await self.group_repository.upsert_group(
            chat_id=ctx.chat_id,
            title=ctx.chat_title,
            username=ctx.raw_message["chat"].get("username"),
            group_type=group_type,
            is_forum=bool(ctx.raw_message["chat"].get("is_forum", False)),
        )

        if group_type == GroupType.MANAGEMENT:
            return await self._handle_management_chat(ctx, agent)

        if ctx.is_command:
            return {"status": "ignored", "reason": "support_group_command"}

        if agent:
            ticket = await self.ticket_service.ingest_agent_message(group, agent, ctx)
            if ticket:
                return {"status": "agent_reply", "ticket_id": ticket["id"], "group_id": group["id"]}
            return {"status": "ignored", "reason": "agent_non_reply"}

        ticket = await self.ticket_service.ingest_customer_message(group, ctx, runtime)
        return {"status": "ticket_recorded", "ticket_id": ticket["id"], "group_id": group["id"]}

    async def _handle_private_chat(self, ctx, agent: dict | None) -> dict[str, Any]:
        if ctx.command == "/registerme":
            registered = await self.agent_service.register_private_chat(ctx.identity.username, ctx.chat_id)
            text = (
                "Chat profilingiz agentga biriktirildi. Endi boshqaruv buyruqlaridan foydalana olasiz."
                if registered
                else "Siz hali agent sifatida ro'yxatdan o'tmagansiz. Admin paneldan oldin biriktirish kerak."
            )
            await self.telegram_service.send_message(chat_id=ctx.chat_id, text=text)
            await self.audit_service.log_command(
                chat_id=ctx.chat_id,
                telegram_user_id=ctx.identity.telegram_user_id,
                command=ctx.command or "",
                args=ctx.command_args,
                was_authorized=bool(registered),
                response_summary=text,
            )
            return {"status": "registered" if registered else "registration_failed"}
        if ctx.is_command:
            return await self._dispatch_privileged_command(ctx, agent)
        return {"status": "ignored", "reason": "private_non_command"}

    async def _handle_management_chat(self, ctx, agent: dict | None) -> dict[str, Any]:
        if not ctx.is_command:
            return {"status": "ignored", "reason": "management_non_command"}
        return await self._dispatch_privileged_command(ctx, agent)

    async def _dispatch_privileged_command(self, ctx, agent: dict | None) -> dict[str, Any]:
        authorized = self.agent_service.is_privileged(agent)
        if ctx.command == "/help":
            text = DEFAULT_COMMAND_HELP
            await self.telegram_service.send_message(chat_id=ctx.chat_id, text=text, thread_id=ctx.thread_id)
            await self.audit_service.log_command(
                chat_id=ctx.chat_id,
                telegram_user_id=ctx.identity.telegram_user_id,
                command=ctx.command or "",
                args=ctx.command_args,
                was_authorized=authorized,
                response_summary="help",
            )
            return {"status": "help_sent", "authorized": authorized}
        if not authorized:
            text = "Sizda bu buyruqni ishlatish uchun ruxsat yo'q."
            await self.telegram_service.send_message(chat_id=ctx.chat_id, text=text, thread_id=ctx.thread_id)
            await self.audit_service.log_command(
                chat_id=ctx.chat_id,
                telegram_user_id=ctx.identity.telegram_user_id,
                command=ctx.command or "",
                args=ctx.command_args,
                was_authorized=False,
                response_summary="forbidden",
            )
            return {"status": "forbidden"}

        runtime = await self.setting_service.get_runtime_settings()
        timezone = str(runtime.get("timezone", "Asia/Tashkent"))
        if ctx.command in {"/stats", "/stats_today"}:
            from_at, to_at = self.stats_service.resolve_window("today", timezone)
            payload = await self.stats_service.overview(from_at, to_at)
            text = self.stats_service.render_overview_text("Bugungi statistika", payload)
        elif ctx.command == "/stats_week":
            from_at, to_at = self.stats_service.resolve_window("week", timezone)
            payload = await self.stats_service.overview(from_at, to_at)
            text = self.stats_service.render_overview_text("Haftalik statistika", payload)
        elif ctx.command == "/groupstats":
            from_at, to_at = self.stats_service.resolve_window("today", timezone)
            text = self.stats_service.render_group_stats_text(await self.stats_service.group_stats(from_at, to_at))
        elif ctx.command == "/agentstats":
            from_at, to_at = self.stats_service.resolve_window("today", timezone)
            text = self.stats_service.render_agent_stats_text(await self.stats_service.agent_stats(from_at, to_at))
        elif ctx.command == "/open":
            text = self.stats_service.render_open_tickets_text(
                await self.ticket_service.open_ticket_summaries(limit=10)
            )
        else:
            text = "Bu buyruq tanilmadi. /help ni yuboring."
        await self.telegram_service.send_message(chat_id=ctx.chat_id, text=text, thread_id=ctx.thread_id)
        await self.audit_service.log_command(
            chat_id=ctx.chat_id,
            telegram_user_id=ctx.identity.telegram_user_id,
            command=ctx.command or "",
            args=ctx.command_args,
            was_authorized=True,
            response_summary=text[:120],
        )
        await self.audit_service.log(
            actor_type=ActorType.AGENT if agent else ActorType.SYSTEM,
            actor_id=agent["id"] if agent else None,
            action=AuditAction.BOT_COMMAND.value,
            entity_type="command",
            entity_id=ctx.command,
            metadata={"chat_id": ctx.chat_id, "args": ctx.command_args},
        )
        return {"status": "command_processed", "command": ctx.command}
