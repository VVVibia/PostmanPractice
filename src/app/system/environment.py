from logging import config

from app.config import Config
from app.system.mdw_logging import context as mdw_log_context
from app.system.mdw_prometheus_metrics import ServiceCollector, set_global_registry


def _configure_logging(service_name, service_version, log_config):
    """Настраивает формат логирования в соответствии с конфигурацией.

    :param service_name: название сервиса
    :param service_version: версия сервиса
    :param log_config: конфигурация логера
    """
    mdw_log_context.service = service_name
    mdw_log_context.version = service_version

    config.dictConfig(log_config)


def _init_metrics(service_name):
    """Инициализирует глобальный сборщик стандартных метрик.

    :param service_name: название сервиса
    """
    set_global_registry(ServiceCollector(service_name))


def initialize(common_config: Config):
    """Инициализирует все обертки над либами для Application.

    :param common_config: конфигурация приложения
    """
    service_name = common_config.service.name
    service_version = common_config.service.version
    _configure_logging(service_name, service_version, common_config.logging)
    _init_metrics(service_name)
