from __future__ import annotations

from app.config import Settings


def test_production_defaults_enable_secure_cookies_and_use_webapp_origin_for_cors():
    settings = Settings.from_env(
        {
            "APP_ENV": "production",
            "APP_BASE_URL": "https://backend.example.workers.dev",
            "ADMIN_WEBAPP_URL": "https://admin.example.workers.dev",
        }
    )

    assert settings.session_secure_cookies is True
    assert settings.session_cookie_same_site == "none"
    assert settings.cors_origins == ["https://admin.example.workers.dev"]
    assert settings.bootstrap_admin_password == ""


def test_cookie_settings_can_be_overridden_explicitly():
    settings = Settings.from_env(
        {
            "APP_ENV": "production",
            "APP_BASE_URL": "https://backend.example.workers.dev",
            "ADMIN_WEBAPP_URL": "https://admin.example.workers.dev",
            "SESSION_COOKIE_DOMAIN": ".example.com",
            "SESSION_COOKIE_SAMESITE": "strict",
        }
    )

    assert settings.session_cookie_domain == ".example.com"
    assert settings.session_cookie_same_site == "strict"
