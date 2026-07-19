"""Memory request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryFact(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1)


class UpsertMemoriesRequest(BaseModel):
    facts: list[MemoryFact] = Field(min_length=1)


class MemoryResponse(BaseModel):
    id: UUID
    username: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoryListResponse(BaseModel):
    username: str
    memories: list[MemoryResponse]
