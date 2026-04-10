from __future__ import annotations

from typing import Any

from app.models.enums import ActorType
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def log(
        self,
        *,
        actor_type: ActorType,
        actor_id: str | None,
        action: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> dict:
        return await self.repository.log_audit(
            {
                "actor_type": actor_type.value,
                "actor_id": actor_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "metadata": metadata or {},
                "ip_address": ip_address,
            }
        )

    async def log_command(
        self,
        *,
        chat_id: int,
        telegram_user_id: int | None,
        command: str,
        args: list[str],
        was_authorized: bool,
        response_summary: str,
    ) -> dict:
        return await self.repository.log_command(
            {
                "chat_id": chat_id,
                "telegram_user_id": telegram_user_id,
                "command": command,
                "args": args,
                "was_authorized": was_authorized,
                "response_summary": response_summary,
            }
        )

    async def log_error(self, scope: str, message: str, context: dict[str, Any] | None = None) -> dict:
        return await self.repository.log_error(
            {
                "scope": scope,
                "message": message,
                "context": context or {},
            }
        )

    async def list_logs(self, filters: dict[str, str] | None = None, limit: int = 100) -> list[dict]:
        return await self.repository.list_audit_logs(filters=filters, limit=limit)
