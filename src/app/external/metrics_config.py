import time
from http import HTTPStatus
from types import SimpleNamespace
from typing import Callable

from aiohttp import (
    ClientSession,
    TraceConfig,
    TraceRequestEndParams,
    TraceRequestExceptionParams,
    TraceRequestStartParams,
)

from src.app.system.mdw_prometheus_metrics import global_registry
from src.app.system.mdw_prometheus_metrics.service.labels import RequestDuration


class MetricsNamespace(SimpleNamespace):
    """Неймспейс для передачи переменных между этапами http запроса."""

    mdw_start_time_monotonic: float
    mdw_operation: str


MetricsOperationBuilder = Callable[
    [ClientSession, MetricsNamespace, TraceRequestStartParams],
    str,
]


def simple_metrics_operation_builder(
    session: ClientSession,
    trace_config_ctx: MetricsNamespace,
    params: TraceRequestStartParams,
) -> str:
    """Возвращает операцию для записи в метрики, которая состоит из метода запроса и эндпоинта."""
    return f'{params.method} {params.url}'


def _on_request_start_factory(metrics_operation_builder: MetricsOperationBuilder):
    async def factory(
        session: ClientSession,
        trace_config_ctx,
        params: TraceRequestStartParams,
    ) -> None:
        # Данные для метрики
        trace_config_ctx.mdw_start_time_monotonic = time.monotonic()
        trace_config_ctx.mdw_operation = metrics_operation_builder(
            session, trace_config_ctx, params,
        )

    return factory


async def _on_request_end(
    session: ClientSession,
    trace_config_ctx,
    params: TraceRequestEndParams,
) -> None:
    request_labels = RequestDuration(
        operation=trace_config_ctx.mdw_operation,
        http_status_code=params.response.status,
        error=False,
    )

    global_registry().write_external_timing(
        time.monotonic() - trace_config_ctx.mdw_start_time_monotonic,
        request_labels,
    )


async def _on_request_exception(
    session: ClientSession,
    trace_config_ctx,
    params: TraceRequestExceptionParams,
) -> None:
    request_labels = RequestDuration(
        operation=trace_config_ctx.mdw_operation,
        http_status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        error=True,
    )

    global_registry().write_external_timing(
        time.monotonic() - trace_config_ctx.mdw_start_time_monotonic,
        request_labels,
    )


def get_metrics_config(metrics_operation_builder: MetricsOperationBuilder) -> TraceConfig:
    """Создаёт TraceConfig с поддержкой метрик и трейсинга для использования в ClientSession.

    Args:
        metrics_operation_builder: функция для построения строкового представления http запроса,
            результат её выполнения, при http запросе, записывается, как операция в метриках.

    Returns:
        Настроенный TraceConfig
    """
    trace_config = TraceConfig(trace_config_ctx_factory=MetricsNamespace)
    trace_config.on_request_start.append(_on_request_start_factory(metrics_operation_builder))
    trace_config.on_request_end.append(_on_request_end)
    trace_config.on_request_exception.append(_on_request_exception)
    return trace_config
