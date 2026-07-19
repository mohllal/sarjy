"""LiveKit token request/response schemas."""

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str | None = Field(
        default=None,
        description="Stable user identity. Auto-generated when omitted or blank.",
    )


class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    username: str
