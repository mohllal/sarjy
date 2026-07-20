"""Typed results and control exceptions for the Weekend Outing Planner."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LocationResult:
    city: str


@dataclass
class TimingResult:
    timing: str


@dataclass
class VibeResult:
    vibe: str


@dataclass
class ProposeResult:
    weather_summary: str
    proposal: str
    confirmed: bool


class OutingCancelled(Exception):
    """Raised when the user cancels the outing TaskGroup mid-flow."""

    def __init__(self, reason: str = "user cancelled") -> None:
        super().__init__(reason)
        self.reason = reason
