import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from app.system.mdw_prometheus_metrics import global_registry
from app.system.mdw_prometheus_metrics.service.labels import ErrorsCount


def _log_error(error: ErrorsCount, **extra_log):
    logging.exception({
        **error.to_dict(),
        **extra_log,
    })
    global_registry().write_error(error)


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Обработчик HTTP ошибок сервиса."""
    error = ErrorsCount(
        operation='{method} {path}'.format(method=request.method, path=request.url.path),
        http_status_code=exc.status_code,
        error_text=str(exc.detail),
    )
    _log_error(error)
    return JSONResponse(
        status_code=exc.status_code,
        headers=getattr(exc, 'headers', None),
        content={'detail': exc.detail},
    )


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Обработчик ошибок валидации входных запросов."""
    error = ErrorsCount(
        operation='{method} {path}'.format(method=request.method, path=request.url.path),
        http_status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        error_text='Request validation error. Locations: {locations}'.format(
            locations=[
                '.'.join(str(_) for _ in error['loc'])
                for error in exc.errors()
            ],
        ),
    )
    _log_error(error, body=exc.body)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={'detail': jsonable_encoder(exc.errors())},
    )


async def errors_middleware(request: Request, call_next):
    """Обрабатывает незнакомые ошибки и записывает их в метрики."""
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        error = ErrorsCount(
            operation='{method} {path}'.format(method=request.method, path=request.url.path),
            http_status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            error_text=str(exc),
        )
        _log_error(error)
        response = JSONResponse(
            status_code=error.http_status_code,
            content=jsonable_encoder({
                'detail': [
                    {
                        'loc': [],
                        'msg': error.error_text,
                        'type': str(type(exc)),
                    },
                ],
            }),
        )
    return response
