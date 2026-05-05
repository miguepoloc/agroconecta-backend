"""Value objects for the Product domain."""

import re

import pydantic

from src.shared_kernel.domain import value_objects


class ProductId(value_objects.UuidId):
    pass


class Slug(value_objects.BaseValueObject):
    value: str

    @pydantic.field_validator("value")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(f"Invalid slug: {v}")
        return v

    def __str__(self) -> str:
        return self.value


class LotNumber(value_objects.BaseValueObject):
    """Format: LOT-YYYY-MMDD-XX"""

    value: str

    @pydantic.field_validator("value")
    @classmethod
    def validate_lot_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^LOT-\d{4}-\d{4}-\d{2}$", v):
            raise ValueError(f"Invalid lot number format: {v}. Expected LOT-YYYY-MMDD-XX")
        return v

    def __str__(self) -> str:
        return self.value


class FreshnessScore(value_objects.BaseValueObject):
    """Score from 0 to 100. freshnessScore = max(0, 100 - days_since_harvest * 3)"""

    value: int

    @pydantic.field_validator("value")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("FreshnessScore must be between 0 and 100")
        return v

    @classmethod
    def calculate(cls, days_since_harvest: int) -> "FreshnessScore":
        score = max(0, 100 - days_since_harvest * 3)
        return cls(value=score)

    def is_stale(self) -> bool:
        return self.value == 0
