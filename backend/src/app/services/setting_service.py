from __future__ import annotations

from app.config import Settings
from app.constants import (
    AUTO_REPLY_CONFIDENCE_THRESHOLD,
    AUTO_REPLY_DELAY_MINUTES,
    BOT_CONTROL_SETTINGS,
    DEFAULT_SAFE_FALLBACK_MESSAGE,
    DEFAULT_TIMEZONE,
    TICKET_MERGE_WINDOW_MINUTES,
    TICKET_REOPEN_WINDOW_MINUTES,
)
from app.repositories.setting_repository import SettingRepository


class SettingService:
    def __init__(self, repository: SettingRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def get_runtime_settings(self) -> dict[str, object]:
        stored = await self.repository.get_all()
        merged: dict[str, object] = {
            "auto_reply_enabled": True,
            "management_hourly_digest_enabled": True,
            "management_daily_summary_enabled": True,
            "management_alert_on_sla_breach": True,
            "auto_reply_delay_minutes": self.settings.auto_reply_delay_minutes
            or AUTO_REPLY_DELAY_MINUTES,
            "response_merge_window_minutes": self.settings.ticket_merge_window_minutes
            or TICKET_MERGE_WINDOW_MINUTES,
            "reopen_window_minutes": self.settings.ticket_reopen_window_minutes
            or TICKET_REOPEN_WINDOW_MINUTES,
            "auto_reply_confidence_threshold": self.settings.default_confidence_threshold
            or AUTO_REPLY_CONFIDENCE_THRESHOLD,
            "safe_fallback_message": self.settings.safe_fallback_message
            or DEFAULT_SAFE_FALLBACK_MESSAGE,
            "default_language": "uz",
            "timezone": self.settings.app_timezone or DEFAULT_TIMEZONE,
            "hourly_digest_cron": "0 * * * *",
            "daily_summary_cron": "0 19 * * *",
            "management_group_chat_id": self.settings.management_group_chat_id,
        }
        merged.update(stored)
        return merged

    async def patch_settings(self, values: dict[str, object], admin_user_id: str | None = None) -> dict[str, object]:
        unknown = set(values) - BOT_CONTROL_SETTINGS
        if unknown:
            raise ValueError(f"Noma'lum sozlama kalitlari: {', '.join(sorted(unknown))}")
        await self.repository.set_values(values, admin_user_id=admin_user_id)
        return await self.get_runtime_settings()
