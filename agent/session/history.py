"""Load prior conversation turns into a ChatContext."""

from __future__ import annotations

import logging

from livekit.agents import ChatContext

from integrations.backend import BackendApiClient


logger = logging.getLogger("sarjy.session.history")


async def load_history_chat_ctx(
    backend: BackendApiClient,
    username: str,
    *,
    limit: int,
) -> ChatContext | None:
    messages = await backend.list_messages(username, limit=limit)
    if not messages:
        return None

    chat_ctx = ChatContext()
    for message in messages:
        role = message["role"]
        if role not in ("user", "assistant"):
            continue
        chat_ctx.add_message(role=role, content=message["content"])
    logger.info(
        "loaded %s prior turns for username=%s",
        len(messages),
        username,
    )
    return chat_ctx
