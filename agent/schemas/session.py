"""Typed userdata carried on AgentSession."""

from dataclasses import dataclass


@dataclass
class SessionData:
    """Typed userdata carried on AgentSession."""

    username: str
