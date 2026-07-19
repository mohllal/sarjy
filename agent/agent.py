"""Sarjy LiveKit Agents worker entrypoint."""

from __future__ import annotations

import logging
import json

from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    inference,
    room_io,
)

from assistants import SarjyAssistant
from integrations import BackendApiClient
from prompts import load_prompt
from schemas import SessionData
from session import (
    attach_conversation_persistence,
    load_history_chat_ctx,
)
from settings import get_settings

logger = logging.getLogger("sarjy.agent")

settings = get_settings()
backend = BackendApiClient(settings.backend_api_base_url)
server = AgentServer()


@server.rtc_session(agent_name=settings.livekit_agent_name)
async def sarjy_agent(ctx: JobContext) -> None:
    username = _username_from_job(ctx)
    logger.info(
        "starting Sarjy session for username=%s room=%s agent=%s",
        username,
        ctx.room.name,
        settings.livekit_agent_name,
    )

    chat_ctx = await load_history_chat_ctx(
        backend,
        username,
        limit=settings.conversation_history_limit,
    )

    session = AgentSession[SessionData](
        userdata=SessionData(username=username),
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        llm=inference.LLM(model="google/gemma-4-31b-it"),
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
    )

    attach_conversation_persistence(session, backend, username)

    await session.start(
        room=ctx.room,
        agent=SarjyAssistant(
            backend=backend,
            settings=settings,
            chat_ctx=chat_ctx,
        ),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(),
        ),
    )

    if username and not username.startswith("guest-"):
        greeting = load_prompt(
            "greeting",
            settings.greeting_prompt_version,
            variables={"username": username},
        )
    else:
        greeting = load_prompt(
            "greeting_guest",
            settings.greeting_prompt_version,
        )

    await session.generate_reply(instructions=greeting)


def _username_from_job(ctx: JobContext) -> str:
    raw = ctx.job.metadata or ""
    if not raw:
        return "friend"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return "friend"
    username = str(payload.get("username") or "").strip()
    return username or "friend"


if __name__ == "__main__":
    agents.cli.run_app(server)
