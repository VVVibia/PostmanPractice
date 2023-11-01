from dataclasses import asdict, dataclass, fields
from typing import Dict, List, Union

Primitive = Union[str, int, bool]


@dataclass
class TracedOperation:
    """Класс, содержащий структуру лейблов для определенного типа операции.

    Спецификация типов операций https://virgo.ftc.ru/pages/viewpage.action?pageId=915091568
    """

    def to_dict(self) -> Dict[str, Primitive]:
        """Лейблы для Prometheus метрик."""
        return asdict(self)

    @classmethod
    def labels(cls) -> List[str]:
        """Хранимые обьектом лейблы."""
        return [field.name for field in fields(cls)]


@dataclass
class RequestDuration(TracedOperation):
    """Лейблы операций http_request_duration_seconds и http_client_request_duration_seconds.

    Лейбл span_kind автоматически задается функцией, которая данный объект для записи метрик.
    """

    operation: str
    http_status_code: int
    error: bool = False

    def to_span_tags(self) -> Dict[str, Primitive]:
        """Теги для интеграции с jaeger."""
        return {
            'operation': self.operation,
            'http.status_code': self.http_status_code,
            'error': self.error,
        }


@dataclass
class MessageBusRequestDuration(TracedOperation):
    """Лейблы операции message_bus_request_duration_seconds.

    Лейблы service и span_kind автоматически задаются функцией,
      в которую передается данный объект для записи метрик.
    """

    component: str
    operation: str
    message_bus_destination: str
    error: bool = False


@dataclass
class ErrorsCount(TracedOperation):
    """Лейблы операции http_request_errors_count."""

    operation: str
    http_status_code: int
    error_text: str


@dataclass
class DbRequestDuration(TracedOperation):
    """Лейблы операции db_request_duration_seconds."""

    operation: str
    db_type: str
    db_user: str
    db_statement: str
    error: bool = False
    db_instance: str = ''

    def to_span_tags(self) -> Dict[str, Union[str, int, bool]]:
        """Теги для интеграции с jaeger."""
        return {
            'operation': self.operation,
            'db.type': self.db_type,
            'db.user': self.db_user,
            'db.instance': self.db_instance,
            'db.statement': self.db_statement,
            'error': self.error,
        }
