"""Input DTOs for identity use cases."""

import typing

import pydantic

from src.identity.user.domain import types


class RegisterInput(pydantic.BaseModel):
    name: str
    email: str
    password: str
    phone: str
    role: types.UserRole
    region: typing.Optional[str] = None
    department: typing.Optional[str] = None
    bio: typing.Optional[str] = None
    nit: typing.Optional[str] = None
    institution_name: typing.Optional[str] = None
    institution_type: typing.Optional[str] = None


class LoginInput(pydantic.BaseModel):
    email: str
    password: str


class RefreshInput(pydantic.BaseModel):
    refresh_token: str
