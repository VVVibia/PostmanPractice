from prometheus_client import CollectorRegistry

from .service.collector import ServiceCollector

_service_registry = None
_analytics_registry: CollectorRegistry = CollectorRegistry()


def global_registry() -> ServiceCollector:
    """Возвращает глобальный регистри метрик сервиса.
    Если регистри не было инициализировано, то raise AttributeError
    """
    if _service_registry is None:
        raise AttributeError('Global registry is not initialised')
    return _service_registry


def set_global_registry(new_registry: ServiceCollector):
    """Устанавливает глобальный регистри.
    Если новое значение регистри должно быть типа ServiceCollector или наследовать его.
    """
    if not isinstance(new_registry, ServiceCollector):
        raise TypeError('The global registry must be ServiceCollector type or inherits it.')

    global _service_registry
    _service_registry = new_registry


def global_analytics_registry() -> CollectorRegistry:
    """Возвращает глобальный регистри метрик сервиса."""
    return _analytics_registry
