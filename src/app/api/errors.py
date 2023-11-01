from typing import Any

from fastapi import HTTPException, status

from src.app.api.schemas.common import ResponseMsg


class CustomHTTPException(HTTPException):
    """Кастомная ошибки сервиса."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Ошибка в сервисе.'

    def __init__(
        self,
        status_code: int = None,
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code or self.status_code,
            detail=detail or self.detail,
        )

    @property
    def example(self):
        return ResponseMsg(detail=self.detail).model_dump()

    @property
    def response_schema(self):
        return {
            self.status_code: {
                'model': ResponseMsg,
                'description': self.__doc__,
                'content': {
                    'application/json': {
                        'example': self.example,
                    },
                },
            },
        }

    @property
    def description(self):
        return self.__doc__


class CredentialsError(CustomHTTPException):
    """Ошибка при невозможности найти пользователя по указанным данным."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Некорркетный адрес почты или пароль.'


class TokenError(CustomHTTPException):
    """Ошибка при невозможности провалидировать токен."""

    status_code: int = status.HTTP_403_FORBIDDEN
    detail: Any = 'Невозможно провалидировать токен.'


class UserNotFoundError(CustomHTTPException):
    """Ошибка при невозможности найти пользователя."""

    status_code: int = status.HTTP_404_NOT_FOUND
    detail: Any = 'Пользователь не найден.'


class CreditCardAlreadyExistError(CustomHTTPException):
    """Ошибка, когда у пользователя уже есть кредитная карта."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'У пользователя уже есть кредитная карта.'


class CreditCardNotExistError(CustomHTTPException):
    """Ошибка, когда у пользователя нет открытых кредитных карт."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Карты нет, сначала надо открыть.'


class CreditCardNotActiveError(CustomHTTPException):
    """Ошибка, когда кредитная карта неактивна."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Карта неактивна.'


class CreditCardSmallLimitError(CustomHTTPException):
    """Ошибка, когда кредитная карта неактивна."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Запрашиваемый лимит меньше текущего.'


class CreditCardCantIncreaseLimitError(CustomHTTPException):
    """Ошибка, когда кредитная карта неактивна."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Увеличение лимита недоступно с текущими параметрами. ' + \
                  'Для увеличения попробуйте дополнить информацию о себе.'


class UserAlreadyExistError(CustomHTTPException):
    """Ошибка, когда пользователь уже зарегестрирован."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: Any = 'Пользователь с таким адресом электронной почты уже существует.'
