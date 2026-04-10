from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import AppContainer, get_container
from app.utils.time import isoformat, utc_now

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck(container: AppContainer = Depends(get_container)) -> dict:
    return {
        "status": "ok" if container.settings.is_configured() else "degraded",
        "configured": container.settings.is_configured(),
        "time": isoformat(utc_now()),
        "timezone": container.settings.app_timezone,
    }
