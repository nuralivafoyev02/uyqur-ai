from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import Settings


class RepositoryError(RuntimeError):
    pass


class SupabaseRepository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    async def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0)
        return self._client

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        client = await self.client()
        response = await client.request(method, url, params=params, json=json_body, headers=headers)
        if response.status_code >= 400:
            raise RepositoryError(
                f"Supabase request failed: {response.status_code} {response.text[:500]}"
            )
        return response

    async def select(
        self,
        table: str,
        *,
        select: str = "*",
        filters: dict[str, str] | None = None,
        order: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        single: bool = False,
    ) -> Any:
        params: dict[str, Any] = {"select": select}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        headers = self._headers()
        if single:
            headers["Accept"] = "application/vnd.pgrst.object+json"
        client = await self.client()
        response = await client.request(
            "GET",
            f"{self.settings.supabase_rest_url}/{table}",
            params=params,
            headers=headers,
        )
        if single and response.status_code == 406:
            return None
        if response.status_code >= 400:
            raise RepositoryError(
                f"Supabase request failed: {response.status_code} {response.text[:500]}"
            )
        return response.json()

    async def insert(
        self,
        table: str,
        payload: dict[str, Any] | list[dict[str, Any]],
        *,
        upsert: bool = False,
        on_conflict: str | None = None,
        returning: str = "representation",
    ) -> Any:
        prefer = f"return={returning}"
        if upsert:
            prefer = f"{prefer},resolution=merge-duplicates"
        params = {"on_conflict": on_conflict} if on_conflict else None
        response = await self._request(
            "POST",
            f"{self.settings.supabase_rest_url}/{table}",
            params=params,
            json_body=payload,
            headers=self._headers(prefer),
        )
        if returning == "minimal" or not response.text:
            return None
        return response.json()

    async def update(
        self,
        table: str,
        payload: dict[str, Any],
        *,
        filters: dict[str, str],
        returning: str = "representation",
    ) -> Any:
        response = await self._request(
            "PATCH",
            f"{self.settings.supabase_rest_url}/{table}",
            params=filters,
            json_body=payload,
            headers=self._headers(f"return={returning}"),
        )
        if returning == "minimal" or not response.text:
            return None
        return response.json()

    async def delete(self, table: str, *, filters: dict[str, str]) -> Any:
        response = await self._request(
            "DELETE",
            f"{self.settings.supabase_rest_url}/{table}",
            params=filters,
            headers=self._headers("return=representation"),
        )
        return response.json() if response.text else None

    async def rpc(self, function_name: str, payload: dict[str, Any]) -> Any:
        response = await self._request(
            "POST",
            f"{self.settings.supabase_rpc_url}/{function_name}",
            json_body=payload,
            headers=self._headers(),
        )
        return response.json() if response.text else None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
