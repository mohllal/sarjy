"""Sarjy voice assistant and its function tools."""

from __future__ import annotations

import logging

from livekit.agents import Agent, ChatContext, RunContext, function_tool

from integrations.backend import BackendApiClient
from integrations.openweather import OpenWeatherClient
from prompts import load_prompt
from schemas.outing import OutingCancelled, ProposeResult
from schemas.session import SessionData
from settings import Settings
from workflows.outing import build_outing_task_group

logger = logging.getLogger("sarjy.assistants")


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

    @function_tool()
    async def plan_weekend_outing(self, context: RunContext[SessionData]) -> str:
        """Start the weekend outing planner multistep flow.

        Call when the user asks to plan a weekend outing or similar
        (plan my weekend, help me plan an outing, what should I do this weekend).
        """
        outing = context.userdata.outing
        outing.status = "in_progress"
        outing.city = None
        outing.timing = None
        outing.vibe = None
        outing.weather_summary = None
        outing.proposal = None

        group = build_outing_task_group(
            weather=self._weather,
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True),
            userdata=context.userdata,
        )

        try:
            results = await group
        except OutingCancelled as exc:
            outing.status = "cancelled"
            logger.info("outing planner cancelled: %s", exc.reason)
            return "Outing planning cancelled. Back to normal chat."

        task_results = results.task_results
        propose = task_results.get("propose")
        if isinstance(propose, ProposeResult) and propose.confirmed:
            summary = (
                f"Outing in {outing.city} ({outing.timing}, {outing.vibe}): "
                f"{propose.proposal} Weather: {propose.weather_summary}"
            )
            try:
                await self._backend.save_memory(
                    context.userdata.username,
                    "last_outing_plan",
                    summary,
                )
            except Exception:  # noqa: BLE001
                logger.warning("failed to persist last_outing_plan", exc_info=True)

            return (
                f"Outing confirmed for {outing.city}. "
                f"{propose.proposal} "
                "Saved as last_outing_plan for later."
            )

        return "Outing planner finished without a confirmed proposal."
