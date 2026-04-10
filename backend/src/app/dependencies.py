from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings
from app.repositories.admin_repository import AdminRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.kb_repository import KBRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.stats_repository import StatsRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.agent_service import AgentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.auto_reply_service import AutoReplyService
from app.services.group_service import GroupService
from app.services.knowledge_service import KnowledgeService
from app.services.management_service import ManagementService
from app.services.scheduler_service import SchedulerService
from app.services.setting_service import SettingService
from app.services.stats_service import StatsService
from app.services.telegram_service import TelegramService
from app.services.ticket_service import TicketService
from bot import BotOrchestrator


@dataclass
class AppContainer:
    settings: Settings
    group_repository: GroupRepository
    audit_repository: AuditRepository
    agent_service: AgentService
    audit_service: AuditService
    auth_service: AuthService
    knowledge_service: KnowledgeService
    ticket_service: TicketService
    stats_service: StatsService
    telegram_service: TelegramService
    setting_service: SettingService
    group_service: GroupService
    management_service: ManagementService
    auto_reply_service: AutoReplyService
    scheduler_service: SchedulerService
    bot: BotOrchestrator


def build_container(env_source: Any | None = None) -> AppContainer:
    settings = Settings.from_env(env_source)
    group_repository = GroupRepository(settings)
    ticket_repository = TicketRepository(settings)
    message_repository = MessageRepository(settings)
    customer_repository = CustomerRepository(settings)
    stats_repository = StatsRepository(settings)
    admin_repository = AdminRepository(settings)
    audit_repository = AuditRepository(settings)
    agent_repository = AgentRepository(settings)
    setting_repository = SettingRepository(settings)
    kb_repository = KBRepository(settings)

    audit_service = AuditService(audit_repository)
    stats_service = StatsService(stats_repository)
    setting_service = SettingService(setting_repository, settings)
    telegram_service = TelegramService(settings)
    auth_service = AuthService(admin_repository, settings, audit_service)
    ticket_service = TicketService(ticket_repository, message_repository, customer_repository, audit_service)
    knowledge_service = KnowledgeService(kb_repository, settings.safe_fallback_message)
    agent_service = AgentService(agent_repository, stats_repository, audit_service)
    group_service = GroupService(group_repository, stats_service, audit_service)
    management_service = ManagementService(
        setting_service,
        stats_service,
        telegram_service,
        audit_repository,
    )
    auto_reply_service = AutoReplyService(
        setting_service,
        stats_repository,
        knowledge_service,
        ticket_service,
        telegram_service,
        audit_service,
    )
    scheduler_service = SchedulerService(auto_reply_service, management_service, auth_service)
    bot = BotOrchestrator(
        settings=settings,
        group_repository=group_repository,
        setting_service=setting_service,
        agent_service=agent_service,
        ticket_service=ticket_service,
        stats_service=stats_service,
        telegram_service=telegram_service,
        audit_service=audit_service,
    )
    return AppContainer(
        settings=settings,
        group_repository=group_repository,
        audit_repository=audit_repository,
        agent_service=agent_service,
        audit_service=audit_service,
        auth_service=auth_service,
        knowledge_service=knowledge_service,
        ticket_service=ticket_service,
        stats_service=stats_service,
        telegram_service=telegram_service,
        setting_service=setting_service,
        group_service=group_service,
        management_service=management_service,
        auto_reply_service=auto_reply_service,
        scheduler_service=scheduler_service,
        bot=bot,
    )


async def get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def get_current_session(
    request: Request,
    container: AppContainer = Depends(get_container),
) -> dict:
    raw_token = request.cookies.get(container.settings.session_cookie_name)
    session = await container.auth_service.get_session(raw_token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessiya topilmadi")
    if session["admin_users"]["must_change_password"] and request.url.path not in {
        "/api/admin/auth/change-password",
        "/api/admin/auth/logout",
        "/api/admin/auth/me",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Avval parolni almashtiring",
        )
    return session


async def get_current_admin_user(session: dict = Depends(get_current_session)) -> dict:
    return session["admin_users"]
