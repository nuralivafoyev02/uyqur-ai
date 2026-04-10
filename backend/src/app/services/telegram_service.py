from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings


class TelegramService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    async def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0)
        return self._client

    async def _call(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.settings.telegram_bot_token:
            raise RuntimeError("Telegram token sozlanmagan")
        client = await self.client()
        response = await client.post(f"{self.settings.telegram_api_root}/{method}", json=payload or {})
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API xatosi: {data}")
        return data["result"]

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
        thread_id: int | None = None,
        disable_notification: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
        }
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if thread_id is not None:
            payload["message_thread_id"] = thread_id
        return await self._call("sendMessage", payload)

    async def get_webhook_info(self) -> dict[str, Any]:
        return await self._call("getWebhookInfo")

    async def get_me(self) -> dict[str, Any]:
        return await self._call("getMe")

    async def set_webhook(self, webhook_url: str) -> dict[str, Any]:
        return await self._call(
            "setWebhook",
            {
                "url": webhook_url,
                "secret_token": self.settings.telegram_webhook_secret,
                "allowed_updates": ["message", "edited_message"],
            },
        )
