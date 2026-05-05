"""SQLAlchemy ORM models for the identity context."""

import sqlalchemy
import sqlalchemy.orm

from src.shared_kernel.infrastructure.database import base


class UserOrm(base.Base):
    __tablename__ = "users"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(10), primary_key=True
    )
    email: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), unique=True, nullable=False, index=True
    )
    first_name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100), nullable=False
    )
    last_name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100), nullable=False
    )
    phone: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False
    )
    password_hash: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    role: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="active"
    )
    version: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=1
    )
    created_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
    updated_at: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger, nullable=False
    )
