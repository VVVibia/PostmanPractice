from contextlib import AbstractAsyncContextManager
from typing import Callable

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.api.schemas import user as user_schemas
from src.app.external.db.models import UserModel
from src.app.services.security import SecurityService


class UserService:

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        security_service: SecurityService,
    ):
        self.session_factory = session_factory
        self.security_service = security_service

    async def get_by_email(self, email: str) -> UserModel | None:
        async with self.session_factory() as session:
            return await session.scalar(
                select(UserModel).
                where(UserModel.email == email).
                options(selectinload(UserModel.credit_card)),
            )

    async def add(self, user_in: user_schemas.UserCreate) -> UserModel:
        password = user_in.password.get_secret_value()
        async with self.session_factory() as session:
            user = UserModel(
                email=user_in.email,
                hashed_password=self.security_service.get_password_hash(password),
            )
            async with session.begin():
                session.add(user)
            return user

    async def authenticate(self, email: str, password: str) -> UserModel | None:
        user = await self.get_by_email(email=email)
        if not user:
            return None
        if not self.security_service.verify_password(password, user.hashed_password):
            return None
        return user

    async def update(self, user_in: user_schemas.UserUpdate, user_db: UserModel):
        update_data = user_in.model_dump(exclude_unset=True)
        obj_data = jsonable_encoder(user_db)
        for field in obj_data:
            if field in update_data:
                setattr(user_db, field, update_data[field])
        async with self.session_factory() as session:
            async with session.begin():
                session.add(user_db)

    async def update_status_doc(self, user_db: UserModel, status: bool):
        user_db.status_document = status
        async with self.session_factory() as session:
            async with session.begin():
                session.add(user_db)

    async def update_status_face(self, user_db: UserModel, status: bool):
        user_db.status_face = status
        async with self.session_factory() as session:
            async with session.begin():
                session.add(user_db)
