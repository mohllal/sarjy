"""Tests for session greeting via generate_reply."""

from __future__ import annotations

from livekit.agents import AgentSession, RunResult, inference

from assistants.sarjy import SarjyAssistant
from schemas.session import SessionData
from session.greeting import greeting_instructions
from settings import Settings


def _run_instructions(session: AgentSession, instructions: str) -> RunResult:
    """Capture a generate_reply(instructions=...) turn the way session.run captures user turns."""
    if session._global_run_state is not None and not session._global_run_state.done():
        raise RuntimeError("nested runs are not supported")

    run_state = RunResult(output_type=None, session=session)
    session._global_run_state = run_state
    session.generate_reply(instructions=instructions)
    return run_state


def test_greeting_instructions_named_user() -> None:
    text = greeting_instructions("kareem", "1.0.0")
    assert "kareem" in text
    assert "Greet" in text


def test_greeting_instructions_guest_user() -> None:
    text = greeting_instructions("guest-abc123", "1.0.0")
    assert "guest-" not in text
    assert "{username}" not in text
    assert "Greet" in text


def test_greeting_instructions_empty_uses_guest() -> None:
    text = greeting_instructions("", "1.0.0")
    assert "{username}" not in text
    assert "Greet" in text


async def test_named_user_greeting_mentions_name(
    settings: Settings,
    assistant: SarjyAssistant,
) -> None:
    async with (
        inference.LLM(
            model="google/gemma-4-31b-it",
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        ) as llm,
        AgentSession(llm=llm, userdata=SessionData(username="kareem")) as session,
    ):
        await session.start(assistant)

        result = await _run_instructions(
            session,
            greeting_instructions("kareem", settings.greeting_prompt_version),
        )

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Greets the user by name (kareem) briefly and offers to help. "
                    "Does not ask for the user's name."
                ),
            )
        )
        result.expect.no_more_events()


async def test_guest_user_greeting_is_generic(
    settings: Settings,
    assistant: SarjyAssistant,
) -> None:
    async with (
        inference.LLM(
            model="google/gemma-4-31b-it",
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        ) as llm,
        AgentSession(
            llm=llm,
            userdata=SessionData(username="guest-abc123"),
        ) as session,
    ):
        await session.start(assistant)

        result = await _run_instructions(
            session,
            greeting_instructions(
                "guest-abc123",
                settings.greeting_prompt_version,
            ),
        )

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Greets the user briefly and offers to help. "
                    "Does not address them as guest-abc123 or any guest- id."
                ),
            )
        )
        result.expect.no_more_events()
