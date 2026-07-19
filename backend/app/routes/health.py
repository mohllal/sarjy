"""Health module routes."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.containers import Container
from app.schemas.health import HealthResponse, ReadyResponse
from app.services.health import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
@inject
async def health(
    service: Annotated[HealthService, Depends(Provide[Container.health_service])],
) -> HealthResponse:
    return service.check_liveness()


@router.get("/ready", response_model=ReadyResponse)
@inject
async def ready(
    service: Annotated[HealthService, Depends(Provide[Container.health_service])],
) -> JSONResponse:
    payload, status_code = await service.check_readiness()
    return JSONResponse(status_code=status_code, content=payload.model_dump(exclude_none=True))
