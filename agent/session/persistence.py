"""Persist conversation turns as the session progresses."""

from __future__ import annotations

import asyncio
import logging

from livekit.agents import AgentSession, ConversationItemAddedEvent
from livekit.agents.llm import ChatMessage

from integrations.backend import BackendApiClient
from schemas.session import SessionData

logger = logging.getLogger("sarjy.session.persistence")


def attach_conversation_persistence(
    session: AgentSession[SessionData],
    backend: BackendApiClient,
    username: str,
) -> None:
    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev: ConversationItemAddedEvent) -> None:
        if not isinstance(ev.item, ChatMessage):
            return
        if ev.item.role not in ("user", "assistant"):
            return
        text = (ev.item.text_content or "").strip()
        if not text:
            return
        asyncio.create_task(
            backend.append_message(username, ev.item.role, text),
            name=f"persist-{ev.item.role}",
        )
        logger.info(
            "persisted %s message for username=%s",
            ev.item.role,
            username,
        )
