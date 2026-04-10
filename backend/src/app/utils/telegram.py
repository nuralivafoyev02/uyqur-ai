from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.domain import MessageContext, TelegramIdentity
from app.utils.text import normalize_text


def is_service_message(message: dict[str, Any]) -> bool:
    service_keys = {
        "new_chat_members",
        "left_chat_member",
        "new_chat_title",
        "delete_chat_photo",
        "group_chat_created",
        "supergroup_chat_created",
        "forum_topic_created",
        "forum_topic_closed",
        "forum_topic_reopened",
        "video_chat_started",
        "video_chat_ended",
        "migrate_to_chat_id",
        "migrate_from_chat_id",
    }
    return any(key in message for key in service_keys)


def extract_message_text(message: dict[str, Any]) -> str:
    if "text" in message and message["text"]:
        return str(message["text"])
    if "caption" in message and message["caption"]:
        return str(message["caption"])
    if "forum_topic_created" in message:
        return str(message["forum_topic_created"].get("name", ""))
    return ""


def message_thread_id(message: dict[str, Any]) -> int | None:
    return message.get("message_thread_id")


def parse_command(text: str) -> tuple[str | None, list[str]]:
    if not text.startswith("/"):
        return None, []
    chunks = text.strip().split()
    command = chunks[0].split("@", 1)[0].lower()
    return command, chunks[1:]


def build_message_context(update_id: int, message: dict[str, Any]) -> MessageContext:
    actor = message.get("from", {})
    first_name = actor.get("first_name", "") or ""
    last_name = actor.get("last_name", "") or ""
    full_name = " ".join(part for part in [first_name, last_name] if part).strip() or actor.get(
        "username", "Noma'lum"
    )
    raw_text = extract_message_text(message)
    command, args = parse_command(raw_text)
    created_at = datetime.fromtimestamp(message["date"], tz=timezone.utc)
    return MessageContext(
        update_id=update_id,
        chat_id=int(message["chat"]["id"]),
        chat_title=message["chat"].get("title") or message["chat"].get("username") or "Private chat",
        chat_type=message["chat"].get("type", "private"),
        message_id=int(message["message_id"]),
        thread_id=message_thread_id(message),
        text=raw_text,
        normalized_text=normalize_text(raw_text),
        created_at=created_at,
        reply_to_message_id=(
            int(message["reply_to_message"]["message_id"]) if message.get("reply_to_message") else None
        ),
        identity=TelegramIdentity(
            telegram_user_id=int(actor["id"]) if actor.get("id") is not None else None,
            username=actor.get("username"),
            full_name=full_name,
            is_bot=bool(actor.get("is_bot", False)),
        ),
        raw_message=message,
        is_command=command is not None,
        command=command,
        command_args=args,
    )
