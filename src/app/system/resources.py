from functools import partial

import aiohttp
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from dependency_injector.providers import Configuration, Factory, Resource, Singleton
from fastapi import FastAPI

from app.external.db.database import Database
from app.external.metrics_config import get_metrics_config, simple_metrics_operation_builder
from app.services.credit_cards import CreditCardService
from app.services.photo import PhotoService
from app.services.security import SecurityService
from app.services.users import UserService
from app.system.mdw_prometheus_metrics import global_registry
from app.system.mdw_prometheus_metrics.service.collector import Severity
from app.system.mdw_prometheus_metrics.service.external import (
    Component,
    ExternalComponentsChecker,
    collect_component_metrics,
    log_check_exception,
)


def _setup_components_checker(
    db: Database,
    photo_service: PhotoService,
):
    return ExternalComponentsChecker(
        callbacks=[
            partial(collect_component_metrics, global_registry()),
            log_check_exception,
        ],
        components=[
            Component(
                name='postgres',
                type='database',
                severity=Severity.MAJOR,
                checker=db.is_connected,
            ),
            Component(
                name='photo_service',
                type='service',
                severity=Severity.MINOR,
                checker=photo_service.is_connected,
            ),
        ],
    )


async def _setup_client_session():
    """Подготавливает клиента для HTTP-запросов с кэшированием во внешние сервисы."""
    trace_config = get_metrics_config(simple_metrics_operation_builder)
    session = aiohttp.ClientSession(trace_configs=[trace_config])
    yield session
    await session.close()


class ApplicationContainer(DeclarativeContainer):
    """Хранилище используемых ресурсов приложения."""

    wiring_config = WiringConfiguration(packages=['app.api'])
    config = Configuration(strict=True)

    db = Singleton(Database, db_url=config.provided.postgres.dsn)
    security = Singleton(
        SecurityService,
        secret_key=config.provided.jwt.secret,
        token_ttl=config.provided.jwt.access_token_expire_minutes,
    )
    user_service = Singleton(
        UserService,
        session_factory=db.provided.session,
        security_service=security,
    )

    credit_card_service = Singleton(
        CreditCardService,
        session_factory=db.provided.session,
        exp_date_in_years=config.provided.credit_card.exp_date_in_years,
        default_limit=config.provided.credit_card.default_limit,
    )

    http_session = Resource(_setup_client_session)
    photo_service = Singleton(
        PhotoService,
        session=http_session,
        config=config.provided.photo_service,
    )

    components_checker = Factory(
        _setup_components_checker,
        db=db,
        photo_service=photo_service,
    )


async def startup_event(app: FastAPI):
    """Инициализация ресурсов приложения."""
    await app.state.container.init_resources()


async def shutdown_event(app: FastAPI):
    """Закрытие ресурсов приложения."""
    await app.state.container.shutdown_resources()
