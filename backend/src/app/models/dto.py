from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import AgentRole, GroupType, TicketStatus


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class AdminUserView(BaseModel):
    id: str
    username: str
    display_name: str
    must_change_password: bool
    is_bootstrap: bool
    created_at: datetime


class SessionView(BaseModel):
    user: AdminUserView | None = None
    authenticated: bool
    must_change_password: bool = False
    expires_at: datetime | None = None


class GroupView(BaseModel):
    id: str
    chat_id: int
    title: str
    username: str | None = None
    group_type: GroupType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metrics: dict[str, Any] = Field(default_factory=dict)


class GroupUpdateRequest(BaseModel):
    title: str | None = None
    username: str | None = None
    group_type: GroupType | None = None
    is_active: bool | None = None


class TicketFilterRequest(BaseModel):
    status: TicketStatus | None = None
    group_id: str | None = None
    agent_id: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    search: str | None = None
    include_closed: bool = True


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatus
    note: str | None = Field(default=None, max_length=500)


class ManualReplyLogRequest(BaseModel):
    agent_id: str
    replied_at: datetime
    note: str | None = Field(default=None, max_length=500)


class TicketMessageView(BaseModel):
    id: str
    chat_id: int
    telegram_message_id: int
    sender_type: Literal["customer", "agent", "bot", "system"]
    user_id: int | None = None
    username: str | None = None
    full_name: str
    text: str
    normalized_text: str
    message_type: str
    reply_to_message_id: int | None = None
    created_at: datetime
    raw_payload: dict[str, Any] | None = None


class TicketView(BaseModel):
    id: str
    group_id: str
    group_title: str | None = None
    topic_id: int | None = None
    customer_id: str
    customer_name: str | None = None
    customer_username: str | None = None
    status: TicketStatus
    source_message_id: int
    source_chat_id: int
    created_at: datetime
    updated_at: datetime
    first_response_at: datetime | None = None
    first_response_seconds: int | None = None
    closed_at: datetime | None = None
    closed_by_agent_id: str | None = None
    auto_replied_at: datetime | None = None
    auto_reply_confidence: float | None = None
    last_customer_message_at: datetime
    last_agent_reply_at: datetime | None = None
    status_label: str | None = None
    messages: list[TicketMessageView] = Field(default_factory=list)


class AgentCreateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=128)
    telegram_username: str | None = Field(default=None, max_length=64)
    telegram_chat_id: int | None = None
    role: AgentRole = AgentRole.AGENT
    is_active: bool = True


class AgentUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=128)
    telegram_username: str | None = Field(default=None, max_length=64)
    telegram_chat_id: int | None = None
    role: AgentRole | None = None
    is_active: bool | None = None


class AgentView(BaseModel):
    id: str
    display_name: str
    telegram_username: str | None = None
    telegram_chat_id: int | None = None
    role: AgentRole
    is_active: bool
    handled_tickets: int = 0
    avg_first_response_seconds: float | None = None
    closure_count: int = 0
    created_at: datetime
    updated_at: datetime


class KBEntryRequest(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    language: str = Field(min_length=2, max_length=10, default="uz")
    category: str = Field(min_length=2, max_length=64)
    keywords: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    answer_template: str = Field(min_length=2, max_length=4000)
    priority: int = 10
    is_active: bool = True
    confidence_threshold_override: float | None = None


class KBTestRequest(BaseModel):
    text: str = Field(min_length=2, max_length=2000)
    language: str = Field(default="uz", min_length=2, max_length=10)


class KBEntryView(BaseModel):
    id: str
    title: str
    language: str
    category: str
    keywords: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    answer_template: str
    priority: int
    is_active: bool
    confidence_threshold_override: float | None = None
    created_at: datetime
    updated_at: datetime


class SettingsView(BaseModel):
    values: dict[str, Any]


class SettingsPatchRequest(BaseModel):
    values: dict[str, Any]


class TimelinePoint(BaseModel):
    bucket: str
    total_requests: int
    closed_requests: int
    auto_replied_requests: int
    avg_first_response_seconds: float | None = None


class OverviewStatsView(BaseModel):
    total_requests: int
    open_requests: int
    closed_requests: int
    answered_requests: int
    unanswered_requests: int
    auto_replied_requests: int
    response_rate: float
    average_first_response_seconds: float | None = None
    median_first_response_seconds: float | None = None
    groups: list[dict[str, Any]] = Field(default_factory=list)
    agents: list[dict[str, Any]] = Field(default_factory=list)
    recent_unresolved: list[dict[str, Any]] = Field(default_factory=list)
