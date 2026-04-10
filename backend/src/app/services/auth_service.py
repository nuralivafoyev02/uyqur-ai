from __future__ import annotations

from datetime import timedelta

from app.config import Settings
from app.constants import LOGIN_RATE_LIMIT_ATTEMPTS, LOGIN_RATE_LIMIT_WINDOW_MINUTES
from app.models.enums import AuditAction, ActorType
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService
from app.utils.security import digest_token, generate_session_token, hash_password, verify_password
from app.utils.time import isoformat, parse_datetime, utc_now


class AuthError(RuntimeError):
    pass


class AuthService:
    def __init__(self, repository: AdminRepository, settings: Settings, audit_service: AuditService):
        self.repository = repository
        self.settings = settings
        self.audit_service = audit_service

    def _ensure_production_bootstrap_password(self) -> None:
        if self.settings.is_production and not self.settings.has_safe_bootstrap_password:
            raise AuthError(
                "Production muhitida BOOTSTRAP_ADMIN_PASSWORD kamida 12 belgili va default bo'lmagan qiymat bo'lishi kerak."
            )

    async def ensure_bootstrap_admin(self) -> dict:
        existing = await self.repository.get_user_by_username(self.settings.bootstrap_admin_username)
        if existing:
            return existing
        self._ensure_production_bootstrap_password()
        return await self.repository.create_user(
            {
                "username": self.settings.bootstrap_admin_username,
                "display_name": "System Administrator",
                "password_hash": hash_password(
                    self.settings.bootstrap_admin_password,
                    self.settings.password_hash_iterations,
                ),
                "must_change_password": True,
                "is_bootstrap": True,
                "is_active": True,
            }
        )

    async def _guard_rate_limit(self, rate_key: str) -> None:
        rows = await self.repository.auth_rate_limit_hit(rate_key)
        if not rows:
            return
        state = rows[0]
        blocked_until = parse_datetime(state.get("blocked_until"))
        if blocked_until and blocked_until > utc_now():
            raise AuthError("Juda ko'p urinish. Birozdan keyin qayta urinib ko'ring.")

    async def login(self, username: str, password: str, ip_address: str | None, user_agent: str | None):
        await self.ensure_bootstrap_admin()
        rate_key = f"{(ip_address or 'unknown').strip()}:{username.lower()}"
        await self._guard_rate_limit(rate_key)
        user = await self.repository.get_user_by_username(username)
        if not user or not verify_password(password, user["password_hash"]):
            await self.repository.auth_rate_limit_fail(rate_key)
            await self.audit_service.log(
                actor_type=ActorType.SYSTEM,
                actor_id=None,
                action=AuditAction.LOGIN_FAILED.value,
                entity_type="admin_user",
                entity_id=user["id"] if user else None,
                metadata={"username": username},
                ip_address=ip_address,
            )
            raise AuthError("Login yoki parol noto'g'ri.")
        await self.repository.auth_rate_limit_reset(rate_key)
        token = generate_session_token(self.settings.session_ttl_hours)
        session = await self.repository.create_session(
            {
                "admin_user_id": user["id"],
                "token_hash": token.digest,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "expires_at": isoformat(token.expires_at),
            }
        )
        await self.repository.update_user(user["id"], {"last_login_at": isoformat(utc_now())})
        await self.audit_service.log(
            actor_type=ActorType.ADMIN,
            actor_id=user["id"],
            action=AuditAction.LOGIN.value,
            entity_type="session",
            entity_id=session["id"],
            metadata={"username": user["username"]},
            ip_address=ip_address,
        )
        user["must_change_password"] = bool(user["must_change_password"])
        return {"token": token.raw, "session": session, "user": user, "expires_at": token.expires_at}

    async def get_session(self, raw_token: str | None) -> dict | None:
        if not raw_token:
            return None
        session = await self.repository.get_session(digest_token(raw_token))
        if not session:
            return None
        expires_at = parse_datetime(session.get("expires_at"))
        if expires_at and expires_at <= utc_now():
            await self.repository.revoke_session(session["id"])
            return None
        new_expiry = utc_now() + timedelta(hours=self.settings.session_ttl_hours)
        await self.repository.touch_session(session["id"], new_expiry)
        session["expires_at"] = isoformat(new_expiry)
        return session

    async def logout(self, raw_token: str | None) -> None:
        session = await self.get_session(raw_token)
        if not session:
            return
        await self.repository.revoke_session(session["id"])
        await self.audit_service.log(
            actor_type=ActorType.ADMIN,
            actor_id=session["admin_user_id"],
            action=AuditAction.LOGOUT.value,
            entity_type="session",
            entity_id=session["id"],
            metadata={},
        )

    async def change_password(
        self,
        *,
        user_id: str,
        current_password: str,
        new_password: str,
        session_id: str | None = None,
    ) -> dict:
        user = await self.repository.get_user_by_id(user_id)
        if not user or not verify_password(current_password, user["password_hash"]):
            raise AuthError("Joriy parol noto'g'ri.")
        if new_password == current_password:
            raise AuthError("Yangi parol joriy parol bilan bir xil bo'lmasligi kerak.")
        if len(new_password) < 12:
            raise AuthError("Yangi parol kamida 12 belgidan iborat bo'lishi kerak.")
        updated = await self.repository.update_user(
            user_id,
            {
                "password_hash": hash_password(new_password, self.settings.password_hash_iterations),
                "must_change_password": False,
            },
        )
        await self.repository.revoke_other_sessions(user_id, except_session_id=session_id)
        await self.audit_service.log(
            actor_type=ActorType.ADMIN,
            actor_id=user_id,
            action=AuditAction.PASSWORD_CHANGED.value,
            entity_type="admin_user",
            entity_id=user_id,
            metadata={},
        )
        return updated

    async def expire_sessions(self) -> int:
        return await self.repository.expire_sessions()
