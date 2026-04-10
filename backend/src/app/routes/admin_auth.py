from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response

from app.dependencies import AppContainer, get_container, get_current_admin_user, get_current_session
from app.models.dto import AdminUserView, LoginRequest, PasswordChangeRequest, SessionView

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


def _set_session_cookie(response: Response, container: AppContainer, token: str) -> None:
    response.set_cookie(
        key=container.settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=container.settings.session_secure_cookies,
        samesite="lax",
        max_age=container.settings.session_ttl_hours * 3600,
        path="/",
    )


def _build_session_view(
    *,
    authenticated: bool,
    user: dict | None,
    must_change_password: bool = False,
    expires_at: datetime | None = None,
) -> SessionView:
    safe_user = AdminUserView.model_validate(user) if user else None
    return SessionView(
        authenticated=authenticated,
        user=safe_user,
        must_change_password=must_change_password,
        expires_at=expires_at,
    )


@router.post("/login", response_model=SessionView)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    container: AppContainer = Depends(get_container),
) -> SessionView:
    result = await container.auth_service.login(
        payload.username,
        payload.password,
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
    )
    _set_session_cookie(response, container, result["token"])
    return _build_session_view(
        authenticated=True,
        user=result["user"],
        must_change_password=result["user"]["must_change_password"],
        expires_at=result["expires_at"],
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    container: AppContainer = Depends(get_container),
) -> dict:
    await container.auth_service.logout(request.cookies.get(container.settings.session_cookie_name))
    response.delete_cookie(container.settings.session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=SessionView)
async def me(request: Request, container: AppContainer = Depends(get_container)) -> SessionView:
    session = await container.auth_service.get_session(
        request.cookies.get(container.settings.session_cookie_name)
    )
    if not session:
        return _build_session_view(authenticated=False, user=None)
    return _build_session_view(
        authenticated=True,
        user=session["admin_users"],
        must_change_password=session["admin_users"]["must_change_password"],
        expires_at=session["expires_at"],
    )


@router.post("/change-password")
async def change_password(
    payload: PasswordChangeRequest,
    session: dict = Depends(get_current_session),
    user: dict = Depends(get_current_admin_user),
    container: AppContainer = Depends(get_container),
) -> dict:
    await container.auth_service.change_password(
        user_id=user["id"],
        current_password=payload.current_password,
        new_password=payload.new_password,
        session_id=session["id"],
    )
    return {"ok": True}
