"""Order domain enums."""

import enum


class OrderStatus(enum.StrEnum):
    PENDING = "pendiente"
    CONFIRMED = "confirmado"
    IN_TRANSIT = "en_camino"
    DELIVERED = "entregado"
    CANCELLED = "cancelado"


class OrderType(enum.StrEnum):
    INDIVIDUAL = "individual"
    INSTITUTIONAL = "institucional"


class PaymentMethod(enum.StrEnum):
    CARD = "tarjeta"
    PSE = "pse"
    NEQUI = "nequi"


_VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED},
    OrderStatus.IN_TRANSIT: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


def is_valid_transition(current: OrderStatus, next_status: OrderStatus) -> bool:
    return next_status in _VALID_TRANSITIONS.get(current, set())
