import logging
from enum import Enum, auto
from http import HTTPStatus

import prometheus_client

from .labels import DbRequestDuration, ErrorsCount, MessageBusRequestDuration, RequestDuration

_UP_HELP = 'DP application UP status'
_READY_HELP = 'DP application READY status'
_READY_COMPONENT_HELP = 'DP application component UP status'
_REQUEST_LATENCY_HELP = 'DP application request latency'
_EXTERNAL_REQUEST_LATENCY_HELP = 'DP application external request latency'
_CLIENT_REQUEST_LATENCY_HELP = 'DP application request latency of external services'
_DB_REQUEST_LATENCY_HELP = 'DP application sql query latency'
_MESSAGE_BUS_REQUEST_LATENCY_HELP = 'DP application request latency of message bus'
_ERROR_COUNTER_HELP = 'DP application errors count'
_METRICS_PREFIX = 'dp_service'
_COMPONENT = 'backend'


class Severity(Enum):
    """Перечисление важности компонента."""

    MINOR = auto()
    MAJOR = auto()


class ServiceCollector:  # noqa: WPS214 необходимость т.к. сервис экспортируем много метрик
    """Фасад для сбора prometheus метрик по стандарту ДП.

    Стандарт по сбору метрик https://virgo.ftc.ru/pages/viewpage.action?pageId=915091568
    """

    def __init__(self, service_name: str):
        """Принимает на вход название сервиса."""
        self._service_name = service_name
        self.new_health_metrics()
        self.new_activity_metrics()

    def write_timing(self, timing_s: float, request_labels: RequestDuration) -> None:
        """Метрика длительности запроса сервиса _http_request_duration_seconds."""
        self._request_latency_histogram.labels(
            service=self._service_name,
            **request_labels.to_dict(),
            span_kind='server',
        ).observe(timing_s)

    def write_external_timing(self, timing_s: float, request_labels: RequestDuration) -> None:
        """Метрика длительности запроса сервиса _http_client_request_duration_seconds."""
        self._external_request_latency_histogram.labels(
            service=self._service_name,
            **request_labels.to_dict(),
            span_kind='client',
        ).observe(timing_s)

    def write_db_timing(self, timing_s: float, db_labels: DbRequestDuration) -> None:
        """Метрика длительности запроса в бд _db_request_duration_seconds."""
        self._db_request_latency_histogram.labels(
            service=self._service_name,
            **db_labels.to_dict(),
            span_kind='client',
        ).observe(timing_s)

    def write_message_bus_consumer_timing(
        self,
        timing_s: float,
        message_bus_labels: MessageBusRequestDuration,
    ) -> None:
        """Метрика длительности вызова брокера очереди сообщений _message_bus_request_duration_seconds."""
        self._message_bus_request_latency_histogram.labels(
            service=self._service_name,
            **message_bus_labels.to_dict(),
            span_kind='consumer',
        ).observe(timing_s)

    def write_message_bus_producer_timing(
        self,
        timing_s: float,
        message_bus_labels: MessageBusRequestDuration,
    ) -> None:
        """Метрика длительности вызова брокера очереди сообщений _message_bus_request_duration_seconds."""
        self._message_bus_request_latency_histogram.labels(
            service=self._service_name,
            **message_bus_labels.to_dict(),
            span_kind='producer',
        ).observe(timing_s)

    def write_error(self, error_labels: ErrorsCount) -> None:
        """Метрика подсчета кол-ва ошибок _http_request_errors_count."""
        self._errors_counter.labels(
            service=self._service_name,
            **error_labels.to_dict(),
        ).inc()

    def write_up_status(self, http_status: int) -> None:
        """Метрика живучести _up."""
        status = 1 if HTTPStatus.OK <= http_status < HTTPStatus.BAD_REQUEST else 0
        self._up_gauge.set(status)

    def write_ready_status(self, http_status: int, probe=None) -> None:
        """Метрика доступности _ready."""
        status = 1 if HTTPStatus.OK <= http_status < HTTPStatus.BAD_REQUEST else 0
        if probe is not None:
            logging.warning(
                'Parameter probe is outdated. Use write_ready_component_status method instead.')
        self._ready_gauge.set(status)

    def write_ready_component_status(
        self,
        http_status: int,
        component: str,
        component_type: str,
        severity: Severity,
    ) -> None:
        """Метрика доступности компонентов сервиса _ready_component."""
        status = 1 if HTTPStatus.OK <= http_status < HTTPStatus.BAD_REQUEST else 0
        self._ready_component_gauge.labels(
            name=self._service_name,
            component=component,
            component_type=component_type,
            severity=severity.name.lower(),
        ).set(status)

    def export_health_metrics(self) -> str:
        """Экспорт метрик здоровья для типа метрик health."""
        return prometheus_client.generate_latest(self._health_reg)

    def export_activity_metrics(self) -> str:
        """Экспорт метрик здоровья для типа метрик activity."""
        return prometheus_client.generate_latest(self._activity_reg)

    def new_activity_metrics(self) -> None:
        """Инициализирует activity метрики. Может быть использовано для их пересоздания."""
        self._activity_reg = prometheus_client.CollectorRegistry()
        service_label = 'service'
        span_kind_label = 'span_kind'
        self._request_latency_histogram = prometheus_client.Histogram(
            name=f'{_METRICS_PREFIX}_http_request_duration_seconds',
            documentation=_REQUEST_LATENCY_HELP,
            labelnames=[service_label, span_kind_label] + RequestDuration.labels(),
            registry=self._activity_reg,
            buckets=(
                .005, .01, .025, .05, .075, .1, .2, .3, .4, .5, .75,
                1.0, 2.5, 5.0, 7.5, 10.0, float('inf'),
            ),
        )
        self._external_request_latency_histogram = prometheus_client.Histogram(
            name=f'{_METRICS_PREFIX}_http_client_request_duration_seconds',
            documentation=_EXTERNAL_REQUEST_LATENCY_HELP,
            labelnames=[service_label, span_kind_label] + RequestDuration.labels(),
            registry=self._activity_reg,
        )
        self._db_request_latency_histogram = prometheus_client.Histogram(
            name=f'{_METRICS_PREFIX}_db_request_duration_seconds',
            documentation=_DB_REQUEST_LATENCY_HELP,
            labelnames=[service_label, span_kind_label] + DbRequestDuration.labels(),
            registry=self._activity_reg,
        )
        self._message_bus_request_latency_histogram = prometheus_client.Histogram(
            name=f'{_METRICS_PREFIX}_message_bus_request_duration_seconds',
            documentation=_MESSAGE_BUS_REQUEST_LATENCY_HELP,
            labelnames=[service_label, span_kind_label] + MessageBusRequestDuration.labels(),
            registry=self._activity_reg,
        )
        self._errors_counter = prometheus_client.Counter(
            name=f'{_METRICS_PREFIX}_http_request_errors_count',
            documentation=_ERROR_COUNTER_HELP,
            labelnames=[service_label] + ErrorsCount.labels(),
            registry=self._activity_reg,
        )

    def new_health_metrics(self) -> None:
        """Инициализирует health метрики. Может быть использовано для их пересоздания."""
        self._health_reg = prometheus_client.CollectorRegistry()
        self._up_gauge = prometheus_client.Gauge(
            name=f'{_METRICS_PREFIX}_up',
            documentation=_UP_HELP,
            labelnames=['name', 'type'],
            registry=self._health_reg,
        ).labels(name=self._service_name, type=_COMPONENT)
        self._ready_gauge = prometheus_client.Gauge(
            name=f'{_METRICS_PREFIX}_ready',
            documentation=_READY_HELP,
            labelnames=['name', 'type'],
            registry=self._health_reg,
        ).labels(name=self._service_name, type=_COMPONENT)
        self._ready_component_gauge = prometheus_client.Gauge(
            name=f'{_METRICS_PREFIX}_ready_component',
            documentation=_READY_COMPONENT_HELP,
            labelnames=['name', 'component_type', 'component', 'severity'],
            registry=self._health_reg,
        )
