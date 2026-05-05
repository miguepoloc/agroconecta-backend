"""Data Mapper — converts between ORM models and domain aggregates."""

from src.identity.user.domain import aggregates as user_aggregates
from src.identity.user.domain import types, value_objects
from src.identity.user.infrastructure import models
from src.shared_kernel.domain import value_objects as shared_value_objects


def orm_to_domain(orm: models.UserOrm) -> user_aggregates.User:
    return user_aggregates.User(
        id=value_objects.UserId(value=orm.id),
        email=value_objects.Email(value=orm.email),
        personal_name=value_objects.PersonalName(
            first_name=orm.first_name, last_name=orm.last_name
        ),
        phone=value_objects.Phone(value=orm.phone),
        password_hash=value_objects.PasswordHash(value=orm.password_hash),
        role=types.UserRole(orm.role),
        status=types.UserStatus(orm.status),
        version=orm.version,
        created_at=shared_value_objects.PosixTime(microseconds=orm.created_at),
        updated_at=shared_value_objects.PosixTime(microseconds=orm.updated_at),
    )


def domain_to_orm(user: user_aggregates.User) -> models.UserOrm:
    return models.UserOrm(
        id=str(user.id),
        email=str(user.email),
        first_name=user.personal_name.first_name,
        last_name=user.personal_name.last_name,
        phone=str(user.phone),
        password_hash=user.password_hash.value,
        role=user.role.value,
        status=user.status.value,
        version=user.version,
        created_at=user.created_at.microseconds,
        updated_at=user.updated_at.microseconds,
    )
