"""Integration tests for conversation history endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.conversation import ConversationMessage


async def _messages_for(
    session_factory: async_sessionmaker[AsyncSession],
    username: str,
) -> list[ConversationMessage]:
    async with session_factory() as session:
        result = await session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.username == username)
            .order_by(
                ConversationMessage.created_at.asc(),
                ConversationMessage.id.asc(),
            )
        )
        return list(result.scalars().all())


async def test_append_messages(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post(
        "/conversations/kareem/messages",
        json={
            "messages": [
                {"role": "user", "content": "My favorite color is blue."},
                {"role": "assistant", "content": "Got it, I'll remember that."},
            ]
        },
    )
    assert response.status_code == 200
    assert len(response.json()["messages"]) == 2

    rows = await _messages_for(session_factory, "kareem")
    assert [(row.role, row.content) for row in rows] == [
        ("user", "My favorite color is blue."),
        ("assistant", "Got it, I'll remember that."),
    ]


async def test_list_messages(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    base = datetime.now(UTC)
    async with session_factory() as session:
        session.add_all(
            [
                ConversationMessage(
                    username="kareem",
                    role="user",
                    content="My favorite color is blue.",
                    created_at=base,
                ),
                ConversationMessage(
                    username="kareem",
                    role="assistant",
                    content="Got it, I'll remember that.",
                    created_at=base + timedelta(microseconds=1),
                ),
            ]
        )
        await session.commit()

    response = await client.get("/conversations/kareem/messages")
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "My favorite color is blue."


async def test_list_messages_respects_limit(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    base = datetime.now(UTC)
    async with session_factory() as session:
        session.add_all(
            [
                ConversationMessage(
                    username="kareem",
                    role="user",
                    content="one",
                    created_at=base,
                ),
                ConversationMessage(
                    username="kareem",
                    role="assistant",
                    content="two",
                    created_at=base + timedelta(microseconds=1),
                ),
                ConversationMessage(
                    username="kareem",
                    role="user",
                    content="three",
                    created_at=base + timedelta(microseconds=2),
                ),
            ]
        )
        await session.commit()

    response = await client.get(
        "/conversations/kareem/messages",
        params={"limit": 2},
    )
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert len(messages) == 2
    # Newest window, returned chronological: assistant "two", user "three"
    assert [m["content"] for m in messages] == ["two", "three"]


async def test_clear_conversation(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add(
            ConversationMessage(
                username="kareem",
                role="user",
                content="hello",
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

    response = await client.delete("/conversations/kareem")
    assert response.status_code == 204
    assert await _messages_for(session_factory, "kareem") == []


async def test_list_messages_scoped_by_username(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    async with session_factory() as session:
        session.add_all(
            [
                ConversationMessage(
                    username="alice",
                    role="user",
                    content="alice says hi",
                    created_at=now,
                ),
                ConversationMessage(
                    username="bob",
                    role="user",
                    content="bob says hi",
                    created_at=now,
                ),
            ]
        )
        await session.commit()

    alice = await client.get("/conversations/alice/messages")
    bob = await client.get("/conversations/bob/messages")
    assert alice.json()["messages"][0]["content"] == "alice says hi"
    assert bob.json()["messages"][0]["content"] == "bob says hi"
