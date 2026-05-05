"""PostgreSQL adapter for refresh token storage."""

import time
import typing

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.shared_kernel.infrastructure.database import models


class PostgresRefreshTokenAdapter:
    def __init__(
        self,
        session_factory: sqlalchemy.ext.asyncio.async_sessionmaker[
            sqlalchemy.ext.asyncio.AsyncSession
        ],
    ) -> None:
        self._session_factory = session_factory

    async def put(self, token_hash: str, user_id: str, expires_at_unix: int) -> None:
        async with self._session_factory() as session:
            record = models.RefreshTokenOrm(
                token_hash=token_hash,
                user_id=user_id,
                expires_at=expires_at_unix,
                created_at=int(time.time()),
            )
            session.add(record)
            await session.commit()

    async def find_by_hash(self, token_hash: str) -> typing.Optional[dict[str, typing.Any]]:
        async with self._session_factory() as session:
            result = await session.get(models.RefreshTokenOrm, token_hash)
            if result is None:
                return None
            if result.expires_at <= int(time.time()):
                return None
            return {
                "token_hash": result.token_hash,
                "user_id": result.user_id,
                "expires_at": result.expires_at,
            }

    async def delete_by_hash(self, token_hash: str) -> None:
        async with self._session_factory() as session:
            result = await session.get(models.RefreshTokenOrm, token_hash)
            if result is not None:
                await session.delete(result)
                await session.commit()

    async def delete_by_user(self, user_id: str) -> None:
        async with self._session_factory() as session:
            stmt = sqlalchemy.delete(models.RefreshTokenOrm).where(
                models.RefreshTokenOrm.user_id == user_id
            )
            await session.execute(stmt)
            await session.commit()
