from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import GroupType
from app.utils.time import isoformat


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_context(
    *,
    update_id: int,
    chat_id: int,
    message_id: int,
    user_id: int,
    username: str | None,
    full_name: str,
    text: str,
    chat_type: str = "supergroup",
    chat_title: str = "Support Group",
    reply_to_message_id: int | None = None,
    created_at: datetime | None = None,
    thread_id: int | None = None,
    is_command: bool = False,
    command: str | None = None,
    command_args: list[str] | None = None,
):
    created_at = created_at or utc_now()
    return SimpleNamespace(
        update_id=update_id,
        chat_id=chat_id,
        chat_title=chat_title,
        chat_type=chat_type,
        message_id=message_id,
        thread_id=thread_id,
        text=text,
        normalized_text=text.lower(),
        created_at=created_at,
        reply_to_message_id=reply_to_message_id,
        identity=SimpleNamespace(
            telegram_user_id=user_id,
            username=username,
            full_name=full_name,
            is_bot=False,
        ),
        raw_message={
            "message_id": message_id,
            "chat": {"id": chat_id, "type": chat_type, "title": chat_title},
            "from": {"id": user_id, "username": username, "first_name": full_name},
        },
        is_command=is_command,
        command=command,
        command_args=command_args or [],
    )


class FakeAuditService:
    def __init__(self):
        self.logs = []
        self.command_logs = []
        self.errors = []

    async def log(self, **payload):
        self.logs.append(payload)
        return payload

    async def log_command(self, **payload):
        self.command_logs.append(payload)
        return payload

    async def log_error(self, scope, message, context=None):
        entry = {"scope": scope, "message": message, "context": context or {}}
        self.errors.append(entry)
        return entry

    async def list_logs(self, filters=None, limit=100):
        return self.logs[:limit]


class FakeCustomerRepository:
    def __init__(self):
        self.customers = {}

    async def upsert_customer(self, *, telegram_user_id, username, full_name, language="uz"):
        key = telegram_user_id
        existing = self.customers.get(key)
        if existing:
            existing.update({"username": username, "full_name": full_name, "language": language})
            return deepcopy(existing)
        created = {
            "id": str(uuid4()),
            "telegram_user_id": telegram_user_id,
            "username": username,
            "full_name": full_name,
            "language": language,
        }
        self.customers[key] = created
        return deepcopy(created)


class FakeMessageRepository:
    def __init__(self):
        self.messages = []

    async def create_message(self, payload):
        existing = next(
            (
                item
                for item in self.messages
                if item["chat_id"] == payload["chat_id"]
                and item["telegram_message_id"] == payload["telegram_message_id"]
            ),
            None,
        )
        if existing:
            return deepcopy(existing)
        created = {"id": str(uuid4()), **payload}
        self.messages.append(created)
        return deepcopy(created)

    async def get_by_chat_message(self, chat_id, message_id):
        for item in self.messages:
            if item["chat_id"] == chat_id and item["telegram_message_id"] == message_id:
                return deepcopy(item)
        return None

    async def list_by_ticket(self, ticket_id):
        return [deepcopy(item) for item in self.messages if item["ticket_id"] == ticket_id]


class FakeTicketRepository:
    def __init__(self):
        self.tickets = {}
        self.events = []

    async def get_latest_customer_ticket(self, *, group_id, customer_id, topic_id):
        rows = [
            item
            for item in self.tickets.values()
            if item["group_id"] == group_id
            and item["customer_id"] == customer_id
            and item.get("topic_id") == topic_id
        ]
        rows.sort(key=lambda item: item["created_at"], reverse=True)
        return deepcopy(rows[0]) if rows else None

    async def create_ticket(self, payload):
        ticket_id = str(uuid4())
        created = {
            "id": ticket_id,
            "created_at": payload.get("source_message_at") or isoformat(utc_now()),
            "updated_at": payload.get("source_message_at") or isoformat(utc_now()),
            "closed_at": None,
            "closed_by_agent_id": None,
            "first_response_at": None,
            "first_response_seconds": None,
            "auto_replied_at": None,
            "auto_reply_confidence": None,
            "last_agent_reply_at": None,
            "reopened_count": 0,
            **payload,
        }
        self.tickets[ticket_id] = created
        return deepcopy(created)

    async def update_ticket(self, ticket_id, payload):
        self.tickets[ticket_id].update(payload)
        self.tickets[ticket_id]["updated_at"] = isoformat(utc_now())
        return deepcopy(self.tickets[ticket_id])

    async def get_ticket(self, ticket_id):
        ticket = deepcopy(self.tickets.get(ticket_id))
        if not ticket:
            return None
        ticket.setdefault("telegram_groups", {"title": "Support Group", "chat_id": -1001})
        ticket.setdefault("customers", {"full_name": "Customer", "username": "customer"})
        return ticket

    async def list_tickets(self, *, filters=None, order="created_at.desc", limit=None, offset=None):
        rows = list(self.tickets.values())
        if filters and "status" in filters:
            raw = filters["status"]
            if raw.startswith("eq."):
                rows = [row for row in rows if row["status"] == raw.removeprefix("eq.")]
            elif raw.startswith("in.("):
                allowed = set(raw.removeprefix("in.(").removesuffix(")").split(","))
                rows = [row for row in rows if row["status"] in allowed]
        rows.sort(key=lambda item: item["created_at"], reverse=True)
        if limit is not None:
            rows = rows[:limit]
        result = []
        for row in rows:
            item = deepcopy(row)
            item.setdefault("telegram_groups", {"title": "Support Group", "chat_id": -1001})
            item.setdefault("customers", {"full_name": "Customer", "username": "customer"})
            result.append(item)
        return result

    async def create_event(self, payload):
        self.events.append(payload)
        return payload

    async def insert(self, table, payload):
        return payload


