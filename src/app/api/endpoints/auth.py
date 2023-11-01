from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.app.api.errors import CredentialsError, TokenError, UserNotFoundError
from src.app.api.schemas.auth import Token
from src.app.external.db.models import UserModel
from src.app.services.security import SecurityService
from src.app.services.users import UserService
from src.app.system.mdw_fastapi.api.docs import openapi
from src.app.system.resources import ApplicationContainer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/access_token')


@openapi(
    responses={
        **CredentialsError().response_schema,
    },
)
@inject
async def access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
    security_service: SecurityService = Depends(Provide[ApplicationContainer.security]),
) -> Token:
    """Получение токена авторизации."""
    user = await user_service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise CredentialsError()
    return security_service.create_access_token(user.email)


authorize_responses = {
    **TokenError().response_schema,
    **UserNotFoundError().response_schema,
}


@inject
async def authorize(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
    security_service: SecurityService = Depends(Provide[ApplicationContainer.security]),
) -> UserModel:
    """Аутентификация пользователя: по токену ищется пользователь в БД и возвращает его."""
    try:
        email = security_service.get_email_from_token(token)
    except Exception:
        raise TokenError()
    user = await user_service.get_by_email(email=email)
    if not user:
        raise UserNotFoundError()
    return user
