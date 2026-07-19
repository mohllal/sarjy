"""Conversation history persistence service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.models.conversation import ConversationMessage
from app.schemas.conversation import (
    AppendMessagesRequest,
    ConversationMessageListResponse,
    ConversationMessageResponse,
)
from app.uow.sqlalchemy import SqlAlchemyUnitOfWork


class ConversationService:
    """Append and read conversation turns keyed by username."""

    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def append(
        self,
        username: str,
        request: AppendMessagesRequest,
    ) -> ConversationMessageListResponse:
        async with self._uow_factory() as uow:
            session = uow.session
            assert session is not None

            base = datetime.now(timezone.utc)
            rows: list[ConversationMessage] = []
            for index, item in enumerate(request.messages):
                row = ConversationMessage(
                    username=username,
                    role=item.role,
                    content=item.content,
                    # Assigns a unique timestamp to each message in the batch to preserve their order,
                    # even when multiple messages are created at the same base time.
                    created_at=base + timedelta(microseconds=index),
                )
                session.add(row)
                rows.append(row)

            await session.flush()
            for row in rows:
                await session.refresh(row)

            return ConversationMessageListResponse(
                username=username,
                messages=[ConversationMessageResponse.model_validate(r) for r in rows],
            )

    async def list_recent(
        self,
        username: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> ConversationMessageListResponse:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        async with self._uow_factory() as uow:
            session = uow.session
            assert session is not None

            # Newest-first window by (created_at, id) and offset/limit.
            # Then sort chronologically if there are multiple messages at the same time.
            result = await session.execute(
                select(ConversationMessage)
                .where(ConversationMessage.username == username)
                .order_by(
                    ConversationMessage.created_at.desc(),
                    ConversationMessage.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
            rows = sorted(
                result.scalars().all(),
                key=lambda row: (row.created_at, row.id),
            )

            return ConversationMessageListResponse(
                username=username,
                messages=[ConversationMessageResponse.model_validate(r) for r in rows],
            )

    async def clear(self, username: str) -> int:
        async with self._uow_factory() as uow:
            session = uow.session
            assert session is not None

            result = await session.execute(
                delete(ConversationMessage).where(
                    ConversationMessage.username == username
                )
            )
            return int(result.rowcount or 0)
