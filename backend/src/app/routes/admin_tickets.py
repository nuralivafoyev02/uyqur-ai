from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import AppContainer, get_container, get_current_admin_user
from app.models.dto import ManualReplyLogRequest, TicketStatusUpdateRequest
from app.utils.time import parse_datetime

router = APIRouter(prefix="/api/admin/tickets", tags=["admin-tickets"])


@router.get("")
async def list_tickets(
    status: str | None = Query(default=None),
    group_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_closed: bool = Query(default=True),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> list[dict]:
    rows = await container.ticket_service.list_tickets(
        {
            "status": status,
            "group_id": group_id,
            "search": search,
            "include_closed": include_closed,
            "from_date": parse_datetime(from_date),
            "to_date": parse_datetime(to_date),
        }
    )
    return rows


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    return await container.ticket_service.get_ticket_detail(ticket_id) or {}


@router.patch("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdateRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    return await container.ticket_service.update_status(ticket_id, payload.status.value, payload.note, user["id"])


@router.post("/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, container: AppContainer = Depends(get_container), user: dict = Depends(get_current_admin_user)) -> dict:
    return await container.ticket_service.reopen_ticket(ticket_id, user["id"])


@router.post("/{ticket_id}/manual-reply-log")
async def manual_reply_log(
    ticket_id: str,
    payload: ManualReplyLogRequest,
    container: AppContainer = Depends(get_container),
    user: dict = Depends(get_current_admin_user),
) -> dict:
    return await container.ticket_service.manual_reply_log(ticket_id, payload.agent_id, payload.replied_at, payload.note)
