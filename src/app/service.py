import argparse
import logging
import sys
from functools import partial
from typing import Callable

import uvicorn
from fastapi import FastAPI

from src.app.api.routes import setup_routes
from src.app.config import Config, read_config
from src.app.system import environment
from src.app.system.middlewares import setup_middlewares
from src.app.system.resources import ApplicationContainer, shutdown_event, startup_event


def prepare_app(config: Config) -> Callable:
    """Настраивает экземпляр FastAPI приложения.

    :param config: конфиг сервиса
    :return: настроенный экземпляр FastAPI приложения
    """
    tags_metadata = [
        {
            'name': 'healthz',
            'description': 'Служебные операции для определения состояния сервиса и сбора метрик.',
        },
        {
            'name': 'auth',
            'description': 'Операции по авторизации. Используется OAuth 2.0.',
        },
        {
            'name': 'user',
            'description': 'Операции по управлению пользователями.',
        },
        {
            'name': 'credit_card',
            'description': 'Операции по работе с кредитными картами.',
        },
    ]

    app = FastAPI(
        title='CreditCard application API',
        version=config.service.version,
        openapi_tags=tags_metadata,
    )
    container = ApplicationContainer(config=config)
    app.state.container = container
    setup_routes(app)
    setup_middlewares(app)
    app.on_event('startup')(partial(startup_event, app))
    app.on_event('shutdown')(partial(shutdown_event, app))
    return app


def start():
    """Запускает сервис."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-c',
        '--config',
        type=str,
        required=True,
        help='Path to configuration file',
    )
    ap.add_argument(
        '--env_prefix',
        type=str,
        help='Prefix for environment variables',
    )

    options, _ = ap.parse_known_args(sys.argv[1:])

    config = read_config(options.config, Config)

    environment.initialize(config)
    logging.info(config.model_dump())

    uvicorn.run(
        prepare_app(config),
        host='0.0.0.0',  # noqa: S104
        port=config.service.port,
        access_log=False,
        log_config=None,
    )


if __name__ == '__main__':
    start()
