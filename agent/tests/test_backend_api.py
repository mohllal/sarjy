"""Unit tests for BackendApiClient (mocked HTTP)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from livekit.agents import utils
from livekit.agents.llm import ToolError

from integrations.backend import BackendApiClient


class _FakeResponse:
    def __init__(self, *, status: int, payload: Any = None, text: str = "") -> None:
        self.status = status
        self._payload = payload
        self._text = text

    async def json(self) -> Any:
        return self._payload

    async def text(self) -> str:
        return self._text

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.fixture
def client() -> BackendApiClient:
    return BackendApiClient("http://backend:8000")


async def test_save_memory_success(client: BackendApiClient) -> None:
    response = _FakeResponse(
        status=200,
        payload={
            "username": "kareem",
            "memories": [
                {
                    "id": "1",
                    "username": "kareem",
                    "key": "favorite_color",
                    "value": "blue",
                    "created_at": "2026-07-19T00:00:00Z",
                    "updated_at": "2026-07-19T00:00:00Z",
                }
            ],
        },
    )
    session = MagicMock()
    session.request = MagicMock(return_value=response)

    with patch.object(utils.http_context, "http_session", return_value=session):
        result = await client.save_memory("kareem", "favorite_color", "blue")

    assert result["memories"][0]["value"] == "blue"
    args, kwargs = session.request.call_args
    assert args[0] == "PUT"
    assert args[1] == "http://backend:8000/memories/kareem"
    assert kwargs["json"] == {
        "facts": [{"key": "favorite_color", "value": "blue"}]
    }


async def test_save_memory_raises_tool_error_on_http_failure(
    client: BackendApiClient,
) -> None:
    response = _FakeResponse(status=500, text="boom")
    session = MagicMock()
    session.request = MagicMock(return_value=response)

    with patch.object(utils.http_context, "http_session", return_value=session):
        with pytest.raises(ToolError, match="Could not save that memory"):
            await client.save_memory("kareem", "favorite_color", "blue")


async def test_recall_memories_raises_tool_error_on_network_failure(
    client: BackendApiClient,
) -> None:
    session = MagicMock()
    session.request = MagicMock(side_effect=RuntimeError("connection refused"))

    with patch.object(utils.http_context, "http_session", return_value=session):
        with pytest.raises(ToolError, match="Could not recall memories"):
            await client.recall_memories("kareem")


async def test_list_messages_soft_fails_without_tool_error(
    client: BackendApiClient,
) -> None:
    session = MagicMock()
    session.request = MagicMock(side_effect=RuntimeError("down"))

    with patch.object(utils.http_context, "http_session", return_value=session):
        messages = await client.list_messages("kareem", limit=10)

    assert messages == []
