"""Typed userdata carried on AgentSession."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OutingPlanState:
    """In-progress / completed Weekend Outing Planner fields.

    Status is one of: idle | in_progress | completed | cancelled.
    """

    city: str | None = None
    timing: str | None = None
    vibe: str | None = None
    weather_summary: str | None = None
    proposal: str | None = None
    status: str = "idle"


@dataclass
class SessionData:
    """Typed userdata carried on AgentSession."""

    username: str
    outing: OutingPlanState = field(default_factory=OutingPlanState)