class FakeStatsRepository:
    def __init__(self):
        self.stale_rows = []

    async def stale_tickets(self, cutoff_at):
        return deepcopy(self.stale_rows)


class FakeSettingService:
    def __init__(self, values=None):
        self.values = values or {
            "auto_reply_enabled": True,
            "auto_reply_delay_minutes": 5,
            "auto_reply_confidence_threshold": 0.62,
            "response_merge_window_minutes": 30,
            "reopen_window_minutes": 60,
            "default_language": "uz",
            "timezone": "Asia/Tashkent",
            "management_group_chat_id": -100999,
        }

    async def get_runtime_settings(self):
        return deepcopy(self.values)


class FakeKnowledgeRepository:
    def __init__(self, entries=None):
        self.entries = entries or []

    async def list_entries(self, only_active=False):
        if not only_active:
            return deepcopy(self.entries)
        return [deepcopy(item) for item in self.entries if item.get("is_active", True)]

    async def create_entry(self, payload):
        created = {"id": str(uuid4()), **payload}
        self.entries.append(created)
        return deepcopy(created)

    async def update_entry(self, entry_id, payload):
        for item in self.entries:
            if item["id"] == entry_id:
                item.update(payload)
                return deepcopy(item)
        raise KeyError(entry_id)

    async def get_entry(self, entry_id):
        for item in self.entries:
            if item["id"] == entry_id:
                return deepcopy(item)
        return None

    async def delete_entry(self, entry_id):
        self.entries = [item for item in self.entries if item["id"] != entry_id]

    async def replace_terms(self, entry_id, terms):
        for item in self.entries:
            if item["id"] == entry_id:
                item["kb_terms"] = terms
                return deepcopy(terms)
        return []


class FakeTelegramService:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, *, chat_id, text, reply_to_message_id=None, thread_id=None, disable_notification=True):
        payload = {
            "message_id": 9000 + len(self.sent_messages) + 1,
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id,
            "thread_id": thread_id,
        }
        self.sent_messages.append(payload)
        return {"message_id": payload["message_id"], "chat": {"id": chat_id}, "text": text}

    async def get_webhook_info(self):
        return {"url": "https://example.com/telegram/webhook"}

    async def get_me(self):
        return {"id": 1, "username": "uyqur_test_bot"}


