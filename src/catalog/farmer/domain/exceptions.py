"""Farmer domain exceptions."""

from src.shared_kernel.domain import exceptions


class FarmerNotFoundError(exceptions.NotFoundError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Farmer not found: {identifier}")


class FarmerExpiredError(exceptions.BusinessRuleViolationError):
    def __init__(self) -> None:
        super().__init__("Farmer compliance is expired and cannot sell")
