"""Memory persistence service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.models.memory import Memory
from app.schemas.memory import (
    MemoryFact,
    MemoryListResponse,
    MemoryResponse,
    UpsertMemoriesRequest,
)
from app.uow.sqlalchemy import SqlAlchemyUnitOfWork


class MemoryService:
    """CRUD for per-username durable facts."""

    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def upsert(
        self,
        username: str,
        request: UpsertMemoriesRequest,
    ) -> MemoryListResponse:
        async with self._uow_factory() as uow:
            session = uow.session
            assert session is not None

            saved: list[Memory] = []
            for fact in request.facts:
                memory = await self._upsert_one(session, username, fact)
                saved.append(memory)

            for memory in saved:
                await session.refresh(memory)

            return MemoryListResponse(
                username=username,
                memories=[MemoryResponse.model_validate(m) for m in saved],
            )

    async def list_all(self, username: str) -> MemoryListResponse:
        async with self._uow_factory() as uow:
            session = uow.session
            assert session is not None

            result = await session.execute(
                select(Memory)
                .where(Memory.username == username)
                .order_by(Memory.key.asc())
            )
            rows = list(result.scalars().all())
            return MemoryListResponse(
                username=username,
                memories=[MemoryResponse.model_validate(m) for m in rows],
            )

    async def clear(self, username: str) -> int:
        async with self._uow_factory() as uow:
            session = uow.session
            assert session is not None

            result = await session.execute(
                delete(Memory).where(Memory.username == username)
            )
            return int(result.rowcount or 0)

    @staticmethod
    async def _upsert_one(session, username: str, fact: MemoryFact) -> Memory:
        result = await session.execute(
            select(Memory).where(
                Memory.username == username,
                Memory.key == fact.key,
            )
        )
        memory = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if memory is None:
            memory = Memory(
                username=username,
                key=fact.key,
                value=fact.value,
                created_at=now,
                updated_at=now,
            )
            session.add(memory)
        else:
            memory.value = fact.value
            memory.updated_at = now

        await session.flush()
        return memory
