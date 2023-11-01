import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from src.app.api.schemas.common import Sex


class UserCreate(BaseModel):
    """Схема полей при регистрации пользователя."""

    email: EmailStr = Field(
        description='Адрес электронной почты пользователя.',
        example='user@example.com',
    )
    password: SecretStr = Field(
        description='Пароль в открытом виде.',
        example='mypassword',
        min_length=1,
    )


class BaseUser(BaseModel):
    full_name: str | None = Field(
        None,
        description='ФИО пользователя',
        example='Иванов Иван Иванович',
        min_length=3,
    )
    income: int | None = Field(
        None,
        description='Доход пользователя в копейках',
        example=100_000_00,
        gt=0,
    )
    another_loans: bool | None = Field(
        None,
        description='Есть ли у пользователя другие займы.',
        example=False,
    )
    birth_date: datetime.date | None = Field(
        None,
        description='Дата рождения. Формат: yyyy-mm-dd',
        example='1990-04-24',
    )
    sex: Sex | None = Field(
        None,
        description='Пол.',
        example='male',
    )


class UserUpdate(BaseUser):
    """Обновление полей пользователя."""


class User(BaseUser):
    """Информация о пользователе."""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr = Field(
        description='Адрес электронной почты пользователя.',
        example='user@example.com',
    )
    status_document: bool = Field(
        default=False,
        description='Предоставлена ли фотография валидного документа.',
        example=False,
    )
    status_face: bool = Field(
        default=False,
        description='Предоставлена ли валидная фотография лица.',
        example=False,
    )
