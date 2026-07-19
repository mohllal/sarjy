"""Conversation history request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationMessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AppendMessagesRequest(BaseModel):
    messages: list[ConversationMessageCreate] = Field(min_length=1)


class ConversationMessageResponse(BaseModel):
    id: UUID
    username: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageListResponse(BaseModel):
    username: str
    messages: list[ConversationMessageResponse]
