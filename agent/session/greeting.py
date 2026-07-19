"""Build the first-turn greeting instructions for a session."""

from __future__ import annotations

from prompts import load_prompt


def greeting_instructions(username: str, version: str) -> str:
    """Return spoken-turn instructions for the session greeting.

    Named users get a personalized prompt; auto-generated guest usernames
    (and empty names) use the guest prompt.
    """
    if username and not username.startswith("guest-"):
        return load_prompt(
            "greeting",
            version,
            variables={"username": username},
        )
    return load_prompt("greeting_guest", version)
