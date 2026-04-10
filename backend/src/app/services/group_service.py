from __future__ import annotations

from app.models.enums import AuditAction, ActorType
from app.repositories.group_repository import GroupRepository
from app.services.audit_service import AuditService
from app.services.stats_service import StatsService


class GroupService:
    def __init__(self, repository: GroupRepository, stats_service: StatsService, audit_service: AuditService):
        self.repository = repository
        self.stats_service = stats_service
        self.audit_service = audit_service

    async def list_groups(self, from_at=None, to_at=None) -> list[dict]:
        groups = await self.repository.list_groups()
        metrics_map: dict[str, dict] = {}
        if from_at and to_at:
            for row in await self.stats_service.group_stats(from_at, to_at):
                metrics_map[row["id"]] = row
        for group in groups:
            group["metrics"] = metrics_map.get(group["id"], {})
        return groups

    async def get_group(self, group_id: str) -> dict | None:
        return await self.repository.get_group(group_id)

    async def update_group(self, group_id: str, payload: dict, actor_id: str | None = None) -> dict:
        group = await self.repository.update_group(group_id, payload)
        await self.audit_service.log(
            actor_type=ActorType.ADMIN if actor_id else ActorType.SYSTEM,
            actor_id=actor_id,
            action=AuditAction.GROUP_UPDATED.value,
            entity_type="telegram_group",
            entity_id=group_id,
            metadata=payload,
        )
        return group
