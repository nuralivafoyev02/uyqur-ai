from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Response

from app.config import Settings
from app.dependencies import AppContainer
from app.routes.admin_auth import _build_session_view, _set_session_cookie


def test_build_session_view_filters_sensitive_fields():
    payload = _build_session_view(
        authenticated=True,
        user={
            "id": "user-1",
            "username": "admin",
            "display_name": "System Administrator",
            "must_change_password": True,
            "is_bootstrap": True,
            "created_at": datetime(2026, 4, 10, tzinfo=timezone.utc),
            "password_hash": "secret",
            "username_normalized": "admin",
            "last_login_at": "2026-04-10T00:00:00Z",
        },
        must_change_password=True,
        expires_at=datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc),
    )

    data = payload.model_dump(mode="json")
    assert data["authenticated"] is True
    assert data["must_change_password"] is True
    assert data["user"]["username"] == "admin"
    assert "password_hash" not in data["user"]
    assert "username_normalized" not in data["user"]
    assert "last_login_at" not in data["user"]


def test_set_session_cookie_uses_configured_samesite_and_domain():
    settings = Settings.from_env(
        {
            "APP_ENV": "production",
            "APP_BASE_URL": "https://backend.example.workers.dev",
            "ADMIN_WEBAPP_URL": "https://admin.example.workers.dev",
            "SESSION_COOKIE_DOMAIN": ".example.com",
        }
    )
    container = AppContainer(
        settings=settings,
        group_repository=None,
        audit_repository=None,
        agent_service=None,
        audit_service=None,
        auth_service=None,
        knowledge_service=None,
        ticket_service=None,
        stats_service=None,
        telegram_service=None,
        setting_service=None,
        group_service=None,
        management_service=None,
        auto_reply_service=None,
        scheduler_service=None,
        bot=None,
    )
    response = Response()

    _set_session_cookie(response, container, "token-123")

    header = response.headers.get("set-cookie", "")
    assert "SameSite=none" in header
    assert "Domain=.example.com" in header
    assert "HttpOnly" in header
    assert "Secure" in header
