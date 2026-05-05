"""Product domain exceptions."""

from src.shared_kernel.domain import exceptions


class ProductNotFoundError(exceptions.NotFoundError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Product not found: {identifier}")


class ExpiredFarmerCannotSellError(exceptions.BusinessRuleViolationError):
    def __init__(self) -> None:
        super().__init__("Farmer compliance is expired; product cannot be published")
