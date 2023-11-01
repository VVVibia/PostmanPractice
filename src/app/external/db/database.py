import logging
from asyncio import current_task
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Базвый класс алхимии."""


class Database:

    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(db_url, echo=False)
        self._session_factory = async_scoped_session(
            async_sessionmaker(self._engine, expire_on_commit=False),
            current_task,
        )

    async def create_database(self) -> None:
        """Для использования в тестах."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> Callable[..., AbstractAsyncContextManager[AsyncSession]]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            logging.exception('Session rollback because of exception')
            await session.rollback()
            raise
        finally:
            await session.close()

    async def is_connected(self):
        status = True
        try:
            async with self.session() as session:
                await session.scalar(text('SELECT 1'))
        except Exception:
            status = False
        return status
