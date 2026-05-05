"""Async SQLAlchemy session factory."""

import typing

import sqlalchemy.ext.asyncio


def build_engine(database_url: str) -> sqlalchemy.ext.asyncio.AsyncEngine:
    # Strip SSL query params that asyncpg doesn't accept directly;
    # pass ssl=True via connect_args when the URL targets a non-local host.
    import urllib.parse
    parsed = urllib.parse.urlparse(database_url)
    params = urllib.parse.parse_qs(parsed.query)
    ssl_params = {"sslmode", "channel_binding", "ssl"}
    cleaned_params = {k: v for k, v in params.items() if k not in ssl_params}
    cleaned_query = urllib.parse.urlencode(cleaned_params, doseq=True)
    clean_url = parsed._replace(query=cleaned_query).geturl()

    needs_ssl = parsed.hostname not in (None, "localhost", "127.0.0.1")
    connect_args: dict = {"ssl": True} if needs_ssl else {}

    return sqlalchemy.ext.asyncio.create_async_engine(
        clean_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args,
    )


def build_session_factory(
    engine: sqlalchemy.ext.asyncio.AsyncEngine,
) -> sqlalchemy.ext.asyncio.async_sessionmaker[sqlalchemy.ext.asyncio.AsyncSession]:
    return sqlalchemy.ext.asyncio.async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=sqlalchemy.ext.asyncio.AsyncSession,
    )


async def get_async_session(
    session_factory: sqlalchemy.ext.asyncio.async_sessionmaker[
        sqlalchemy.ext.asyncio.AsyncSession
    ],
) -> typing.AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    async with session_factory() as session:
        yield session
