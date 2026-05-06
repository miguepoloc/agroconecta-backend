"""Value objects for the User domain."""

import re

import pydantic

from src.shared_kernel.domain import value_objects


class UserId(value_objects.HumanFriendlyId):
    @classmethod
    def generate(cls, length: int = 10) -> "UserId":
        base = value_objects.HumanFriendlyId.generate(length=length)
        return cls(value=base.value)


class Email(value_objects.BaseValueObject):
    value: str

    @pydantic.field_validator("value")
    @classmethod
    def normalize_and_validate(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError(f"Invalid email: {v}")
        return v

    def __str__(self) -> str:
        return self.value


class PersonalName(value_objects.BaseValueObject):
    first_name: str
    last_name: str

    @pydantic.field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not 1 <= len(v) <= 100:
            raise ValueError("Name must be between 1 and 100 characters")
        return v

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Phone(value_objects.BaseValueObject):
    value: str

    @pydantic.field_validator("value")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            raise ValueError(f"Invalid phone number: {v}")
        return cleaned

    def __str__(self) -> str:
        return self.value


class PasswordHash(value_objects.BaseValueObject):
    value: str

    def __repr__(self) -> str:
        return "PasswordHash(***)"

    def __str__(self) -> str:
        return "***"
