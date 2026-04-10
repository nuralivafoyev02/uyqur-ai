from __future__ import annotations

from app.config import Settings
from app.services.auth_service import AuthError, AuthService
from tests.fakes import FakeAdminRepository, FakeAuditService


async def test_admin_login_flow():
    repository = FakeAdminRepository()
    audit = FakeAuditService()
    service = AuthService(repository, Settings(), audit)

    await service.ensure_bootstrap_admin()
    result = await service.login("admin", "admin123", "127.0.0.1", "pytest")

    assert result["user"]["username"] == "admin"
    assert result["token"]
    assert len(repository.sessions) == 1


async def test_first_login_password_change_requirement():
    repository = FakeAdminRepository()
    audit = FakeAuditService()
    settings = Settings()
    service = AuthService(repository, settings, audit)

    await service.ensure_bootstrap_admin()
    login = await service.login("admin", "admin123", "127.0.0.1", "pytest")
    assert login["user"]["must_change_password"] is True

    await service.change_password(
        user_id=login["user"]["id"],
        current_password="admin123",
        new_password="VeryStrongPass123",
        session_id=login["session"]["id"],
    )

    refreshed = await repository.get_user_by_id(login["user"]["id"])
    assert refreshed["must_change_password"] is False
    second_login = await service.login("admin", "VeryStrongPass123", "127.0.0.1", "pytest")
    assert second_login["user"]["must_change_password"] is False


async def test_change_password_rejects_weak_or_reused_password():
    repository = FakeAdminRepository()
    audit = FakeAuditService()
    service = AuthService(repository, Settings(), audit)

    await service.ensure_bootstrap_admin()
    login = await service.login("admin", "admin123", "127.0.0.1", "pytest")

    try:
        await service.change_password(
            user_id=login["user"]["id"],
            current_password="admin123",
            new_password="admin123",
            session_id=login["session"]["id"],
        )
    except AuthError as exc:
        assert "bir xil" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected same-password validation to fail")

    try:
        await service.change_password(
            user_id=login["user"]["id"],
            current_password="admin123",
            new_password="Short123",
            session_id=login["session"]["id"],
        )
    except AuthError as exc:
        assert "kamida 12" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected weak-password validation to fail")


async def test_production_bootstrap_requires_strong_password():
    repository = FakeAdminRepository()
    audit = FakeAuditService()
    settings = Settings.from_env({"APP_ENV": "production", "BOOTSTRAP_ADMIN_PASSWORD": "admin123"})
    service = AuthService(repository, settings, audit)

    try:
        await service.ensure_bootstrap_admin()
    except AuthError as exc:
        assert "BOOTSTRAP_ADMIN_PASSWORD" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected production bootstrap password validation to fail")
