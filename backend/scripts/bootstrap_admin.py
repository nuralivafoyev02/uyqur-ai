from __future__ import annotations

import argparse
import asyncio

from app.config import Settings
from app.repositories.admin_repository import AdminRepository
from app.utils.security import hash_password


async def bootstrap(username: str, password: str, display_name: str) -> None:
    settings = Settings.from_env()
    password = password or settings.bootstrap_admin_password
    if settings.is_production and not settings.has_safe_bootstrap_password and password == settings.bootstrap_admin_password:
        raise SystemExit(
            "Production uchun BOOTSTRAP_ADMIN_PASSWORD yoki --password orqali kamida 12 belgili kuchli parol bering."
        )
    repository = AdminRepository(settings)
    existing = await repository.get_user_by_username(username)
    payload = {
        "username": username,
        "display_name": display_name,
        "password_hash": hash_password(password, settings.password_hash_iterations),
        "must_change_password": True,
        "is_bootstrap": True,
        "is_active": True,
    }
    if existing:
        await repository.update_user(existing["id"], payload)
        print(f"Bootstrap admin yangilandi: {username}")
    else:
        await repository.create_user(payload)
        print(f"Bootstrap admin yaratildi: {username}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or refresh the bootstrap admin user.")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=None)
    parser.add_argument("--display-name", default="System Administrator")
    args = parser.parse_args()
    asyncio.run(bootstrap(args.username, args.password, args.display_name))


if __name__ == "__main__":
    main()
