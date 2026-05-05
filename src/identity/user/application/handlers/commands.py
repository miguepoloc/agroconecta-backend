"""Command handlers for identity use cases."""

import typing

import sqlalchemy.ext.asyncio

from src.shared_kernel.infrastructure import config as app_config
from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.identity.user.application import unit_of_work as user_uow
from src.identity.user.application.dtos import inputs, outputs
from src.identity.user.domain import exceptions as user_exceptions
from src.identity.user.domain import types, value_objects as user_value_objects
from src.identity.user.domain import aggregates as user_aggregates
from src.identity.user.infrastructure import mappers, models
from src.identity.user.infrastructure.adapters import jwt as jwt_adapter
from src.identity.user.infrastructure.adapters import password as password_adapter

# Type alias for refresh token adapters (DynamoRefreshTokenAdapter or StubRefreshTokenAdapter)
RefreshTokenAdapter = typing.Any


def _build_user_output(user: user_aggregates.User) -> outputs.UserOutput:
    return outputs.UserOutput(
        id=str(user.id),
        email=str(user.email),
        first_name=user.personal_name.first_name,
        last_name=user.personal_name.last_name,
        phone=str(user.phone),
        role=user.role,
        status=user.status,
    )


def _build_auth_output(
    user: user_aggregates.User,
    settings: app_config.Settings,
) -> tuple[str, str]:
    access_token = jwt_adapter.create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expire_hours=settings.jwt_access_token_expire_hours,
    )
    raw_refresh = jwt_adapter.generate_refresh_token()
    return access_token, raw_refresh


async def handle_register(
    command: inputs.RegisterInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    settings: app_config.Settings,
    publisher: event_publisher_port.AbstractEventPublisher,
    token_adapter: RefreshTokenAdapter,
) -> outputs.AuthOutput:
    async with user_uow.UserUnitOfWork(session) as uow:
        existing = await uow.users.find_by_email(
            user_value_objects.Email(value=command.email)
        )
        if existing is not None:
            raise user_exceptions.EmailAlreadyExistsError(command.email)

        name_parts = command.name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = user_aggregates.User.register(
            email=user_value_objects.Email(value=command.email),
            first_name=first_name,
            last_name=last_name,
            password_hash=password_adapter.hash_password(command.password),
            phone=user_value_objects.Phone(value=command.phone),
            role=command.role,
        )
        await uow.users.put(user)
        await uow.commit()
        pending_events = list(uow.collect_new_events())

    access_token, raw_refresh = _build_auth_output(user, settings)
    refresh_hash = jwt_adapter.hash_refresh_token(raw_refresh)
    expires_at = jwt_adapter.refresh_token_expires_at(settings.jwt_refresh_token_expire_days)
    await token_adapter.put(
        token_hash=refresh_hash,
        user_id=str(user.id),
        expires_at_unix=expires_at.microseconds // 1_000_000,
    )

    await publisher.publish_many(pending_events)

    return outputs.AuthOutput(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=_build_user_output(user),
    )


async def handle_login(
    command: inputs.LoginInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    settings: app_config.Settings,
    token_adapter: RefreshTokenAdapter,
) -> outputs.AuthOutput:
    async with user_uow.UserUnitOfWork(session) as uow:
        user = await uow.users.find_by_email(
            user_value_objects.Email(value=command.email)
        )
        if user is None:
            raise user_exceptions.InvalidCredentialsError()
        if not user.is_active():
            raise user_exceptions.UserBlockedError()
        if not password_adapter.verify_password(command.password, user.password_hash):
            raise user_exceptions.InvalidCredentialsError()

    access_token, raw_refresh = _build_auth_output(user, settings)
    refresh_hash = jwt_adapter.hash_refresh_token(raw_refresh)
    expires_at = jwt_adapter.refresh_token_expires_at(settings.jwt_refresh_token_expire_days)
    await token_adapter.put(
        token_hash=refresh_hash,
        user_id=str(user.id),
        expires_at_unix=expires_at.microseconds // 1_000_000,
    )

    return outputs.AuthOutput(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=_build_user_output(user),
    )


async def handle_refresh(
    command: inputs.RefreshInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    settings: app_config.Settings,
    token_adapter: RefreshTokenAdapter,
) -> outputs.AuthOutput:
    token_hash = jwt_adapter.hash_refresh_token(command.refresh_token)
    token_data = await token_adapter.find_by_hash(token_hash)
    if token_data is None:
        raise user_exceptions.InvalidCredentialsError()

    await token_adapter.delete_by_hash(token_hash)

    user_orm = await session.get(models.UserOrm, token_data["user_id"])
    if user_orm is None or user_orm.status != types.UserStatus.ACTIVE.value:
        raise user_exceptions.InvalidCredentialsError()

    user = mappers.orm_to_domain(user_orm)

    access_token, raw_refresh = _build_auth_output(user, settings)
    new_hash = jwt_adapter.hash_refresh_token(raw_refresh)
    new_expires = jwt_adapter.refresh_token_expires_at(settings.jwt_refresh_token_expire_days)
    await token_adapter.put(
        token_hash=new_hash,
        user_id=str(user.id),
        expires_at_unix=new_expires.microseconds // 1_000_000,
    )

    return outputs.AuthOutput(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=_build_user_output(user),
    )


async def handle_logout(
    refresh_token: str,
    token_adapter: RefreshTokenAdapter,
) -> None:
    token_hash = jwt_adapter.hash_refresh_token(refresh_token)
    await token_adapter.delete_by_hash(token_hash)
