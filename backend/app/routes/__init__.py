"""HTTP route registration."""

from fastapi import APIRouter, FastAPI

from app.routes import health, livekit


def create_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(health.router)
    api.include_router(livekit.router)
    return api


def register_routes(app: FastAPI) -> None:
    app.include_router(create_api_router())
