"""Alembic migration environment — sync psycopg2."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logging.config import fileConfig

import sqlalchemy
from alembic import context

from src.shared_kernel.infrastructure import config as app_config
from src.shared_kernel.infrastructure.database import base

# Import all ORM models so Alembic can detect them
from src.shared_kernel.infrastructure.database import models as shared_models  # noqa: F401
from src.identity.user.infrastructure import models as user_models  # noqa: F401
from src.catalog.farmer.infrastructure import models as farmer_models  # noqa: F401
from src.catalog.product.infrastructure import models as product_models  # noqa: F401
from src.commerce.order.infrastructure import models as order_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = base.Base.metadata

settings = app_config.get_settings()
DATABASE_URL = settings.database_url
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    SYNC_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
else:
    SYNC_URL = DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: sqlalchemy.Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = sqlalchemy.create_engine(SYNC_URL)
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
