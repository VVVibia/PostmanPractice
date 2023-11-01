import enum

from pydantic import BaseModel, Field


class Sex(enum.Enum):
    male = 'male'
    female = 'female'


class ResponseMsg(BaseModel):
    """Ответ с текстовым статусом операции."""

    detail: str = Field(
        title='Текстовое описание результата',
    )
