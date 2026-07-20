"""Build the Weekend Outing Planner TaskGroup."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from livekit.agents import llm
from livekit.agents.beta.workflows import TaskCompletedEvent, TaskGroup

from integrations.openweather import OpenWeatherClient
from schemas.outing import (
    LocationResult,
    ProposeResult,
    TimingResult,
    VibeResult,
)
from schemas.session import SessionData
from workflows.outing.tasks import (
    LocationTask,
    ProposeOutingTask,
    TimingTask,
    VibeTask,
)

OnTaskCompleted = Callable[[TaskCompletedEvent], Awaitable[None]]


def build_outing_task_group(
    *,
    weather: OpenWeatherClient,
    chat_ctx: llm.ChatContext | None = None,
    userdata: SessionData | None = None,
    summarize_chat_ctx: bool = True,
    on_task_completed: OnTaskCompleted | None = None,
) -> TaskGroup:
    """Ordered location → timing → vibe → weather+propose TaskGroup."""

    async def _on_task_completed(event: TaskCompletedEvent) -> None:
        if userdata is not None:
            outing = userdata.outing
            result = event.result
            if event.task_id == "location" and isinstance(result, LocationResult):
                outing.city = result.city
            elif event.task_id == "timing" and isinstance(result, TimingResult):
                outing.timing = result.timing
            elif event.task_id == "vibe" and isinstance(result, VibeResult):
                outing.vibe = result.vibe
            elif event.task_id == "propose" and isinstance(result, ProposeResult):
                outing.weather_summary = result.weather_summary
                outing.proposal = result.proposal
                outing.status = "completed"

        if on_task_completed is not None:
            await on_task_completed(event)

    kwargs: dict = {
        "summarize_chat_ctx": summarize_chat_ctx,
        "on_task_completed": _on_task_completed,
    }
    if chat_ctx is not None:
        kwargs["chat_ctx"] = chat_ctx

    group = TaskGroup(**kwargs)
    group.add(
        lambda: LocationTask(weather=weather),
        id="location",
        description="Collect and resolve the city or area for the outing",
    )
    group.add(
        lambda: TimingTask(),
        id="timing",
        description="Collect weekend day-part timing (e.g. Saturday morning)",
    )
    group.add(
        lambda: VibeTask(),
        id="vibe",
        description="Collect activity vibe: outdoor, indoor, food, or flexible",
    )
    group.add(
        lambda: ProposeOutingTask(weather=weather),
        id="propose",
        description="Check weather and propose outing options for confirmation",
    )
    return group
