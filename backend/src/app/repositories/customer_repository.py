from __future__ import annotations

from app.repositories.base import SupabaseRepository


class CustomerRepository(SupabaseRepository):
    async def upsert_customer(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        full_name: str,
        language: str = "uz",
    ) -> dict:
        result = await self.insert(
            "customers",
            [
                {
                    "telegram_user_id": telegram_user_id,
                    "username": username,
                    "full_name": full_name,
                    "language": language,
                }
            ],
            upsert=True,
            on_conflict="telegram_user_id",
        )
        return result[0]
