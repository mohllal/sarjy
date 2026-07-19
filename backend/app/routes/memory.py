"""Memory HTTP routes."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.containers import Container
from app.schemas.memory import MemoryListResponse, UpsertMemoriesRequest
from app.services.memory import MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])


@router.put("/{username}", response_model=MemoryListResponse)
@inject
async def upsert_memories(
    username: str,
    body: UpsertMemoriesRequest,
    service: Annotated[
        MemoryService,
        Depends(Provide[Container.memory_service]),
    ],
) -> MemoryListResponse:
    return await service.upsert(username, body)


@router.get("/{username}", response_model=MemoryListResponse)
@inject
async def list_memories(
    username: str,
    service: Annotated[
        MemoryService,
        Depends(Provide[Container.memory_service]),
    ],
) -> MemoryListResponse:
    return await service.list_all(username)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def clear_memories(
    username: str,
    service: Annotated[
        MemoryService,
        Depends(Provide[Container.memory_service]),
    ],
) -> None:
    await service.clear(username)
