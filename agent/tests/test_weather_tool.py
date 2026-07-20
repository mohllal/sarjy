"""Tests for get_weather tool invocation."""

from __future__ import annotations

import json

from livekit.agents import AgentSession, inference, mock_tools

from assistants.sarjy import SarjyAssistant
from schemas.session import SessionData
from settings import Settings


def _mock_weather(context, location: str, when: str | None = None) -> str:
    """Include RunContext in the signature so location binds correctly."""
    _ = context, when
    return f"Weather in {location}: clear sky, 28 degrees Celsius, light wind, low chance of rain."


async def test_weather_question_calls_get_weather(
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

        with mock_tools(SarjyAssistant, {"get_weather": _mock_weather}):
            result = await session.run(user_input="What's the weather in Amman right now?")

        call = result.expect.next_event().is_function_call(name="get_weather")
        raw_args = call.event().item.arguments
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        assert "Amman" in str(args.get("location", ""))

        result.expect.next_event().is_function_call_output()
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Answers with weather for Amman grounded in the tool result "
                    "(clear sky around 28 degrees). Does not invent other numbers."
                ),
            )
        )
