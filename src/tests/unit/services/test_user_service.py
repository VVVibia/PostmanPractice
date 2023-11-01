import datetime

import pytest
from dateutil.relativedelta import relativedelta
from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select

from app.api.schemas.common import Sex
from app.api.schemas.user import UserCreate, UserUpdate
from app.external.db.models import UserModel


@pytest.fixture
async def email(session, request):
    yield request.param
    await session.execute(delete(UserModel).where(UserModel.email == request.param))
    await session.commit()


# indirect позволяет передать в фикстуру значение параметра
@pytest.mark.parametrize('email', ['test@user.email'], indirect=["email"])
async def test_add_valid_user(
    user_service,
    session,
    email,
):
    expected_user = UserModel(email=email)
    user_in = UserCreate(email=email, password='test_user_password')

    added_user = await user_service.add(user_in=user_in)

    assert added_user.email == expected_user.email

    user_in_db = await session.scalar(select(UserModel).where(UserModel.email == email))
    assert user_in_db.email == expected_user.email
    assert user_in_db.hashed_password == added_user.hashed_password


@pytest.mark.parametrize('user_in', [
    pytest.param(
        UserUpdate(
            full_name='Hello Im User',
            income=10_000_00,
            another_loans=False,
            birth_date=datetime.date.today() - relativedelta(years=25),
            sex=Sex.male,
        ),
        id='fill all data to new user with empty data'
    ),
    pytest.param(
        UserUpdate(
            full_name='Hello Im User',
            income=10_000_00,
            another_loans=False,
            birth_date=datetime.date.today() - relativedelta(years=25),
            sex=Sex.male,
        ),
        marks=pytest.mark.add_test_user_data({
            'full_name': 'Some Big Name',
            'income': 500_00,
            'another_loans': True,
            'birth_date': datetime.date.today() - relativedelta(years=21),
            'sex': Sex.female,
        }),
        id='update all data to user with data',
    ),
    pytest.param(
        UserUpdate(
            full_name=None,   # заполненный параметр на None
            birth_date=datetime.date.today() - relativedelta(years=25),   # заполненный параметр на другое значние
            sex=Sex.male,   # None на другое значение
        ),
        marks=pytest.mark.add_test_user_data({
                'full_name': 'Some Big Name',
                'income': 500_00,
                'another_loans': True,
                'birth_date': datetime.date.today() - relativedelta(years=21),
                'sex': None,
        }),
        id='update some params to user with data',
    ),
    pytest.param(
        UserUpdate(),
        marks=pytest.mark.add_test_user_data({
                'full_name': 'Some Big Name',
                'income': 500_00,
                'another_loans': True,
                'birth_date': datetime.date.today() - relativedelta(years=21),
                'sex': None,
        }),
        id='no fields to update',
    ),
])
async def test_update_user(
    user_service,
    add_test_user,
    session,
    user_in: UserUpdate,
):
    await user_service.update(user_in=user_in, user_db=add_test_user)

    updated_user = await session.scalar(select(UserModel).where(UserModel.email == add_test_user.email))
    user_in_data = user_in.model_dump(exclude_unset=True)
    updated_user_data = jsonable_encoder(updated_user)

    for field in updated_user_data:
        # если в UserUpdate задан параметр, то проверяем, что в обновленной записи он изменился
        if field in user_in_data:
            assert getattr(updated_user, field) == getattr(user_in, field)
        # иначе, проверяем, что параметр остался без изменений
        else:
            assert getattr(updated_user, field) == getattr(add_test_user, field)
