"""Concrete Unit of Work implementations for SQLAlchemy."""

import typing

import sqlalchemy.ext.asyncio

from src.shared_kernel.application.ports import unit_of_work


class SqlAlchemyUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """Manages its own session lifecycle — for Lambda/CLI/background jobs."""

    def __init__(
        self,
        session_factory: sqlalchemy.ext.asyncio.async_sessionmaker[
            sqlalchemy.ext.asyncio.AsyncSession
        ],
    ) -> None:
        self._session_factory = session_factory
        self._session: typing.Optional[sqlalchemy.ext.asyncio.AsyncSession] = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: object,
    ) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        if self._session is not None:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> sqlalchemy.ext.asyncio.AsyncSession:
        if self._session is None:
            raise RuntimeError("Session accessed outside of 'async with' block")
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


class FastAPIUnitOfWork(unit_of_work.AbstractUnitOfWork):
    """Wraps a FastAPI dependency-injected session — FastAPI manages lifecycle."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> "FastAPIUnitOfWork":
        return self

    @property
    def session(self) -> sqlalchemy.ext.asyncio.AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
