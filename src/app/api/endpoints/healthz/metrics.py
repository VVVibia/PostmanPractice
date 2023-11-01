from enum import Enum
from http import HTTPStatus
from typing import Optional

import prometheus_client
from dependency_injector.wiring import Provide, inject
from fastapi import BackgroundTasks, Depends, Response

from src.app.system.mdw_prometheus_metrics import global_analytics_registry, global_registry
from src.app.system.mdw_prometheus_metrics.service.external import ExternalComponentsChecker
from src.app.system.resources import ApplicationContainer


class MetricsGet(Enum):
    """Типы метрик для получения."""

    activity = 'activity'
    analytics = 'analytics'
    health = 'health'


@inject
async def get_metrics(
    type: MetricsGet,  # noqa: WPS125 API
    background_tasks: BackgroundTasks,
    components: ExternalComponentsChecker =
    Depends(Provide[ApplicationContainer.components_checker]),
):
    """Возвращает метрики в формате Prometheus.

    * activity - метрики активности сервиса
    * health - метрики по состоянию сервиса
    * analytics - кастомные аналитические метрики
    """
    if type == MetricsGet.health:
        background_tasks.add_task(components.minor_components_status)
        return Response(
            content=global_registry().export_health_metrics(),
        )
    elif type == MetricsGet.activity:
        return Response(
            content=global_registry().export_activity_metrics(),
        )
    elif type == MetricsGet.analytics:
        return Response(
            content=prometheus_client.generate_latest(global_analytics_registry()),
        )


class MetricsDelete(Enum):
    """Типы метрик для получения."""

    activity = 'activity'
    health = 'health'


async def delete_metrics(type: Optional[MetricsDelete] = None):  # noqa: WPS125 API
    """Сбрасывает метрики."""
    metrics_facade = global_registry()
    if type is None:
        metrics_facade.new_activity_metrics()
        metrics_facade.new_health_metrics()
        return Response(status_code=int(HTTPStatus.OK))
    elif type == MetricsDelete.health:
        metrics_facade.new_health_metrics()
        return Response(status_code=int(HTTPStatus.OK))
    elif type == MetricsDelete.activity:
        metrics_facade.new_activity_metrics()
        return Response(status_code=int(HTTPStatus.OK))
