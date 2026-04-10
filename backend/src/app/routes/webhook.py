from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.dependencies import AppContainer, get_container

router = APIRouter(tags=["telegram"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    container: AppContainer = Depends(get_container),
    telegram_secret: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict:
    if container.settings.telegram_webhook_secret and telegram_secret != container.settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook secret noto'g'ri")
    update = await request.json()
    try:
        return await container.bot.process_update(
            update,
            claim_processed=container.audit_repository.claim_processed_update,
        )
    except Exception as exc:
        await container.audit_service.log_error(
            "telegram_webhook",
            str(exc),
            {"update_id": update.get("update_id"), "keys": list(update.keys())},
        )
        raise HTTPException(status_code=500, detail="Telegram update qayta ishlanmadi") from exc
