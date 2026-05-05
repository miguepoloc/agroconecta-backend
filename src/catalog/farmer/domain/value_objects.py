"""Value objects for the Farmer domain."""

import pydantic

from src.shared_kernel.domain import value_objects


class FarmerId(value_objects.UuidId):
    pass


class Region(value_objects.BaseValueObject):
    value: str

    @pydantic.field_validator("value")
    @classmethod
    def validate_region(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Region cannot be empty")
        return v

    def __str__(self) -> str:
        return self.value


class Department(value_objects.BaseValueObject):
    value: str

    @pydantic.field_validator("value")
    @classmethod
    def validate_department(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Department cannot be empty")
        return v

    def __str__(self) -> str:
        return self.value
