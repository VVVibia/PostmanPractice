from src.app.external.db.models import CreditCardModel


async def test_close(cli, auth_header, add_test_credit_card, session):
    """Проверка закрытия кредитной карты клиента"""
    resp = await cli.post(url='/credit_card/close', headers=auth_header)

    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data['detail'] == 'closed'

    credit_card = await session.get(CreditCardModel, add_test_credit_card.id)

    assert credit_card.active is False
