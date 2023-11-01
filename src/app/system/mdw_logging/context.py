from contextvars import ContextVar

service: str
version: str

additional_context: ContextVar[dict | None] = ContextVar('additional_context', default={})
