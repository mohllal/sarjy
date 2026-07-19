"""LiveKit access-token minting."""

from __future__ import annotations

import json
import re
import secrets
import uuid

from livekit.api import AccessToken, RoomAgentDispatch, RoomConfiguration, VideoGrants

from app.config import Settings
from app.schemas.livekit import TokenRequest, TokenResponse

_USERNAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")


class LiveKitTokenService:
    """Mints participant tokens with explicit Sarjy agent dispatch."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_token(self, request: TokenRequest) -> TokenResponse:
        username = self._resolve_username(request.username)
        room_name = self._generate_room_name(username)
        metadata = json.dumps({"username": username})

        token = (
            AccessToken(
                api_key=self._settings.livekit_api_key,
                api_secret=self._settings.livekit_api_secret,
            )
            .with_identity(username)
            .with_name(username)
            .with_metadata(metadata)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .with_room_config(
                RoomConfiguration(
                    agents=[
                        RoomAgentDispatch(
                            agent_name=self._settings.livekit_agent_name,
                            metadata=metadata,
                        )
                    ],
                )
            )
            .to_jwt()
        )

        return TokenResponse(
            token=token,
            url=self._settings.livekit_url,
            room_name=room_name,
            username=username,
        )

    @staticmethod
    def _resolve_username(username: str | None) -> str:
        cleaned = (username or "").strip()
        if cleaned:
            # Replace any non-alphanumeric character with a dash, then strip leading/trailing dashes and underscores
            sanitized = _USERNAME_RE.sub("-", cleaned).strip("-_")
            if sanitized:
                return sanitized[:64]
        return f"guest-{secrets.token_hex(4)}"

    @staticmethod
    def _generate_room_name(username: str) -> str:
        # Unique per session so token-based agent dispatch runs on room create
        return f"sarjy-{username}-{uuid.uuid4().hex[:8]}"
