"""Dependency injection container."""

from dependency_injector import containers, providers

from app.db.engine import create_engine, create_session_factory
from app.services.conversation import ConversationService
from app.services.health import HealthService
from app.services.livekit import LiveKitTokenService
from app.services.memory import MemoryService
from app.settings import Settings
from app.uow.sqlalchemy import SqlAlchemyUnitOfWork


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.routes.health",
            "app.routes.livekit",
            "app.routes.memory",
            "app.routes.conversation",
        ]
    )

    settings = providers.Singleton(Settings)

    engine = providers.Singleton(create_engine, settings=settings)

    session_factory = providers.Singleton(create_session_factory, engine=engine)

    uow = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)

    health_service = providers.Factory(
        HealthService,
        settings=settings,
        uow_factory=uow.provider,
    )

    livekit_token_service = providers.Factory(
        LiveKitTokenService,
        settings=settings,
    )

    memory_service = providers.Factory(
        MemoryService,
        uow_factory=uow.provider,
    )

    conversation_service = providers.Factory(
        ConversationService,
        uow_factory=uow.provider,
    )
