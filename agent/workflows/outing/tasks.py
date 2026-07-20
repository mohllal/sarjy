"""AgentTask steps for the Weekend Outing Planner."""

from __future__ import annotations

from typing import Generic, TypeVar

from livekit.agents import AgentTask, RunContext, function_tool

from integrations.openweather import OpenWeatherClient
from prompts import load_prompt
from schemas.outing import (
    LocationResult,
    OutingCancelled,
    ProposeResult,
    TimingResult,
    VibeResult,
)
from schemas.session import SessionData

T = TypeVar("T")

_VIBES = frozenset({"outdoor", "indoor", "food", "flexible"})


class CancellableOutingTask(AgentTask[T], Generic[T]):
    """Shared cancel path for outing steps."""

    @function_tool()
    async def cancel_outing(self, context: RunContext[SessionData]) -> None:
        """Call when the user wants to stop planning (never mind, cancel, stop)."""
        context.userdata.outing.status = "cancelled"
        await self.session.generate_reply(
            instructions=(
                "Briefly acknowledge that you are cancelling the outing plan "
                "and returning to normal chat. Do not ask further outing questions."
            ),
        )
        self.complete(OutingCancelled("user cancelled"))


class LocationTask(CancellableOutingTask[LocationResult]):
    """Collect and resolve the outing city / area."""

    def __init__(self, *, weather: OpenWeatherClient) -> None:
        self._weather = weather
        super().__init__(instructions=load_prompt("outing_location", "1.0.0"))

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Ask which city or area they want the weekend outing in. "
                "Keep it to one short question."
            ),
        )

    @function_tool()
    async def record_location(
        self,
        context: RunContext[SessionData],
        city: str,
    ) -> None:
        """Record the outing location after the user names a city or area.

        Resolves the place via geocoding before completing this step.

        Args:
            city: City or area the user named (e.g. Amman, Cairo).
        """
        resolved = await self._weather.resolve_location(city)
        label = str(resolved["label"])
        context.userdata.outing.city = label
        self.complete(LocationResult(city=label))


class TimingTask(CancellableOutingTask[TimingResult]):
    """Collect weekend day-part preference."""

    def __init__(self) -> None:
        super().__init__(instructions=load_prompt("outing_timing", "1.0.0"))

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Ask which part of the weekend they prefer "
                "(for example Saturday morning or Sunday afternoon). "
                "One short question only."
            ),
        )

    @function_tool()
    async def record_timing(
        self,
        context: RunContext[SessionData],
        timing: str,
    ) -> None:
        """Record the weekend timing preference.

        Args:
            timing: Day part such as Saturday morning or Sunday afternoon.
        """
        cleaned = timing.strip()
        context.userdata.outing.timing = cleaned
        self.complete(TimingResult(timing=cleaned))


class VibeTask(CancellableOutingTask[VibeResult]):
    """Collect outdoor / indoor / food / flexible preference."""

    def __init__(self) -> None:
        super().__init__(instructions=load_prompt("outing_vibe", "1.0.0"))

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Ask whether they want outdoor, indoor, food-focused, or flexible. "
                "One short question only."
            ),
        )

    @function_tool()
    async def record_vibe(
        self,
        context: RunContext[SessionData],
        vibe: str,
    ) -> None:
        """Record the activity vibe preference.

        Args:
            vibe: One of outdoor, indoor, food, or flexible.
        """
        cleaned = vibe.strip().lower()
        if cleaned not in _VIBES:
            # Soft-normalize common synonyms so we do not stall the flow.
            if "out" in cleaned:
                cleaned = "outdoor"
            elif "in" in cleaned:
                cleaned = "indoor"
            elif "eat" in cleaned or "restaurant" in cleaned or "cafe" in cleaned:
                cleaned = "food"
            else:
                cleaned = "flexible"
        context.userdata.outing.vibe = cleaned
        self.complete(VibeResult(vibe=cleaned))


class ProposeOutingTask(CancellableOutingTask[ProposeResult]):
    """Fetch weather, propose 1–2 outings, confirm with the user."""

    def __init__(self, *, weather: OpenWeatherClient) -> None:
        self._weather = weather
        super().__init__(instructions=load_prompt("outing_propose", "1.0.0"))

    async def on_enter(self) -> None:
        outing = self.session.userdata.outing
        await self.session.generate_reply(
            instructions=(
                f"They chose {outing.city} for {outing.timing}, vibe {outing.vibe}. "
                "Call get_weather for that city with when set to their timing, "
                "then propose one or two concrete outing options that fit the vibe "
                "and weather. Ask if they want to confirm or revise."
            ),
        )

    @function_tool()
    async def get_weather(
        self,
        context: RunContext[SessionData],
        location: str,
        when: str | None = None,
    ) -> dict:
        """Look up weather for the outing city and timing.

        Args:
            location: City already collected for the outing.
            when: Timing hint such as Saturday afternoon.
        """
        return await self._weather.get_weather(location, when)

    @function_tool()
    async def confirm_outing(
        self,
        context: RunContext[SessionData],
        weather_summary: str,
        proposal: str,
    ) -> None:
        """Call when the user confirms the outing proposal (or accepts a revision).

        Args:
            weather_summary: Short spoken-friendly weather summary used in the pitch.
            proposal: The confirmed outing idea(s) in one or two sentences.
        """
        outing = context.userdata.outing
        outing.weather_summary = weather_summary.strip()
        outing.proposal = proposal.strip()
        outing.status = "completed"
        self.complete(
            ProposeResult(
                weather_summary=outing.weather_summary,
                proposal=outing.proposal,
                confirmed=True,
            )
        )
