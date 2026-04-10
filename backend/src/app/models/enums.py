from __future__ import annotations

from enum import Enum


class GroupType(str, Enum):
    SUPPORT = "support"
    MANAGEMENT = "management"


class TicketStatus(str, Enum):
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"
    REOPENED = "reopened"
    AUTO_REPLIED = "auto_replied"


class TicketEventType(str, Enum):
    CREATED = "created"
    CUSTOMER_MESSAGE = "customer_message"
    AGENT_REPLIED = "agent_replied"
    CLOSED = "closed"
    REOPENED = "reopened"
    AUTO_REPLIED = "auto_replied"
    STATUS_CHANGED = "status_changed"
    MANUAL_REPLY_LOGGED = "manual_reply_logged"


class ActorType(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"
    BOT = "bot"
    SYSTEM = "system"


class AgentRole(str, Enum):
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"


class ReportType(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    ALERT = "alert"


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    GROUP_UPDATED = "group_updated"
    SETTINGS_UPDATED = "settings_updated"
    KB_CREATED = "kb_created"
    KB_UPDATED = "kb_updated"
    KB_DELETED = "kb_deleted"
    BOT_COMMAND = "bot_command"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    ERROR = "error"
