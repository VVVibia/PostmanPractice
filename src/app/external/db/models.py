import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.schemas.common import Sex
from app.external.db.database import Base


class UserModel(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    full_name: Mapped[str | None]
    income: Mapped[int | None]
    another_loans: Mapped[bool | None]
    birth_date: Mapped[datetime.date | None]
    sex: Mapped[Sex | None]
    status_document: Mapped[bool] = mapped_column(default=False)
    status_face: Mapped[bool] = mapped_column(default=False)
    credit_card: Mapped['CreditCardModel'] = relationship()


class CreditCardModel(Base):
    __tablename__ = 'credit_card'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    limit: Mapped[int]
    balance: Mapped[int]
    active: Mapped[bool] = mapped_column(default=True)
    exp_date: Mapped[datetime.date]
