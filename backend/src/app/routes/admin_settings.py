from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import AppContainer, get_container, get_current_admin_user
from app.models.dto import PasswordChangeRequest, SettingsPatchRequest
from app.models.enums import ActorType, AuditAction

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])


class AutoReplySimulationRequest(BaseModel):
    text: str = Field(min_length=2, max_length=2000)


@router.get("")
async def get_settings(container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    return {"values": await container.setting_service.get_runtime_settings()}


@router.patch("")
async def patch_settings(
    payload: SettingsPatchRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    values = await container.setting_service.patch_settings(payload.values, admin_user_id=user["id"])
    await container.audit_service.log(
        actor_type=ActorType.ADMIN,
        actor_id=user["id"],
        action=AuditAction.SETTINGS_UPDATED.value,
        entity_type="settings",
        entity_id="bot_settings",
        metadata=payload.values,
    )
    return {"values": values}


@router.get("/bot-status")
async def get_bot_status(container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    webhook_info = await container.telegram_service.get_webhook_info()
    bot_info = await container.telegram_service.get_me()
    groups = await container.group_service.list_groups()
    return {
        "bot": bot_info,
        "webhook": webhook_info,
        "groups": groups,
        "settings": await container.setting_service.get_runtime_settings(),
    }


@router.post("/test-summary")
async def test_summary(container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    return await container.management_service.send_test_summary()


@router.post("/test-auto-reply")
async def test_auto_reply(
    payload: AutoReplySimulationRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    return await container.auto_reply_service.simulate(payload.text)
