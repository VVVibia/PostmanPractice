from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, HTTPException, Response, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from src.app.api.endpoints.auth import authorize, authorize_responses
from src.app.api.errors import UserAlreadyExistError
from src.app.api.schemas import user as user_schemas
from src.app.api.schemas.common import ResponseMsg
from src.app.external.db.models import UserModel
from src.app.external.http_errors import HttpClientTimeoutError
from src.app.services.photo import PhotoService
from src.app.services.users import UserService
from src.app.system.mdw_fastapi.api.docs import openapi
from src.app.system.resources import ApplicationContainer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/access_token')


@openapi(
    responses={
        **UserAlreadyExistError().response_schema,
    },
)
@inject
async def register(
    user_in: user_schemas.UserCreate,
    user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
) -> ResponseMsg:
    """Регистрация нового пользователя."""
    user = await user_service.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким адресом электронной почты уже существует.',
        )
    await user_service.add(user_in)
    return ResponseMsg(detail='success')


@openapi(
    response_model=user_schemas.User,
    responses={
        **authorize_responses,
    },
)
async def get_user_me(
    user: UserModel = Depends(authorize),
):
    """Получить информацию о текущем пользователе."""
    return user


@openapi(
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **authorize_responses,
    },
)
async def update_user(
    user_in: user_schemas.UserUpdate,
    user: UserModel = Depends(authorize),
    user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
) -> Response:
    """Обновить информацию о текущем пользователе."""
    await user_service.update(user_in, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@openapi(
    response_model=ResponseMsg,
    responses={
        **authorize_responses,
        **HttpClientTimeoutError(service_name='PhotoService', timeout=2).response_schema,
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseMsg,
            'description': 'Ошибка если фотография признаётся невалидной.',
            'content': {
                'application/json': {
                    'example': ResponseMsg(detail='not validated').model_dump(),
                },
            },
        },
    },
)
async def document_photo(
    file: Annotated[UploadFile, File(description='Фотография документа')],
    user: UserModel = Depends(authorize),
    photo_service: PhotoService = Depends(Provide[ApplicationContainer.photo_service]),
    user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
):
    """Приложить фотографию документа для проверки."""
    status_photo = await photo_service.validate_photo(photo=file, photo_type='doc')
    await user_service.update_status_doc(status=status_photo, user_db=user)
    if status_photo:
        return ResponseMsg(detail='validated')
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ResponseMsg(detail='not validated')),
    )


@openapi(
    response_model=ResponseMsg,
    responses={
        **authorize_responses,
        **HttpClientTimeoutError(service_name='PhotoService', timeout=2).response_schema,
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseMsg,
            'description': 'Ошибка если фотография признаётся невалидной.',
            'content': {
                'application/json': {
                    'example': ResponseMsg(detail='not validated').model_dump(),
                },
            },
        },
    },
)
async def face_photo(
    file: Annotated[UploadFile, File(description='Фотография лица')],
    user: UserModel = Depends(authorize),
    photo_service: PhotoService = Depends(Provide[ApplicationContainer.photo_service]),
    user_service: UserService = Depends(Provide[ApplicationContainer.user_service]),
):
    """Приложить фотографию лица для проверки."""
    status_photo = await photo_service.validate_photo(photo=file, photo_type='face')
    await user_service.update_status_face(status=status_photo, user_db=user)
    if status_photo:
        return ResponseMsg(detail='validated')
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ResponseMsg(detail='not validated')),
    )
