from __future__ import annotations

from app.repositories.base import SupabaseRepository


class AuditRepository(SupabaseRepository):
    async def log_audit(self, payload: dict) -> dict:
        result = await self.insert("audit_logs", payload)
        return result[0]

    async def list_audit_logs(self, filters: dict[str, str] | None = None, limit: int = 100) -> list[dict]:
        return await self.select(
            "audit_logs",
            filters=filters,
            order="created_at.desc",
            limit=limit,
        )

    async def log_command(self, payload: dict) -> dict:
        result = await self.insert("command_logs", payload)
        return result[0]

    async def log_error(self, payload: dict) -> dict:
        result = await self.insert("error_logs", payload)
        return result[0]

    async def claim_processed_update(self, update_id: int, update_hash: str | None = None) -> bool:
        return await self.rpc(
            "claim_processed_update",
            {"p_update_id": update_id, "p_update_hash": update_hash},
        )

    async def claim_management_report(self, report_type: str, window_start, window_end, chat_id: int):
        from app.utils.time import isoformat

        return await self.rpc(
            "claim_management_report",
            {
                "p_report_type": report_type,
                "p_window_start": isoformat(window_start),
                "p_window_end": isoformat(window_end),
                "p_chat_id": chat_id,
            },
        )

    async def mark_management_report_sent(
        self,
        report_id: str,
        message_text: str,
        success: bool,
        error_text: str | None = None,
    ) -> None:
        from app.utils.time import isoformat, utc_now

        payload = {
            "message_text": message_text,
            "is_success": success,
            "error_text": error_text,
        }
        if success:
            payload["sent_at"] = isoformat(utc_now())
        await self.update(
            "management_reports",
            payload,
            filters={"id": f"eq.{report_id}"},
        )
