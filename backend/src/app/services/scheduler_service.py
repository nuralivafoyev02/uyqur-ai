from __future__ import annotations

from app.services.auth_service import AuthService
from app.services.auto_reply_service import AutoReplyService
from app.services.management_service import ManagementService


class SchedulerService:
    def __init__(
        self,
        auto_reply_service: AutoReplyService,
        management_service: ManagementService,
        auth_service: AuthService,
    ):
        self.auto_reply_service = auto_reply_service
        self.management_service = management_service
        self.auth_service = auth_service

    async def run_for_cron(self, cron: str | None) -> dict:
        result = {
            "cron": cron,
            "auto_reply": await self.auto_reply_service.run_due_auto_replies(),
            "expired_sessions": await self.auth_service.expire_sessions(),
        }
        if cron == "0 * * * *":
            result["hourly"] = await self.management_service.send_hourly_digest()
        if cron == "0 19 * * *":
            result["daily"] = await self.management_service.send_daily_summary()
        return result
