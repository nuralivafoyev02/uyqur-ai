from __future__ import annotations

from app.repositories.base import SupabaseRepository
from app.utils.time import isoformat, utc_now


class AdminRepository(SupabaseRepository):
    async def get_user_by_username(self, username: str) -> dict | None:
        return await self.select(
            "admin_users",
            filters={"username_normalized": f"eq.{username.lower()}", "is_active": "eq.true"},
            single=True,
        )

    async def get_user_by_id(self, user_id: str) -> dict | None:
        return await self.select(
            "admin_users",
            filters={"id": f"eq.{user_id}", "is_active": "eq.true"},
            single=True,
        )

    async def create_user(self, payload: dict) -> dict:
        result = await self.insert("admin_users", payload)
        return result[0]

    async def update_user(self, user_id: str, payload: dict) -> dict:
        result = await self.update("admin_users", payload, filters={"id": f"eq.{user_id}"})
        return result[0]

    async def create_session(self, payload: dict) -> dict:
        result = await self.insert("admin_sessions", payload)
        return result[0]

    async def get_session(self, token_hash: str) -> dict | None:
        return await self.select(
            "admin_sessions",
            select="*,admin_users(*)",
            filters={
                "token_hash": f"eq.{token_hash}",
                "revoked_at": "is.null",
            },
            single=True,
        )

    async def revoke_session(self, session_id: str) -> list[dict]:
        return await self.update(
            "admin_sessions",
            {"revoked_at": isoformat(utc_now())},
            filters={"id": f"eq.{session_id}"},
        )

    async def revoke_other_sessions(self, user_id: str, except_session_id: str | None = None) -> None:
        filters = {"admin_user_id": f"eq.{user_id}", "revoked_at": "is.null"}
        if except_session_id:
            filters["id"] = f"neq.{except_session_id}"
        await self.update(
            "admin_sessions",
            {"revoked_at": isoformat(utc_now())},
            filters=filters,
        )

    async def touch_session(self, session_id: str, expires_at) -> dict:
        result = await self.update(
            "admin_sessions",
            {"last_seen_at": isoformat(utc_now()), "expires_at": isoformat(expires_at)},
            filters={"id": f"eq.{session_id}"},
        )
        return result[0]

    async def auth_rate_limit_hit(self, key: str) -> list[dict]:
        return await self.rpc("auth_rate_limit_hit", {"p_key": key})

    async def auth_rate_limit_fail(self, key: str) -> list[dict]:
        return await self.rpc("auth_rate_limit_fail", {"p_key": key})

    async def auth_rate_limit_reset(self, key: str) -> None:
        await self.delete("auth_rate_limits", filters={"key": f"eq.{key}"})

    async def expire_sessions(self) -> int:
        return await self.rpc("expire_admin_sessions", {})
