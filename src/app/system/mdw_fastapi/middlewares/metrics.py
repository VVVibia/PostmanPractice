import time

from fastapi import Request, Response
from starlette.status import HTTP_400_BAD_REQUEST

from app.system.mdw_prometheus_metrics import global_registry
from app.system.mdw_prometheus_metrics.service.labels import RequestDuration


async def metrics_middleware(request: Request, call_next):
    """Фиксирует prometheus метрики запроса."""
    start_time = time.monotonic()
    response: Response = await call_next(request)
    operation = '{method} {path}'.format(method=request.method, path=request.url.path)
    request_labels = RequestDuration(
        operation=operation,
        http_status_code=response.status_code,
        error=response.status_code >= HTTP_400_BAD_REQUEST,
    )

    global_registry().write_timing(
        (time.monotonic() - start_time),
        request_labels,
    )
    return response
