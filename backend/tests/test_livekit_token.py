"""Unit tests for LiveKit token minting (no network)."""

from app.schemas.livekit import TokenRequest
from app.services.livekit import LiveKitTokenService


class _Settings:
    livekit_url = "wss://example.livekit.cloud"
    livekit_api_key = "APItest"
    livekit_api_secret = "secret"
    livekit_agent_name = "sarjy"


def test_auto_generates_username_when_blank() -> None:
    service = LiveKitTokenService(_Settings())  # type: ignore[arg-type]
    response = service.create_token(TokenRequest(username="  "))
    assert response.username.startswith("guest-")
    assert response.room_name.startswith(f"sarjy-{response.username}-")
    assert response.url.startswith("wss://")
    assert response.token


def test_uses_provided_username() -> None:
    service = LiveKitTokenService(_Settings())  # type: ignore[arg-type]
    response = service.create_token(TokenRequest(username="Kareem!"))
    assert response.username == "Kareem"
    assert "Kareem" in response.room_name
