"""Dependency injection container."""

from dependency_injector import containers, providers

from app.config import Settings
from app.db.engine import create_engine, create_session_factory
from app.services.health import HealthService
from app.uow.sqlalchemy import SqlAlchemyUnitOfWork


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.routes.health",
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
