from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.system.mdw_fastapi.middlewares import errors, metrics
from app.system.mdw_logging import context as mdw_log_context


async def _context_middleware(request: Request, call_next):
    """Обогащает логи контекстными переменными - айди запроса, endpoint."""
    mdw_log_context.additional_context.set({
        'service_endpoint': '{method} {path}'.format(method=request.method, path=request.url.path),
        'service_request_uid': str(uuid4()),
    })
    return await call_next(request)


def setup_middlewares(app: FastAPI):
    """Настраивает мидлвари приложения."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.add_middleware(BaseHTTPMiddleware, dispatch=errors.errors_middleware)
    app.add_middleware(BaseHTTPMiddleware, dispatch=metrics.metrics_middleware)
    app.add_middleware(BaseHTTPMiddleware, dispatch=_context_middleware)

    app.add_exception_handler(HTTPException, errors.handle_http_exception)
    app.add_exception_handler(RequestValidationError, errors.handle_validation_error)
