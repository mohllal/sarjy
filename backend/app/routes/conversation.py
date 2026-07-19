"""Conversation history HTTP routes."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.containers import Container
from app.schemas.conversation import (
    AppendMessagesRequest,
    ConversationMessageListResponse,
)
from app.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/{username}/messages", response_model=ConversationMessageListResponse)
@inject
async def append_messages(
    username: str,
    body: AppendMessagesRequest,
    service: Annotated[
        ConversationService,
        Depends(Provide[Container.conversation_service]),
    ],
) -> ConversationMessageListResponse:
    return await service.append(username, body)


@router.get("/{username}/messages", response_model=ConversationMessageListResponse)
@inject
async def list_messages(
    username: str,
    service: Annotated[
        ConversationService,
        Depends(Provide[Container.conversation_service]),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationMessageListResponse:
    return await service.list_recent(username, limit=limit, offset=offset)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def clear_conversation(
    username: str,
    service: Annotated[
        ConversationService,
        Depends(Provide[Container.conversation_service]),
    ],
) -> None:
    await service.clear(username)
