"""Core value objects for the shared kernel."""

import datetime
import decimal
import secrets
import string
import typing
import uuid

import pydantic

from src.shared_kernel.domain import base_model


class BaseValueObject(base_model.DomainModel):
    model_config = pydantic.ConfigDict(frozen=True)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.model_dump().items())))


class DomainId(BaseValueObject):
    value: str

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


class UuidId(DomainId):
    @classmethod
    def generate(cls) -> "UuidId":
        return cls(value=str(uuid.uuid4()))

    @pydantic.field_validator("value")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        uuid.UUID(v)
        return v


class HumanFriendlyId(DomainId):
    @classmethod
    def generate(cls, length: int = 10) -> "HumanFriendlyId":
        chars = string.ascii_uppercase + string.digits
        return cls(value="".join(secrets.choice(chars) for _ in range(length)))


class NumericId(BaseValueObject):
    value: int

    def __str__(self) -> str:
        return str(self.value)


class PosixTime(BaseValueObject):
    """datetime.UTC microseconds since Unix epoch."""

    microseconds: int

    @classmethod
    def now(cls) -> "PosixTime":
        dt = datetime.datetime.now(tz=datetime.UTC)
        return cls(microseconds=int(dt.timestamp() * 1_000_000))

    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> "PosixTime":
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.UTC)
        return cls(microseconds=int(dt.timestamp() * 1_000_000))

    @classmethod
    def from_isoformat(cls, iso_str: str) -> "PosixTime":
        return cls.from_datetime(datetime.datetime.fromisoformat(iso_str))

    def to_datetime(self, tz: datetime.timezone = datetime.UTC) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.microseconds / 1_000_000, tz=tz)

    def to_isoformat(self) -> str:
        return self.to_datetime().isoformat()

    def add_days(self, days: int) -> "PosixTime":
        return PosixTime(microseconds=self.microseconds + days * 86_400 * 1_000_000)

    def add_hours(self, hours: int) -> "PosixTime":
        return PosixTime(microseconds=self.microseconds + hours * 3_600 * 1_000_000)

    def __lt__(self, other: "PosixTime") -> bool:
        return self.microseconds < other.microseconds

    def __le__(self, other: "PosixTime") -> bool:
        return self.microseconds <= other.microseconds

    def __gt__(self, other: "PosixTime") -> bool:
        return self.microseconds > other.microseconds

    def __ge__(self, other: "PosixTime") -> bool:
        return self.microseconds >= other.microseconds


class Money(BaseValueObject):
    amount: decimal.Decimal
    currency: str = "COP"

    @pydantic.field_validator("amount", mode="before")
    @classmethod
    def coerce_decimal(cls, v: typing.Any) -> decimal.Decimal:
        return decimal.Decimal(str(v))

    @classmethod
    def cop(cls, amount: decimal.Decimal | int | str) -> "Money":
        return cls(amount=decimal.Decimal(str(amount)), currency="COP")

    @classmethod
    def zero_cop(cls) -> "Money":
        return cls.cop(decimal.Decimal("0"))

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: decimal.Decimal | int | str) -> "Money":
        result = self.amount * decimal.Decimal(str(factor))
        return Money(
            amount=result.quantize(decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP),
            currency=self.currency,
        )

    def is_zero(self) -> bool:
        return self.amount == decimal.Decimal("0")

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.0f}"


class NonNegativeMoney(Money):
    @pydantic.field_validator("amount")
    @classmethod
    def must_be_non_negative(cls, v: decimal.Decimal) -> decimal.Decimal:
        if v < decimal.Decimal("0"):
            raise ValueError("Amount must be >= 0")
        return v


class PositiveMoney(Money):
    @pydantic.field_validator("amount")
    @classmethod
    def must_be_positive(cls, v: decimal.Decimal) -> decimal.Decimal:
        if v <= decimal.Decimal("0"):
            raise ValueError("Amount must be > 0")
        return v
