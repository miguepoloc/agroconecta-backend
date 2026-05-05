"""Order value objects."""

import decimal

from src.shared_kernel.domain import value_objects as shared_vos


class OrderId(shared_vos.HumanFriendlyId): ...


class OrderItemId(shared_vos.UuidId): ...


class DeliveryAddress(shared_vos.BaseValueObject):
    street: str
    city: str
    department: str
    postal_code: str | None = None
    notes: str | None = None


class OrderItem(shared_vos.BaseValueObject):
    item_id: OrderItemId
    product_id: str
    product_name: str
    quantity: decimal.Decimal
    unit_price_cop: decimal.Decimal

    @property
    def subtotal(self) -> decimal.Decimal:
        return self.quantity * self.unit_price_cop
