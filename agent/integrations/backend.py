"""HTTP client for the Sarjy FastAPI backend (memories + conversations)."""

from __future__ import annotations

import logging
from typing import Any

from livekit.agents import utils
from livekit.agents.llm import ToolError

logger = logging.getLogger("sarjy.integrations.backend")


class BackendApiClient:
    """Thin wrapper around Sarjy FastAPI persistence endpoints."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def save_memory(self, username: str, key: str, value: str) -> dict[str, Any]:
        payload = {"facts": [{"key": key, "value": value}]}
        return await self._request(
            "PUT",
            f"/memories/{username}",
            json=payload,
            error_message="Could not save that memory right now.",
        )

    async def recall_memories(self, username: str) -> list[dict[str, str]]:
        data = await self._request(
            "GET",
            f"/memories/{username}",
            error_message="Could not recall memories right now.",
        )
        return [{"key": item["key"], "value": item["value"]} for item in data.get("memories", [])]

    async def list_messages(
        self,
        username: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, str]]:
        data = await self._request(
            "GET",
            f"/conversations/{username}/messages",
            params={"limit": limit},
            error_message="Could not load conversation history.",
            raise_tool_error=False,
        )
        if data is None:
            return []
        return [
            {"role": item["role"], "content": item["content"]} for item in data.get("messages", [])
        ]

    async def append_message(
        self,
        username: str,
        role: str,
        content: str,
    ) -> None:
        await self._request(
            "POST",
            f"/conversations/{username}/messages",
            json={"messages": [{"role": role, "content": content}]},
            error_message="Could not persist conversation turn.",
            raise_tool_error=False,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        error_message: str,
        raise_tool_error: bool = True,
    ) -> Any:
        url = f"{self._base_url}{path}"
        session = utils.http_context.http_session()
        try:
            async with session.request(
                method,
                url,
                json=json,
                params=params,
            ) as response:
                if response.status >= 400:
                    body = await response.text()
                    logger.warning(
                        "backend api %s %s failed status=%s body=%s",
                        method,
                        path,
                        response.status,
                        body[:200],
                    )
                    if raise_tool_error:
                        raise ToolError(error_message)
                    return None
                if response.status == 204:
                    return None
                return await response.json()
        except ToolError:
            raise
        except Exception as exc:  # noqa: BLE001 — surface as tool/log failure
            logger.warning("backend api %s %s error: %s", method, path, exc)
            if raise_tool_error:
                raise ToolError(error_message) from exc
            return None
