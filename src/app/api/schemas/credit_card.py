import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreditCard(BaseModel):
    """Информация о кредитной карте."""

    model_config = ConfigDict(from_attributes=True)

    limit: int = Field(
        description='Лимит карты в копейках',
        example=1_000_00,
        gt=0,
    )
    balance: int = Field(
        description='Текущий баланс карты в копейках',
        example=1_000_00,
        gt=0,
    )
    active: bool = Field(
        default=True,
        description='Флаг активности карты. False - карта закрыта',
    )
    exp_date: datetime.date = Field(
        description='Дата истечения действия карты. Формат: yyyy-mm-dd',
        example='2030-04-24',
    )
