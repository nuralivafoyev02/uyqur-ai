from __future__ import annotations

from datetime import datetime, timezone

from app.routes.admin_auth import _build_session_view


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
