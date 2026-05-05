"""Order aggregate root."""

import datetime
import decimal

from src.shared_kernel.domain import aggregates, value_objects as shared_vos
from src.commerce.order.domain import events, exceptions, types, value_objects


_FREE_DELIVERY_THRESHOLD = decimal.Decimal("200000")
_DELIVERY_FEE = decimal.Decimal("15000")


class Order(aggregates.BaseAggregateRoot):
    order_number: str
    buyer_id: str
    order_type: types.OrderType
    status: types.OrderStatus
    items: list[value_objects.OrderItem]
    subtotal_cop: decimal.Decimal
    delivery_fee_cop: decimal.Decimal
    total_cop: decimal.Decimal
    payment_method: types.PaymentMethod
    delivery_date: datetime.date
    delivery_address: value_objects.DeliveryAddress
    purchase_order_number: str | None = None

    @classmethod
    def place(
        cls,
        order_number: str,
        buyer_id: str,
        buyer_role: str,
        items: list[value_objects.OrderItem],
        payment_method: types.PaymentMethod,
        delivery_date: datetime.date,
        delivery_address: value_objects.DeliveryAddress,
        purchase_order_number: str | None = None,
    ) -> "Order":
        subtotal = sum((item.subtotal for item in items), decimal.Decimal("0"))
        is_institutional = buyer_role == "institucion"
        order_type = types.OrderType.INSTITUTIONAL if is_institutional else types.OrderType.INDIVIDUAL
        delivery_fee = (
            decimal.Decimal("0")
            if is_institutional or subtotal >= _FREE_DELIVERY_THRESHOLD
            else _DELIVERY_FEE
        )
        order = cls(
            id=value_objects.OrderId.generate(),
            order_number=order_number,
            buyer_id=buyer_id,
            order_type=order_type,
            status=types.OrderStatus.PENDING,
            items=items,
            subtotal_cop=subtotal,
            delivery_fee_cop=delivery_fee,
            total_cop=subtotal + delivery_fee,
            payment_method=payment_method,
            delivery_date=delivery_date,
            delivery_address=delivery_address,
            purchase_order_number=purchase_order_number,
        )
        order.record_event(
            events.OrderPlaced(
                aggregate_id=str(order.id),
                order_id=str(order.id),
                order_number=order_number,
                buyer_id=buyer_id,
                total_cop=str(order.total_cop),
                order_type=order_type.value,
            )
        )
        return order

    def change_status(self, new_status: types.OrderStatus) -> None:
        if not types.is_valid_transition(self.status, new_status):
            raise exceptions.InvalidStatusTransitionError(
                self.status.value, new_status.value
            )
        previous = self.status
        self.status = new_status
        self.touch()
        self.record_event(
            events.OrderStatusChanged(
                aggregate_id=str(self.id),
                order_id=str(self.id),
                order_number=self.order_number,
                previous_status=previous.value,
                new_status=new_status.value,
            )
        )
