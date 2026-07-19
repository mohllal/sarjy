"""Integration tests for memory endpoints."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.memory import Memory


async def _memories_for(
    session_factory: async_sessionmaker[AsyncSession],
    username: str,
) -> list[Memory]:
    async with session_factory() as session:
        result = await session.execute(
            select(Memory).where(Memory.username == username).order_by(Memory.key.asc())
        )
        return list(result.scalars().all())


async def test_upsert_memories(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.put(
        "/memories/kareem",
        json={
            "facts": [
                {"key": "favorite_color", "value": "blue"},
                {"key": "home_city", "value": "Cairo"},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "kareem"
    assert {m["key"]: m["value"] for m in body["memories"]} == {
        "favorite_color": "blue",
        "home_city": "Cairo",
    }

    rows = await _memories_for(session_factory, "kareem")
    assert {row.key: row.value for row in rows} == {
        "favorite_color": "blue",
        "home_city": "Cairo",
    }


async def test_upsert_overwrites_same_key(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add(Memory(username="kareem", key="favorite_color", value="blue"))
        await session.commit()

    response = await client.put(
        "/memories/kareem",
        json={"facts": [{"key": "favorite_color", "value": "green"}]},
    )
    assert response.status_code == 200
    assert response.json()["memories"][0]["value"] == "green"

    rows = await _memories_for(session_factory, "kareem")
    assert len(rows) == 1
    assert rows[0].value == "green"


async def test_list_memories(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add_all(
            [
                Memory(username="kareem", key="favorite_color", value="blue"),
                Memory(username="kareem", key="home_city", value="Cairo"),
            ]
        )
        await session.commit()

    response = await client.get("/memories/kareem")
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "kareem"
    assert {m["key"]: m["value"] for m in body["memories"]} == {
        "favorite_color": "blue",
        "home_city": "Cairo",
    }


async def test_clear_memories(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add_all(
            [
                Memory(username="kareem", key="favorite_color", value="blue"),
                Memory(username="kareem", key="home_city", value="Cairo"),
            ]
        )
        await session.commit()

    response = await client.delete("/memories/kareem")
    assert response.status_code == 204
    assert await _memories_for(session_factory, "kareem") == []

    # Clearing again is idempotent.
    again = await client.delete("/memories/kareem")
    assert again.status_code == 204
    assert await _memories_for(session_factory, "kareem") == []


async def test_list_memories_scoped_by_username(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add_all(
            [
                Memory(username="alice", key="favorite_color", value="red"),
                Memory(username="bob", key="favorite_color", value="green"),
            ]
        )
        await session.commit()

    alice = await client.get("/memories/alice")
    bob = await client.get("/memories/bob")
    assert alice.json()["memories"][0]["value"] == "red"
    assert bob.json()["memories"][0]["value"] == "green"
