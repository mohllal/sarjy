"""Shared fixtures for agent behavioral tests."""

from __future__ import annotations

import pytest

from assistants.sarjy import SarjyAssistant
from integrations.backend import BackendApiClient
from integrations.openweather import OpenWeatherClient
from settings import Settings, get_settings


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def assistant(settings: Settings) -> SarjyAssistant:
    return SarjyAssistant(
        backend=BackendApiClient("http://localhost:8000"),
        weather=OpenWeatherClient(settings.openweather_api_key),
        settings=settings,
    )