class FakeAdminRepository:
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.rate_limits = {}

    async def get_user_by_username(self, username):
        for user in self.users.values():
            if user["username"].lower() == username.lower() and user["is_active"]:
                return deepcopy(user)
        return None

    async def get_user_by_id(self, user_id):
        user = self.users.get(user_id)
        return deepcopy(user) if user else None

    async def create_user(self, payload):
        user_id = str(uuid4())
        created = {
            "id": user_id,
            "created_at": isoformat(utc_now()),
            "updated_at": isoformat(utc_now()),
            **payload,
        }
        self.users[user_id] = created
        return deepcopy(created)

    async def update_user(self, user_id, payload):
        self.users[user_id].update(payload)
        return deepcopy(self.users[user_id])

    async def create_session(self, payload):
        session_id = str(uuid4())
        created = {"id": session_id, "revoked_at": None, **payload}
        self.sessions[session_id] = created
        return deepcopy(created)

    async def get_session(self, token_hash):
        for session in self.sessions.values():
            if session["token_hash"] == token_hash and session["revoked_at"] is None:
                data = deepcopy(session)
                data["admin_users"] = deepcopy(self.users[session["admin_user_id"]])
                return data
        return None

    async def revoke_session(self, session_id):
        self.sessions[session_id]["revoked_at"] = isoformat(utc_now())
        return [deepcopy(self.sessions[session_id])]

    async def revoke_other_sessions(self, user_id, except_session_id=None):
        for session_id, session in self.sessions.items():
            if session["admin_user_id"] == user_id and session_id != except_session_id:
                session["revoked_at"] = isoformat(utc_now())

    async def touch_session(self, session_id, expires_at):
        self.sessions[session_id]["expires_at"] = isoformat(expires_at)
        return deepcopy(self.sessions[session_id])

    async def auth_rate_limit_hit(self, key):
        value = self.rate_limits.get(key)
        return [deepcopy(value)] if value else []

    async def auth_rate_limit_fail(self, key):
        current = self.rate_limits.get(key) or {"attempts": 0, "blocked_until": None}
        current["attempts"] += 1
        if current["attempts"] >= 5:
            current["blocked_until"] = isoformat(utc_now() + timedelta(minutes=15))
        self.rate_limits[key] = current
        return [deepcopy(current)]

    async def auth_rate_limit_reset(self, key):
        self.rate_limits.pop(key, None)

    async def expire_sessions(self):
        count = 0
        now = utc_now()
        for session in self.sessions.values():
            expires_at = datetime.fromisoformat(session["expires_at"])
            if session["revoked_at"] is None and expires_at < now:
                session["revoked_at"] = isoformat(now)
                count += 1
        return count


class FakeAgentService:
    def __init__(self, privileged_agent=None):
        self.privileged_agent = privileged_agent

    async def find_agent(self, username, chat_id):
        if self.privileged_agent and (
            username == self.privileged_agent.get("telegram_username")
            or chat_id == self.privileged_agent.get("telegram_chat_id")
        ):
            return deepcopy(self.privileged_agent)
        return None

    async def register_private_chat(self, telegram_username, chat_id):
        if self.privileged_agent and telegram_username == self.privileged_agent.get("telegram_username"):
            self.privileged_agent["telegram_chat_id"] = chat_id
            return deepcopy(self.privileged_agent)
        return None

    @staticmethod
    def is_privileged(agent):
        return bool(agent and agent.get("role") in {"manager", "admin"})


class FakeStatsService:
    def __init__(self):
        self.overview_payload = {
            "total_requests": 10,
            "open_requests": 2,
            "closed_requests": 8,
            "answered_requests": 8,
            "unanswered_requests": 2,
            "auto_replied_requests": 1,
            "response_rate": 80.0,
            "average_first_response_seconds": 120.0,
        }

    def resolve_window(self, label, tz_name):
        now = utc_now()
        return now - timedelta(hours=1), now

    async def overview(self, from_at, to_at):
        return deepcopy(self.overview_payload)

    async def group_stats(self, from_at, to_at):
        return [{"title": "Support Group", "total_requests": 10, "open_requests": 2, "closed_requests": 8, "response_rate": 80.0}]

    async def agent_stats(self, from_at, to_at):
        return [{"display_name": "Manager", "handled_tickets": 4, "avg_first_response_seconds": 90.0}]

    def render_overview_text(self, label, payload):
        return f"{label}: {payload['total_requests']}"

    def render_group_stats_text(self, rows):
        return "group stats"

    def render_agent_stats_text(self, rows):
        return "agent stats"

    def render_open_tickets_text(self, rows):
        return "open tickets"


class FakeGroupRepository:
    def __init__(self):
        self.groups = {}

    async def get_by_chat_id(self, chat_id):
        return deepcopy(self.groups.get(chat_id))

    async def upsert_group(self, *, chat_id, title, username, group_type, is_forum, is_active=True):
        current = self.groups.get(chat_id) or {
            "id": str(uuid4()),
            "chat_id": chat_id,
            "title": title,
            "username": username,
            "group_type": group_type.value if isinstance(group_type, GroupType) else group_type,
            "is_active": is_active,
            "is_forum": is_forum,
        }
        current.update(
            {
                "title": title,
                "username": username,
                "group_type": group_type.value if isinstance(group_type, GroupType) else group_type,
                "is_active": is_active,
                "is_forum": is_forum,
            }
        )
        self.groups[chat_id] = current
        return deepcopy(current)
