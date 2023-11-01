import datetime

import pytest
from dateutil.relativedelta import relativedelta

from app.api.schemas.common import Sex


@pytest.mark.add_test_user_data(
    {
        'full_name': 'Some Big Name',
        'income': 500_00,
        'another_loans': True,
        'birth_date': datetime.date.today() - relativedelta(years=21),
        'sex': Sex.male,
    }
)
async def test_user(cli, auth_header, add_test_user):
    """Проверка получения текущего пользователя"""
    resp = await cli.get(url='/user', headers=auth_header)

    assert resp.status_code == 200
    resp_data = resp.json()

    assert resp_data['another_loans'] == add_test_user.another_loans
    assert resp_data['full_name'] == add_test_user.full_name
    assert resp_data['income'] == add_test_user.income
    assert resp_data['birth_date'] == add_test_user.birth_date.isoformat()
    assert resp_data['sex'] == add_test_user.sex.value
    assert resp_data['email'] == add_test_user.email
    assert resp_data['status_document'] == add_test_user.status_document
    assert resp_data['status_face'] == add_test_user.status_face
