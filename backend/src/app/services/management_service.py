from __future__ import annotations

from app.models.enums import ReportType
from app.repositories.audit_repository import AuditRepository
from app.services.setting_service import SettingService
from app.services.stats_service import StatsService
from app.services.telegram_service import TelegramService
from app.utils.time import utc_now


class ManagementService:
    def __init__(
        self,
        settings_service: SettingService,
        stats_service: StatsService,
        telegram_service: TelegramService,
        audit_repository: AuditRepository,
    ):
        self.settings_service = settings_service
        self.stats_service = stats_service
        self.telegram_service = telegram_service
        self.audit_repository = audit_repository

    async def _send_summary(self, report_type: ReportType, from_at, to_at, label: str) -> dict:
        runtime = await self.settings_service.get_runtime_settings()
        chat_id = runtime.get("management_group_chat_id")
        if not chat_id:
            return {"sent": False, "reason": "management_group_not_configured"}
        claim_id = await self.audit_repository.claim_management_report(
            report_type.value,
            from_at,
            to_at,
            int(chat_id),
        )
        if not claim_id:
            return {"sent": False, "reason": "duplicate"}
        summary = await self.stats_service.management_summary_payload(from_at, to_at)
        text = self.stats_service.render_overview_text(label, summary)
        try:
            await self.telegram_service.send_message(chat_id=int(chat_id), text=text)
            await self.audit_repository.mark_management_report_sent(
                report_id=claim_id,
                message_text=text,
                success=True,
            )
            return {"sent": True, "report_id": claim_id, "text": text}
        except Exception as exc:
            await self.audit_repository.mark_management_report_sent(
                report_id=claim_id,
                message_text=text,
                success=False,
                error_text=str(exc),
            )
            raise

    async def send_hourly_digest(self) -> dict:
        from_at, to_at = self.stats_service.previous_hour_window()
        return await self._send_summary(ReportType.HOURLY, from_at, to_at, "Soatlik hisobot")

    async def send_daily_summary(self) -> dict:
        runtime = await self.settings_service.get_runtime_settings()
        from_at, to_at = self.stats_service.previous_day_window(str(runtime.get("timezone", "Asia/Tashkent")))
        return await self._send_summary(ReportType.DAILY, from_at, to_at, "Kunlik hisobot")

    async def send_alert(self, text: str) -> dict:
        runtime = await self.settings_service.get_runtime_settings()
        chat_id = runtime.get("management_group_chat_id")
        if not chat_id:
            return {"sent": False, "reason": "management_group_not_configured"}
        minute = utc_now().replace(second=0, microsecond=0)
        claim_id = await self.audit_repository.claim_management_report(
            ReportType.ALERT.value,
            minute,
            minute,
            int(chat_id),
        )
        if not claim_id:
            return {"sent": False, "reason": "duplicate"}
        await self.telegram_service.send_message(chat_id=int(chat_id), text=text)
        await self.audit_repository.mark_management_report_sent(
            report_id=claim_id,
            message_text=text,
            success=True,
        )
        return {"sent": True, "report_id": claim_id}

    async def send_test_summary(self) -> dict:
        runtime = await self.settings_service.get_runtime_settings()
        from_at, to_at = self.stats_service.resolve_window("today", str(runtime.get("timezone", "Asia/Tashkent")))
        return await self._send_summary(ReportType.ALERT, from_at, to_at, "Test boshqaruv hisobot")
