from unittest.mock import ANY, patch

from app.api.schemas.auth import Token


@patch('app.services.security.jwt.encode')
def test_create_token(mocked_thing, test_user_email, security_service):

    mocked_thing.return_value = 'token'
    access_token = security_service.create_access_token(test_user_email)

    assert access_token == Token(access_token='token', token_type='bearer')

    mocked_thing.assert_called_once_with(
        {'exp': ANY, 'sub': test_user_email},
        security_service.secret_key,
        algorithm='HS256'
    )
