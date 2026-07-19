"""Behavioral tests: recall_memories tool invocation.

Verified against:
https://docs.livekit.io/agents/start/testing/test-framework/
"""

from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference, mock_tools

from assistants.sarjy import SarjyAssistant
from schemas.session import SessionData
from settings import Settings


def _mock_recall_memories(context) -> dict:
    _ = context
    return {
        "memories": [
            {"key": "favorite_color", "value": "blue"},
            {"key": "home_city", "value": "Amman"},
        ]
    }


async def test_recall_question_calls_recall_memories(
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

        with mock_tools(
            SarjyAssistant,
            {"recall_memories": _mock_recall_memories},
        ):
            result = await session.run(user_input="What's my favorite color?")

        result.expect.next_event().is_function_call(name="recall_memories")
        result.expect.next_event().is_function_call_output()
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Answers that the user's favorite color is blue, "
                    "grounded in recalled memories. Does not invent a different color."
                ),
            )
        )
