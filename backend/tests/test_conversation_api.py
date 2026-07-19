"""Integration tests for conversation history endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_append_and_list_messages(client: AsyncClient) -> None:
    created = await client.post(
        "/conversations/kareem/messages",
        json={
            "messages": [
                {"role": "user", "content": "My favorite color is blue."},
                {"role": "assistant", "content": "Got it, I'll remember that."},
            ]
        },
    )
    assert created.status_code == 200
    assert len(created.json()["messages"]) == 2

    listed = await client.get("/conversations/kareem/messages")
    assert listed.status_code == 200
    messages = listed.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "My favorite color is blue."


async def test_list_messages_respects_limit(client: AsyncClient) -> None:
    await client.post(
        "/conversations/kareem/messages",
        json={
            "messages": [
                {"role": "user", "content": "one"},
                {"role": "assistant", "content": "two"},
                {"role": "user", "content": "three"},
            ]
        },
    )

    listed = await client.get("/conversations/kareem/messages", params={"limit": 2})
    assert listed.status_code == 200
    messages = listed.json()["messages"]
    assert len(messages) == 2
    # Newest window, returned chronological: assistant "two", user "three"
    assert [m["content"] for m in messages] == ["two", "three"]


async def test_clear_conversation(client: AsyncClient) -> None:
    await client.post(
        "/conversations/kareem/messages",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    cleared = await client.delete("/conversations/kareem")
    assert cleared.status_code == 204

    listed = await client.get("/conversations/kareem/messages")
    assert listed.json()["messages"] == []


async def test_conversations_are_scoped_by_username(client: AsyncClient) -> None:
    await client.post(
        "/conversations/alice/messages",
        json={"messages": [{"role": "user", "content": "alice says hi"}]},
    )
    await client.post(
        "/conversations/bob/messages",
        json={"messages": [{"role": "user", "content": "bob says hi"}]},
    )

    alice = await client.get("/conversations/alice/messages")
    bob = await client.get("/conversations/bob/messages")
    assert alice.json()["messages"][0]["content"] == "alice says hi"
    assert bob.json()["messages"][0]["content"] == "bob says hi"
