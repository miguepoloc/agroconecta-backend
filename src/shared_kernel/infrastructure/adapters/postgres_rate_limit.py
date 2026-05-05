"""PostgreSQL adapter for login rate limiting."""

import time

import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlalchemy.ext.asyncio

from src.shared_kernel.infrastructure.database import models


class PostgresRateLimitAdapter:
    def __init__(
        self,
        session_factory: sqlalchemy.ext.asyncio.async_sessionmaker[
            sqlalchemy.ext.asyncio.AsyncSession
        ],
    ) -> None:
        self._session_factory = session_factory

    async def increment(self, key: str, window_seconds: int = 900) -> int:
        """Atomically increment the counter; returns the new count."""
        expires_at = int(time.time()) + window_seconds
        stmt = (
            sqlalchemy.dialects.postgresql.insert(models.LoginRateLimitOrm)
            .values(key=key, count=1, expires_at=expires_at)
            .on_conflict_do_update(
                index_elements=["key"],
                set_={"count": models.LoginRateLimitOrm.count + 1},
            )
            .returning(models.LoginRateLimitOrm.count)
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            row = result.fetchone()
            return int(row[0]) if row else 1

    async def is_blocked(self, key: str, max_attempts: int = 5) -> bool:
        async with self._session_factory() as session:
            result = await session.get(models.LoginRateLimitOrm, key)
            if result is None:
                return False
            if result.expires_at <= int(time.time()):
                return False
            return result.count >= max_attempts

    async def reset(self, key: str) -> None:
        async with self._session_factory() as session:
            stmt = sqlalchemy.delete(models.LoginRateLimitOrm).where(
                models.LoginRateLimitOrm.key == key
            )
            await session.execute(stmt)
            await session.commit()
