"""Output DTOs for identity use cases."""

import pydantic

from src.identity.user.domain import types


class UserOutput(pydantic.BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    role: types.UserRole
    status: types.UserStatus


class AuthOutput(pydantic.BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOutput
