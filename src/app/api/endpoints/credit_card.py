from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Query, status
from fastapi.security import OAuth2PasswordBearer

from src.app.api.endpoints.auth import authorize, authorize_responses
from src.app.api.errors import (
    CreditCardAlreadyExistError,
    CreditCardCantIncreaseLimitError,
    CreditCardNotActiveError,
    CreditCardNotExistError,
    CreditCardSmallLimitError,
)
from src.app.api.schemas import credit_card as cc_schemas
from src.app.api.schemas.common import ResponseMsg
from src.app.external.db.models import CreditCardModel, UserModel
from src.app.services.credit_cards import CreditCardService
from src.app.system.mdw_fastapi.api.docs import openapi
from src.app.system.resources import ApplicationContainer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/access_token')


@openapi(
    response_model=cc_schemas.CreditCard,
    responses={
        **authorize_responses,
        **CreditCardAlreadyExistError().response_schema,
    },
)
@inject
async def add_card(
    requested_limit: Annotated[int, Query(
        alias='limit',
        gt=0,
        description='Запрашиваемый лимит карты в копейках',
        example=1_000_00,
    )],
    user: UserModel = Depends(authorize),
    credit_card_service: CreditCardService =
    Depends(Provide[ApplicationContainer.credit_card_service]),
):
    """Завести новую кредитную карту."""
    if user.credit_card:
        raise CreditCardAlreadyExistError()

    limit = credit_card_service.get_limit(requested_limit, user)

    return await credit_card_service.add(limit=limit, user_id=user.id)


get_current_card_responses = {
    **authorize_responses,
    **CreditCardNotExistError().response_schema,
}


@openapi(
    response_model=cc_schemas.CreditCard,
    responses={
        **get_current_card_responses,
    },
)
@inject
async def get_current_card(
    user: UserModel = Depends(authorize),
):
    """Получить информацию о текущей карте."""
    if not user.credit_card:
        raise CreditCardNotExistError()
    return user.credit_card


@openapi(
    response_model=cc_schemas.CreditCard,
    responses={
        **authorize_responses,
        status.HTTP_400_BAD_REQUEST: {
            'description': f'Различного рода ошибки. Такие как:\n'
                           f'* {CreditCardNotExistError().description}\n'
                           f'* {CreditCardNotActiveError().description}\n'
                           f'* {CreditCardSmallLimitError().description}\n'
                           f'* {CreditCardCantIncreaseLimitError().description}\n',
            'model': ResponseMsg,
        },
    },
)
@inject
async def increase_limit(
    requested_limit: Annotated[int, Query(
        alias='limit',
        gt=0,
        description='Запрашиваемый лимит карты в копейках',
        example=1_000_00,
    )],
    user: UserModel = Depends(authorize),
    current_card: CreditCardModel = Depends(get_current_card),
    credit_card_service: CreditCardService =
    Depends(Provide[ApplicationContainer.credit_card_service]),
):
    """Увеличить лимит по текущей карте."""
    if not current_card.active:
        raise CreditCardNotActiveError()
    if current_card.limit >= requested_limit:
        raise CreditCardSmallLimitError()

    limit = credit_card_service.get_limit(requested_limit, user)
    if current_card.limit >= limit:
        raise CreditCardCantIncreaseLimitError()

    return await credit_card_service.update_limit(
        limit=limit,
        credit_card_db=current_card,
    )


@openapi(
    responses={
        **get_current_card_responses,
    },
)
@inject
async def close_card(
    current_card: CreditCardModel = Depends(get_current_card),
    credit_card_service: CreditCardService =
    Depends(Provide[ApplicationContainer.credit_card_service]),
) -> ResponseMsg:
    """Закрыть текущую карту."""
    await credit_card_service.close_card(credit_card_db=current_card)
    return ResponseMsg(detail='closed')
