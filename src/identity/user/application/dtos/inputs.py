"""Input DTOs for identity use cases."""

import pydantic

from src.identity.user.domain import types


class RegisterInput(pydantic.BaseModel):
    name: str
    email: str
    password: str
    phone: str
    role: types.UserRole
    region: str | None = None
    department: str | None = None
    bio: str | None = None
    nit: str | None = None
    institution_name: str | None = None
    institution_type: str | None = None


class LoginInput(pydantic.BaseModel):
    email: str
    password: str


class RefreshInput(pydantic.BaseModel):
    refresh_token: str
