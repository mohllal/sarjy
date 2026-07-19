"""Integration tests for memory endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_upsert_and_list_memories(client: AsyncClient) -> None:
    put = await client.put(
        "/memories/kareem",
        json={
            "facts": [
                {"key": "favorite_color", "value": "blue"},
                {"key": "home_city", "value": "Cairo"},
            ]
        },
    )
    assert put.status_code == 200
    body = put.json()
    assert body["username"] == "kareem"
    assert {m["key"]: m["value"] for m in body["memories"]} == {
        "favorite_color": "blue",
        "home_city": "Cairo",
    }

    listed = await client.get("/memories/kareem")
    assert listed.status_code == 200
    listed_body = listed.json()
    assert len(listed_body["memories"]) == 2
    assert {m["key"] for m in listed_body["memories"]} == {
        "favorite_color",
        "home_city",
    }


async def test_upsert_overwrites_same_key(client: AsyncClient) -> None:
    await client.put(
        "/memories/kareem",
        json={"facts": [{"key": "favorite_color", "value": "blue"}]},
    )
    updated = await client.put(
        "/memories/kareem",
        json={"facts": [{"key": "favorite_color", "value": "green"}]},
    )
    assert updated.status_code == 200
    assert updated.json()["memories"][0]["value"] == "green"

    listed = await client.get("/memories/kareem")
    assert len(listed.json()["memories"]) == 1
    assert listed.json()["memories"][0]["value"] == "green"


async def test_clear_memories(client: AsyncClient) -> None:
    await client.put(
        "/memories/kareem",
        json={
            "facts": [
                {"key": "favorite_color", "value": "blue"},
                {"key": "home_city", "value": "Cairo"},
            ]
        },
    )
    cleared = await client.delete("/memories/kareem")
    assert cleared.status_code == 204

    listed = await client.get("/memories/kareem")
    assert listed.json()["memories"] == []

    # Clearing again is idempotent.
    again = await client.delete("/memories/kareem")
    assert again.status_code == 204


async def test_memories_are_scoped_by_username(client: AsyncClient) -> None:
    await client.put(
        "/memories/alice",
        json={"facts": [{"key": "favorite_color", "value": "red"}]},
    )
    await client.put(
        "/memories/bob",
        json={"facts": [{"key": "favorite_color", "value": "green"}]},
    )

    alice = await client.get("/memories/alice")
    bob = await client.get("/memories/bob")
    assert alice.json()["memories"][0]["value"] == "red"
    assert bob.json()["memories"][0]["value"] == "green"
