"""Order domain exceptions."""

from src.shared_kernel.domain import exceptions as shared_exceptions


class OrderNotFoundError(shared_exceptions.NotFoundError): ...


class InvalidStatusTransitionError(shared_exceptions.DomainException):
    def __init__(self, current: str, requested: str) -> None:
        super().__init__(f"Cannot transition order from '{current}' to '{requested}'")


class ProductOutOfStockError(shared_exceptions.DomainException):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"Product '{product_id}' is out of stock")


class MinimumLotNotMetError(shared_exceptions.DomainException):
    def __init__(self, product_id: str, minimum: float, requested: float) -> None:
        super().__init__(f"Product '{product_id}' requires minimum {minimum} kg, got {requested}")
