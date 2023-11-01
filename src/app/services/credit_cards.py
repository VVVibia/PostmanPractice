import datetime
from contextlib import AbstractAsyncContextManager
from typing import Callable

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.schemas.common import Sex
from src.app.external.db.models import CreditCardModel, UserModel


class CreditCardService:

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        exp_date_in_years: int,
        default_limit: int,
    ):
        self.session_factory = session_factory
        self.exp_date = datetime.datetime.today() + relativedelta(years=exp_date_in_years)
        self.default_limit = default_limit

    def get_limit(
        self,
        requested_limit: int,
        user: UserModel,
    ):
        available_limit = self.default_limit
        if user.full_name:
            available_limit += 1_000_00

        if user.income:
            if user.income >= 300_000_00:
                available_limit += 100_000_00
            elif user.income >= 100_000_00:
                available_limit += 10_000_00
            else:
                available_limit += 1_000_00

        if user.another_loans is False:
            available_limit += 10_000_00
        elif user.another_loans is True:
            available_limit -= 10_000_00

        if user.birth_date:
            age = relativedelta(datetime.datetime.today(), user.birth_date)
            if age.years > 60 or age.years < 18:
                available_limit -= 5_000_00
            else:
                available_limit += 2_000_00

        if user.sex:
            if user.sex == Sex.male:
                available_limit += 1_000_00
            else:
                available_limit += 2_000_00

        if user.status_document:
            available_limit += 5_000_00
        if user.status_face:
            available_limit += 5_000_00

        return max(min(available_limit, requested_limit), self.default_limit)

    async def add(self, limit: int, user_id: int) -> CreditCardModel:
        async with self.session_factory() as session:
            credit_card = CreditCardModel(
                limit=limit,
                balance=limit,
                exp_date=self.exp_date,
                user_id=user_id,
            )
            async with session.begin():
                session.add(credit_card)
            await session.refresh(credit_card)
            return credit_card

    async def update_limit(self, limit: int, credit_card_db: CreditCardModel) -> CreditCardModel:
        diff = limit - credit_card_db.limit
        credit_card_db.limit = limit
        credit_card_db.balance += diff
        async with self.session_factory() as session:
            async with session.begin():
                session.add(credit_card_db)
            await session.refresh(credit_card_db)
            return credit_card_db

    async def close_card(self, credit_card_db: CreditCardModel):
        credit_card_db.active = False
        async with self.session_factory() as session:
            async with session.begin():
                session.add(credit_card_db)
