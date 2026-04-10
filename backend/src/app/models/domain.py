from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.models.enums import ActorType, AgentRole, GroupType, TicketStatus


@dataclass
class TelegramIdentity:
    telegram_user_id: int | None
    username: str | None
    full_name: str
    is_bot: bool = False


@dataclass
class MessageContext:
    update_id: int
    chat_id: int
    chat_title: str
    chat_type: str
    message_id: int
    thread_id: int | None
    text: str
    normalized_text: str
    created_at: datetime
    reply_to_message_id: int | None
    identity: TelegramIdentity
    raw_message: dict[str, Any]
    is_command: bool = False
    command: str | None = None
    command_args: list[str] = field(default_factory=list)


@dataclass
class AgentMatch:
    id: str
    role: AgentRole
    telegram_chat_id: int | None
    telegram_username: str | None
    display_name: str


@dataclass
class TicketSnapshot:
    id: str
    group_id: str
    group_chat_id: int
    topic_id: int | None
    customer_id: str
    status: TicketStatus
    source_message_id: int
    source_chat_id: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    closed_by_agent_id: str | None
    first_response_at: datetime | None
    first_response_seconds: int | None
    auto_replied_at: datetime | None
    auto_reply_confidence: float | None
    last_customer_message_at: datetime
    last_agent_reply_at: datetime | None
    latest_message_text: str | None = None


@dataclass
class KBMatch:
    entry_id: str | None
    title: str | None
    answer_text: str
    confidence: float
    match_reasons: list[str]
    requires_escalation: bool


@dataclass
class SummaryWindow:
    label: str
    start_at: datetime
    end_at: datetime


@dataclass
class AuditRecord:
    actor_type: ActorType
    actor_id: str | None
    action: str
    metadata: dict[str, Any]
    occurred_at: datetime


@dataclass
class GroupRecord:
    id: str
    chat_id: int
    title: str
    username: str | None
    type: GroupType
    is_active: bool
