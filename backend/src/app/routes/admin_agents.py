from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import AppContainer, get_container, get_current_admin_user
from app.models.dto import AgentCreateRequest, AgentUpdateRequest

router = APIRouter(prefix="/api/admin/agents", tags=["admin-agents"])


@router.get("")
async def list_agents(container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> list[dict]:
    from_at, to_at = container.stats_service.resolve_window("today", container.settings.app_timezone)
    return await container.agent_service.list_agents(from_at, to_at)


@router.post("")
async def create_agent(
    payload: AgentCreateRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    data = payload.model_dump()
    data["role"] = payload.role.value
    if data.get("telegram_username"):
        data["telegram_username"] = data["telegram_username"].lstrip("@")
    return await container.agent_service.create_agent(data, actor_id=user["id"])


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    payload: AgentUpdateRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    data = payload.model_dump(exclude_none=True)
    if "role" in data:
        data["role"] = payload.role.value if payload.role else None
    return await container.agent_service.update_agent(agent_id, data, actor_id=user["id"])


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    return await container.agent_service.delete_agent(agent_id, actor_id=user["id"])
