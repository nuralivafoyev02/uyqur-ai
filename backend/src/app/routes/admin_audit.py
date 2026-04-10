from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import AppContainer, get_container, get_current_admin_user

router = APIRouter(prefix="/api/admin/audit-logs", tags=["admin-audit"])


@router.get("")
async def list_audit_logs(
    action: str | None = Query(default=None),
    actor_type: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    filters: dict[str, str] = {}
    if action:
        filters["action"] = f"eq.{action}"
    if actor_type:
        filters["actor_type"] = f"eq.{actor_type}"
    return await container.audit_service.list_logs(filters=filters or None, limit=limit)
