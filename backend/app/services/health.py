"""Health and readiness service."""

from collections.abc import Callable

from sqlalchemy import text

from app.schemas.health import HealthResponse, ReadyResponse
from app.settings import Settings
from app.uow.sqlalchemy import SqlAlchemyUnitOfWork


class HealthService:
    """Liveness and readiness checks."""

    def __init__(
        self,
        settings: Settings,
        uow_factory: Callable[[], SqlAlchemyUnitOfWork],
    ) -> None:
        self._settings = settings
        self._uow_factory = uow_factory

    def check_liveness(self) -> HealthResponse:
        return HealthResponse(status="ok")

    async def check_readiness(self) -> tuple[ReadyResponse, int]:
        if not self._settings.database_url:
            return ReadyResponse(status="ok", database="skipped"), 200

        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("Unit of Work session was not opened")
                await uow.session.execute(text("SELECT 1"))
            return ReadyResponse(status="ok", database="ok"), 200
        except Exception as exc:  # noqa: BLE001 — surface connectivity failures as 503
            return (
                ReadyResponse(
                    status="unavailable",
                    database="error",
                    detail=str(exc),
                ),
                503,
            )
