from typing import Any

from fastapi import status

from src.app.api.errors import CustomHTTPException


class HttpClientError(CustomHTTPException):
    """Ошибка при выполнении HTTP-запроса."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: Any = 'Неожиданная ошибка при обращении к стороннему сервису.'


class HttpClientTimeoutError(CustomHTTPException):
    """Ошибка истечения таймаута при выполнении HTTP-запроса."""

    status_code: int = status.HTTP_408_REQUEST_TIMEOUT
    detail: Any = 'Timeout при обращении к стороннему сервису.'

    def __init__(
        self,
        service_name: str | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=f'Сервис {service_name} недоступен в течении {timeout} секунд.',
        )
