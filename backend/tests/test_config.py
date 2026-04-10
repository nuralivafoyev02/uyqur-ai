from __future__ import annotations

from app.config import Settings


def test_production_defaults_enable_secure_cookies_and_disable_cors_fallback():
    settings = Settings.from_env(
        {
            "APP_ENV": "production",
            "APP_BASE_URL": "https://backend.example.workers.dev",
        }
    )

    assert settings.session_secure_cookies is True
    assert settings.cors_origins == []
    assert settings.bootstrap_admin_password == ""
