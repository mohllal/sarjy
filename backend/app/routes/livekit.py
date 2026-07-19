"""LiveKit token routes."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.containers import Container
from app.schemas.livekit import TokenRequest, TokenResponse
from app.services.livekit import LiveKitTokenService

router = APIRouter(prefix="/livekit", tags=["livekit"])


@router.post("/token", response_model=TokenResponse)
@inject
async def create_token(
    body: TokenRequest,
    service: Annotated[
        LiveKitTokenService,
        Depends(Provide[Container.livekit_token_service]),
    ],
) -> TokenResponse:
    return service.create_token(body)
