"""SQLAlchemy declarative base for all ORM models."""

from __future__ import annotations

import sqlalchemy.orm


class Base(sqlalchemy.orm.DeclarativeBase):
    pass
