"""Sarjy voice assistant and its function tools."""

from __future__ import annotations

from livekit.agents import Agent, ChatContext, RunContext, function_tool

from integrations.backend import BackendApiClient
from integrations.openweather import OpenWeatherClient
from prompts import load_prompt
from schemas.session import SessionData
from settings import Settings


class SarjyAssistant(Agent):
    def __init__(
        self,
        *,
        backend: BackendApiClient,
        weather: OpenWeatherClient,
        settings: Settings,
        chat_ctx: ChatContext | None = None,
    ) -> None:
        self._backend = backend
        self._weather = weather
        kwargs: dict = {
            "instructions": load_prompt("system", settings.system_prompt_version),
        }
        if chat_ctx is not None:
            kwargs["chat_ctx"] = chat_ctx
        super().__init__(**kwargs)

    @function_tool()
    async def save_memory(
        self,
        context: RunContext[SessionData],
        key: str,
        value: str,
    ) -> str:
        """Save a durable fact about the current user.

        Use when the user states a lasting preference or personal detail
        (favorite color, home city, nickname, etc.).

        Args:
            key: Short descriptive label for the fact (e.g. favorite_color).
            value: The fact to remember.
        """
        context.disallow_interruptions()
        username = context.userdata.username
        await self._backend.save_memory(username, key.strip(), value.strip())
        return f"Saved {key} for later."

    @function_tool()
    async def recall_memories(self, context: RunContext[SessionData]) -> dict:
        """Recall all saved facts about the current user.

        Call this whenever the user asks about something you may have stored.
        Returns the full list — match the relevant fact by meaning, do not guess.
        """
        username = context.userdata.username
        memories = await self._backend.recall_memories(username)
        return {"memories": memories}

    @function_tool()
    async def get_weather(
        self,
        context: RunContext[SessionData],
        location: str,
        when: str | None = None,
    ) -> dict:
        """Look up weather for a city or place.

        Use for current conditions or a near-term forecast.

        Args:
            location: City or place name (e.g. Amman, Cairo, Paris France).
            when: Optional timing hint such as tomorrow morning or Saturday
                afternoon. Omit for current conditions.
        """
        return await self._weather.get_weather(location, when)
