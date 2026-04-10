from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import AppContainer, get_container, get_current_admin_user
from app.utils.time import parse_datetime

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"])


def _resolve_window(container: AppContainer, window: str | None, from_date: str | None, to_date: str | None):
    if from_date and to_date:
        return parse_datetime(from_date), parse_datetime(to_date)
    chosen = window or "today"
    return container.stats_service.resolve_window(chosen, container.settings.app_timezone)


@router.get("/overview")
async def overview(
    window: str | None = Query(default="today"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    from_at, to_at = _resolve_window(container, window, from_date, to_date)
    return await container.stats_service.overview(from_at, to_at)


@router.get("/groups")
async def groups(
    window: str | None = Query(default="today"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    from_at, to_at = _resolve_window(container, window, from_date, to_date)
    return await container.stats_service.group_stats(from_at, to_at)


@router.get("/agents")
async def agents(
    window: str | None = Query(default="today"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    from_at, to_at = _resolve_window(container, window, from_date, to_date)
    return await container.stats_service.agent_stats(from_at, to_at)


@router.get("/timeline")
async def timeline(
    window: str | None = Query(default="today"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    bucket: str = Query(default="day"),
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    from_at, to_at = _resolve_window(container, window, from_date, to_date)
    return await container.stats_service.timeline(from_at, to_at, bucket)
