"""FastAPI shared dependencies."""

import typing

import fastapi

from src.shared_kernel.infrastructure import config as app_config
from src.identity.user.domain import aggregates as user_aggregates
from src.identity.user.infrastructure import repositories as user_repos
from src.identity.user.infrastructure.adapters import jwt as jwt_adapter


async def get_current_user(
    request: fastapi.Request,
    authorization: typing.Annotated[
        typing.Optional[str], fastapi.Header(alias="Authorization")
    ] = None,
) -> user_aggregates.User:
    settings = app_config.get_settings()
    if authorization is None or not authorization.startswith("Bearer "):
        raise fastapi.HTTPException(status_code=401, detail="Missing token")

    token = authorization.removeprefix("Bearer ").strip()
    payload = jwt_adapter.decode_access_token(
        token, settings.jwt_secret_key, settings.jwt_algorithm
    )
    if payload is None:
        raise fastapi.HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise fastapi.HTTPException(status_code=401, detail="Invalid token payload")

    session = request.state.db_session
    repo = user_repos.SqlAlchemyUserRepository(session)

    from src.shared_kernel.domain import value_objects
    from src.identity.user.domain import value_objects as user_vos

    user = await repo.find_by_id(user_vos.UserId(value=user_id))
    if user is None or not user.is_active():
        raise fastapi.HTTPException(status_code=401, detail="User not found or inactive")

    request.state.current_user = user
    return user


CurrentUser = typing.Annotated[user_aggregates.User, fastapi.Depends(get_current_user)]
