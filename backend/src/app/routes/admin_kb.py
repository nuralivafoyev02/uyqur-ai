from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import AppContainer, get_container, get_current_admin_user
from app.models.dto import KBEntryRequest, KBTestRequest
from app.models.enums import ActorType, AuditAction

router = APIRouter(prefix="/api/admin/kb", tags=["admin-kb"])


@router.get("")
async def list_kb(container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> list[dict]:
    return await container.knowledge_service.list_entries()


@router.post("")
async def create_kb(
    payload: KBEntryRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    entry = await container.knowledge_service.create_entry(payload.model_dump())
    await container.audit_service.log(
        actor_type=ActorType.ADMIN,
        actor_id=user["id"],
        action=AuditAction.KB_CREATED.value,
        entity_type="kb_entry",
        entity_id=entry["id"],
        metadata={"title": entry["title"]},
    )
    return entry


@router.patch("/{entry_id}")
async def update_kb(
    entry_id: str,
    payload: KBEntryRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    entry = await container.knowledge_service.update_entry(entry_id, payload.model_dump())
    await container.audit_service.log(
        actor_type=ActorType.ADMIN,
        actor_id=user["id"],
        action=AuditAction.KB_UPDATED.value,
        entity_type="kb_entry",
        entity_id=entry_id,
        metadata={"title": entry["title"]},
    )
    return entry


@router.delete("/{entry_id}")
async def delete_kb(
    entry_id: str,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    await container.knowledge_service.delete_entry(entry_id)
    await container.audit_service.log(
        actor_type=ActorType.ADMIN,
        actor_id=user["id"],
        action=AuditAction.KB_DELETED.value,
        entity_type="kb_entry",
        entity_id=entry_id,
        metadata={},
    )
    return {"ok": True}


@router.post("/test-match")
async def test_match(
    payload: KBTestRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    runtime = await container.setting_service.get_runtime_settings()
    return await container.knowledge_service.preview_match(
        payload.text,
        language=payload.language,
        default_threshold=float(runtime.get("auto_reply_confidence_threshold", 0.62)),
    )
