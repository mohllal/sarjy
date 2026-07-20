"""Tests for OpenWeatherClient."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from livekit.agents import utils
from livekit.agents.llm import ToolError

from integrations.openweather import OpenWeatherClient


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


def _session_for(*responses: _FakeResponse) -> MagicMock:
    session = MagicMock()
    session.get = MagicMock(side_effect=[response for response in responses])
    return session


@pytest.fixture
def client() -> OpenWeatherClient:
    return OpenWeatherClient("test-key")


async def test_resolve_location_success(client: OpenWeatherClient) -> None:
    geocode = _FakeResponse(
        status=200,
        payload=[{"name": "Amman", "lat": 31.95, "lon": 35.91, "country": "JO"}],
    )
    session = _session_for(geocode)

    with patch.object(utils.http_context, "http_session", return_value=session):
        result = await client.resolve_location("Amman")

    assert result["label"] == "Amman, JO"
    assert result["lat"] == 31.95


async def test_get_weather_current_success(client: OpenWeatherClient) -> None:
    geocode = _FakeResponse(
        status=200,
        payload=[{"name": "Amman", "lat": 31.95, "lon": 35.91, "country": "JO"}],
    )
    current = _FakeResponse(
        status=200,
        payload={
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 28.0, "feels_like": 29.0, "humidity": 35},
            "wind": {"speed": 2.5},
            "rain": {},
        },
    )
    session = _session_for(geocode, current)

    with patch.object(utils.http_context, "http_session", return_value=session):
        result = await client.get_weather("Amman")

    assert result["location"] == "Amman, JO"
    assert result["when"] == "current"
    assert result["temp_c"] == 28.0
    assert result["conditions"] == "clear sky"
    assert session.get.call_count == 2


async def test_get_weather_unknown_city(client: OpenWeatherClient) -> None:
    geocode = _FakeResponse(status=200, payload=[])
    session = _session_for(geocode)

    with patch.object(utils.http_context, "http_session", return_value=session):
        with pytest.raises(ToolError, match="couldn't find a place"):
            await client.get_weather("Narnia")


async def test_get_weather_rate_limited(client: OpenWeatherClient) -> None:
    geocode = _FakeResponse(
        status=200,
        payload=[{"name": "Amman", "lat": 31.95, "lon": 35.91, "country": "JO"}],
    )
    limited = _FakeResponse(status=429, text="rate limit")
    session = _session_for(geocode, limited)

    with patch.object(utils.http_context, "http_session", return_value=session):
        with pytest.raises(ToolError, match="rate-limited"):
            await client.get_weather("Amman")
