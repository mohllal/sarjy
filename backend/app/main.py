"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.containers import Container
from app.routes import register_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: Container = app.container
    try:
        yield
    finally:
        engine = container.engine()
        await engine.dispose()


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI(title="Sarjy", version="0.1.0", lifespan=lifespan)
    app.container = container

    settings = container.settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routes(app)
    return app


app = create_app()
