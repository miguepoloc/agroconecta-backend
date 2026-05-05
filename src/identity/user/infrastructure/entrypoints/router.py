"""Auth API router — /api/v1/auth/*"""

import typing

import fastapi

from src.shared_kernel.infrastructure import config as app_config
from src.identity.user.application.dtos import inputs, outputs
from src.identity.user.application.handlers import commands
from src.identity.user.domain import aggregates as user_aggregates

router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


async def _get_settings() -> typing.AsyncGenerator[app_config.Settings, None]:
    yield app_config.get_settings()


SettingsDep = typing.Annotated[app_config.Settings, fastapi.Depends(_get_settings)]


@router.post("/register", response_model=outputs.AuthOutput, status_code=201)
async def register(
    body: inputs.RegisterInput,
    settings: SettingsDep,
    request: fastapi.Request,
) -> outputs.AuthOutput:
    return await commands.handle_register(
        command=body,
        session=request.state.db_session,
        settings=settings,
        publisher=request.app.state.event_publisher,
        token_adapter=request.app.state.token_adapter,
    )


@router.post("/login", response_model=outputs.AuthOutput)
async def login(
    body: inputs.LoginInput,
    settings: SettingsDep,
    request: fastapi.Request,
) -> outputs.AuthOutput:
    return await commands.handle_login(
        command=body,
        session=request.state.db_session,
        settings=settings,
        token_adapter=request.app.state.token_adapter,
    )


@router.post("/refresh", response_model=outputs.AuthOutput)
async def refresh(
    body: inputs.RefreshInput,
    settings: SettingsDep,
    request: fastapi.Request,
) -> outputs.AuthOutput:
    return await commands.handle_refresh(
        command=body,
        session=request.state.db_session,
        settings=settings,
        token_adapter=request.app.state.token_adapter,
    )


@router.post("/logout", status_code=204)
async def logout(
    body: inputs.RefreshInput,
    request: fastapi.Request,
) -> None:
    await commands.handle_logout(
        refresh_token=body.refresh_token,
        token_adapter=request.app.state.token_adapter,
    )


@router.get("/me", response_model=outputs.UserOutput)
async def me(
    current_user: typing.Annotated[
        user_aggregates.User, fastapi.Depends(lambda r: r.state.current_user)
    ],
) -> outputs.UserOutput:
    return outputs.UserOutput(
        id=str(current_user.id),
        email=str(current_user.email),
        first_name=current_user.personal_name.first_name,
        last_name=current_user.personal_name.last_name,
        phone=str(current_user.phone),
        role=current_user.role,
        status=current_user.status,
    )
