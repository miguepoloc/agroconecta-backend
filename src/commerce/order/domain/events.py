"""Order domain events."""

from src.shared_kernel.domain import events


class OrderPlaced(events.DomainEvent):
    order_id: str
    order_number: str
    buyer_id: str
    total_cop: str
    order_type: str


class OrderStatusChanged(events.DomainEvent):
    order_id: str
    order_number: str
    previous_status: str
    new_status: str
