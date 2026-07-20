"""Tests for save_memory tool invocation."""

from __future__ import annotations

import json

from livekit.agents import AgentSession, inference, mock_tools

from assistants.sarjy import SarjyAssistant
from schemas.session import SessionData
from settings import Settings


def _mock_save_memory(context, key: str, value: str) -> str:
    _ = context
    return f"Saved {key}={value} for later."


async def test_preference_statement_calls_save_memory(
    settings: Settings,
    assistant: SarjyAssistant,
) -> None:
    async with (
        inference.LLM(
            model="google/gemma-4-31b-it",
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        ) as llm,
        AgentSession(llm=llm, userdata=SessionData(username="tester")) as session,
    ):
        await session.start(assistant)

        with mock_tools(SarjyAssistant, {"save_memory": _mock_save_memory}):
            result = await session.run(user_input="Please remember that my favorite color is blue.")

        call = result.expect.next_event().is_function_call(name="save_memory")
        raw_args = call.event().item.arguments
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        assert "blue" in str(args.get("value", "")).lower()

        result.expect.next_event().is_function_call_output()
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Confirms it will remember the user's favorite color is blue. "
                    "Does not claim it failed to save."
                ),
            )
        )
