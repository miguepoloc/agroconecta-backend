"""ORM models for shared infrastructure tables (tokens, rate limits, event log)."""

import sqlalchemy
import sqlalchemy.orm

from src.shared_kernel.infrastructure.database import base


class RefreshTokenOrm(base.Base):
    __tablename__ = "refresh_tokens"

    token_hash: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(128), primary_key=True
    )
    user_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), nullable=False, index=True
    )
    expires_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    created_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )


class LoginRateLimitOrm(base.Base):
    __tablename__ = "login_rate_limits"

    key: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(128), primary_key=True
    )
    count: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=1
    )
    expires_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )


class EventLogOrm(base.Base):
    __tablename__ = "event_log"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), primary_key=True
    )
    aggregate_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(36), nullable=False, index=True
    )
    event_type: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(128), nullable=False, index=True
    )
    payload: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    occurred_on: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), nullable=False
    )
