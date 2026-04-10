from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlparse

from app.constants import (
    AUTO_REPLY_CONFIDENCE_THRESHOLD,
    AUTO_REPLY_DELAY_MINUTES,
    DEFAULT_SAFE_FALLBACK_MESSAGE,
    DEFAULT_TIMEZONE,
    SESSION_TTL_HOURS,
    TICKET_MERGE_WINDOW_MINUTES,
    TICKET_REOPEN_WINDOW_MINUTES,
)


def _value(source: Mapping[str, Any] | Any | None, name: str, default: str | None = None) -> str | None:
    if source is None:
        return os.getenv(name, default)
    if isinstance(source, Mapping):
        raw = source.get(name, default)
        return None if raw is None else str(raw)
    raw = getattr(source, name, default)
    return None if raw is None else str(raw)


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _is_production_env(value: str | None) -> bool:
    return (value or "").strip().lower() == "production"


def _is_https_url(value: str | None) -> bool:
    if not value:
        return False
    try:
        return urlparse(value).scheme.lower() == "https"
    except ValueError:
        return False


def _normalize_same_site(value: str | None, default: str) -> str:
    candidate = (value or "").strip().lower()
    if candidate in {"lax", "strict", "none"}:
        return candidate
    return default


@dataclass
class Settings:
    app_env: str = "development"
    app_timezone: str = DEFAULT_TIMEZONE
    app_base_url: str = "http://localhost:8788"
    admin_webapp_url: str = "http://localhost:5173"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])

    telegram_bot_token: str = ""
    telegram_bot_username: str = ""
    telegram_webhook_secret: str = ""
    telegram_api_base: str = "https://api.telegram.org"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_rest_url: str = ""
    supabase_rpc_url: str = ""

    session_cookie_name: str = "uyqur_admin_session"
    session_cookie_domain: str | None = None
    session_cookie_same_site: str = "lax"
    session_secure_cookies: bool = False
    session_ttl_hours: int = SESSION_TTL_HOURS
    password_hash_iterations: int = 240_000

    auto_reply_delay_minutes: int = AUTO_REPLY_DELAY_MINUTES
    ticket_merge_window_minutes: int = TICKET_MERGE_WINDOW_MINUTES
    ticket_reopen_window_minutes: int = TICKET_REOPEN_WINDOW_MINUTES
    default_confidence_threshold: float = AUTO_REPLY_CONFIDENCE_THRESHOLD
    safe_fallback_message: str = DEFAULT_SAFE_FALLBACK_MESSAGE

    management_group_chat_id: int | None = None
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin123"

    @classmethod
    def from_env(cls, source: Mapping[str, Any] | Any | None = None) -> "Settings":
        app_env = _value(source, "APP_ENV", "development") or "development"
        production = _is_production_env(app_env)
        supabase_url = (_value(source, "SUPABASE_URL", "") or "").rstrip("/")
        rest_url = _value(source, "SUPABASE_REST_URL")
        rpc_url = _value(source, "SUPABASE_RPC_URL")
        app_base_url = _value(source, "APP_BASE_URL", "http://localhost:8788") or "http://localhost:8788"
        admin_webapp_url = _value(source, "ADMIN_WEBAPP_URL", "http://localhost:5173") or "http://localhost:5173"
        cors_source = _value(
            source,
            "CORS_ORIGINS",
            admin_webapp_url if admin_webapp_url else ("" if production else "http://localhost:5173"),
        )
        origins = (cors_source or "").split(",")
        management_chat = _value(source, "MANAGEMENT_GROUP_CHAT_ID")
        secure_cookie_default = production or _is_https_url(app_base_url)
        same_site_default = "none" if secure_cookie_default else "lax"
        default_bootstrap_password = "" if production else "admin123"
        return cls(
            app_env=app_env,
            app_timezone=_value(source, "APP_TIMEZONE", DEFAULT_TIMEZONE) or DEFAULT_TIMEZONE,
            app_base_url=app_base_url.rstrip("/"),
            admin_webapp_url=admin_webapp_url.rstrip("/"),
            cors_origins=[item.strip() for item in origins if item.strip()],
            telegram_bot_token=_value(source, "TELEGRAM_BOT_TOKEN", "") or "",
            telegram_bot_username=_value(source, "TELEGRAM_BOT_USERNAME", "") or "",
            telegram_webhook_secret=_value(source, "TELEGRAM_WEBHOOK_SECRET", "") or "",
            telegram_api_base=(
                _value(source, "TELEGRAM_API_BASE", "https://api.telegram.org")
                or "https://api.telegram.org"
            ).rstrip("/"),
            supabase_url=supabase_url,
            supabase_service_role_key=_value(source, "SUPABASE_SERVICE_ROLE_KEY", "") or "",
            supabase_rest_url=rest_url or f"{supabase_url}/rest/v1",
            supabase_rpc_url=rpc_url or f"{supabase_url}/rest/v1/rpc",
            session_cookie_name=_value(source, "SESSION_COOKIE_NAME", "uyqur_admin_session")
            or "uyqur_admin_session",
            session_cookie_domain=(_value(source, "SESSION_COOKIE_DOMAIN", "") or "").strip() or None,
            session_cookie_same_site=_normalize_same_site(
                _value(source, "SESSION_COOKIE_SAMESITE"),
                same_site_default,
            ),
            session_secure_cookies=_bool(
                _value(source, "SESSION_SECURE_COOKIES"),
                secure_cookie_default,
            ),
            session_ttl_hours=_int(_value(source, "SESSION_TTL_HOURS"), SESSION_TTL_HOURS),
            password_hash_iterations=_int(
                _value(source, "PASSWORD_HASH_ITERATIONS"), 240_000
            ),
            auto_reply_delay_minutes=_int(
                _value(source, "AUTO_REPLY_DELAY_MINUTES"), AUTO_REPLY_DELAY_MINUTES
            ),
            ticket_merge_window_minutes=_int(
                _value(source, "TICKET_MERGE_WINDOW_MINUTES"), TICKET_MERGE_WINDOW_MINUTES
            ),
            ticket_reopen_window_minutes=_int(
                _value(source, "TICKET_REOPEN_WINDOW_MINUTES"), TICKET_REOPEN_WINDOW_MINUTES
            ),
            default_confidence_threshold=_float(
                _value(source, "AUTO_REPLY_CONFIDENCE_THRESHOLD"),
                AUTO_REPLY_CONFIDENCE_THRESHOLD,
            ),
            safe_fallback_message=_value(
                source, "SAFE_FALLBACK_MESSAGE", DEFAULT_SAFE_FALLBACK_MESSAGE
            )
            or DEFAULT_SAFE_FALLBACK_MESSAGE,
            management_group_chat_id=int(management_chat) if management_chat else None,
            bootstrap_admin_username=_value(source, "BOOTSTRAP_ADMIN_USERNAME", "admin")
            or "admin",
            bootstrap_admin_password=_value(
                source,
                "BOOTSTRAP_ADMIN_PASSWORD",
                default_bootstrap_password,
            )
            or default_bootstrap_password,
        )

    @property
    def telegram_api_root(self) -> str:
        return f"{self.telegram_api_base}/bot{self.telegram_bot_token}"

    @property
    def is_production(self) -> bool:
        return _is_production_env(self.app_env)

    @property
    def has_safe_bootstrap_password(self) -> bool:
        password = self.bootstrap_admin_password or ""
        return len(password) >= 12 and password != "admin123"

    def is_configured(self) -> bool:
        return bool(
            self.telegram_bot_token
            and self.telegram_webhook_secret
            and self.supabase_rest_url
            and self.supabase_service_role_key
        )
