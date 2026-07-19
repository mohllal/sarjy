"""HTTP route registration."""

from fastapi import APIRouter, FastAPI

from app.routes import conversation, health, livekit, memory


def create_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(health.router)
    api.include_router(livekit.router)
    api.include_router(memory.router)
    api.include_router(conversation.router)
    return api


def register_routes(app: FastAPI) -> None:
    app.include_router(create_api_router())
