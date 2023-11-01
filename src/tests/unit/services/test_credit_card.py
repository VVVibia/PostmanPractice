import datetime
from unittest.mock import AsyncMock

import pytest
from dateutil.relativedelta import relativedelta

from app.external.db.models import UserModel
from app.services.credit_cards import CreditCardService


@pytest.fixture
def credit_card_service(config):
    return CreditCardService(
        session_factory=AsyncMock(),
        exp_date_in_years=config.credit_card.exp_date_in_years,
        default_limit=config.credit_card.default_limit,
    )


@pytest.mark.parametrize(('user', 'expected_amount'), [
    pytest.param(UserModel(), 20_000_00, id='user_without_data'),
    pytest.param(UserModel(full_name='full_name'), 21_000_00, id='user has full_name'),
    pytest.param(UserModel(income=500_000_00), 120_000_00, id='user income > 300_000_00'),
    pytest.param(UserModel(income=300_000_00), 120_000_00, id='user income = 300_000_00'),
    pytest.param(UserModel(income=200_000_00), 30_000_00, id='user income > 100_000_00'),
    pytest.param(UserModel(income=100_000_00), 30_000_00, id='user income = 100_000_00'),
    pytest.param(UserModel(income=100_00), 21_000_00, id='user income = 100_00'),
    pytest.param(UserModel(income=0), 20_000_00, id='user income = 0'),
    pytest.param(UserModel(another_loans=False), 30_000_00, id='user with no other loans'),
    pytest.param(UserModel(another_loans=True), 20_000_00, id='user with other loans'),
    pytest.param(
        UserModel(income=300_000_00, another_loans=True),
        110_000_00,
        id='user income = 300_000_00 and other loans'
    ),
    pytest.param(
        UserModel(birth_date=(datetime.date.today() - relativedelta(years=15))),
        20_000_00,
        id='user with age < 18'
    ),
    pytest.param(
        UserModel(income=100_000_00, birth_date=(datetime.date.today() - relativedelta(years=15))),
        25_000_00,
        id='user income = 100_000_00 with age < 18'
    ),
    pytest.param(
        UserModel(birth_date=(datetime.date.today() - relativedelta(years=18) + relativedelta(days=1))),
        20_000_00,
        id='user with age is 1 day before 18'
    ),
    pytest.param(
        UserModel(birth_date=(datetime.date.today() - relativedelta(years=18))),
        22_000_00,
        id='user with age is 18'
    ),
    # ...
])
def test_get_limit(user: UserModel, expected_amount, credit_card_service):
    result_amount = credit_card_service.get_limit(
        requested_limit=500_000_00,
        user=user
    )
    assert result_amount == expected_amount
