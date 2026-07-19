"""Health / readiness response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    status: str
    database: str
    detail: str | None = Field(default=None)
