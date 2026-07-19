"""Integration tests for the LiveKit token endpoint."""

from __future__ import annotations

from httpx import AsyncClient


async def test_token_auto_generates_username_when_blank(client: AsyncClient) -> None:
    response = await client.post("/livekit/token", json={"username": "  "})
    assert response.status_code == 200
    body = response.json()
    assert body["username"].startswith("guest-")
    assert body["room_name"].startswith(f"sarjy-{body['username']}-")
    assert body["url"].startswith("wss://")
    assert body["token"]


async def test_token_uses_provided_username(client: AsyncClient) -> None:
    response = await client.post("/livekit/token", json={"username": "Kareem!"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "Kareem"
    assert "Kareem" in body["room_name"]
    assert body["url"].startswith("wss://")
    assert body["token"]
