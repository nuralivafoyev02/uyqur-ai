from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import AppContainer, get_container, get_current_admin_user
from app.models.dto import GroupUpdateRequest
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/admin/groups", tags=["admin-groups"])


@router.get("")
async def list_groups(
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    from_at, to_at = container.stats_service.resolve_window("today", container.settings.app_timezone)
    return await container.group_service.list_groups(from_at, to_at)


@router.get("/{group_id}")
async def get_group(group_id: str, container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    group = await container.group_service.get_group(group_id)
    return group or {}


@router.patch("/{group_id}")
async def update_group(
    group_id: str,
    payload: GroupUpdateRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    changes = payload.model_dump(exclude_none=True)
    if "group_type" in changes:
        changes["group_type"] = changes["group_type"].value
    return await container.group_service.update_group(group_id, changes, actor_id=user["id"])


@router.post("/sync")
async def sync_groups(
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    from_at, to_at = container.stats_service.resolve_window("today", container.settings.app_timezone)
    return await container.group_service.list_groups(from_at, to_at)
