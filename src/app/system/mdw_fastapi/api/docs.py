import inspect
from typing import Callable, List

from fastapi import APIRouter
from pydantic import BaseModel


def openapi(**openapi_kwargs):
    """Позволяет добавить openapi спецификацию хендлеров через ключевые параметры."""

    def decorator(func: Callable):
        func.openapi = openapi_kwargs
        return func

    return decorator


def add_route(router: APIRouter, methods: List[str], path: str, handler: Callable, **kwargs):
    """Добавляет эндпоинт в рутер с учетом аннотации возвращаемого типа и openapi параметров."""
    handler_signature = inspect.signature(handler)
    response_model = handler_signature.return_annotation
    if not issubclass(response_model, BaseModel):
        response_model = None
    openapi_val = getattr(handler, 'openapi', {})
    if "response_model" in openapi_val:
        response_model = openapi_val.pop("response_model")
    router.api_route(
        path=path,
        methods=methods,
        response_model=response_model,
        **openapi_val,
        **kwargs,
    )(handler)


def add_get(router: APIRouter, path: str, handler: Callable, **kwargs):
    """Добавляет GET метод в рутер."""
    add_route(router, ['GET'], path, handler, **kwargs)


def add_post(router: APIRouter, path: str, handler: Callable, **kwargs):
    """Добавляет POST метод в рутер."""
    add_route(router, ['POST'], path, handler, **kwargs)


def add_delete(router: APIRouter, path: str, handler: Callable, **kwargs):
    """Добавляет DELETE метод в рутер."""
    add_route(router, ['DELETE'], path, handler, **kwargs)


def add_patch(router: APIRouter, path: str, handler: Callable, **kwargs):
    """Добавляет POST метод в рутер."""
    add_route(router, ['PATCH'], path, handler, **kwargs)
