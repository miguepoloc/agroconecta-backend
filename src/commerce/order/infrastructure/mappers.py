"""ORM ↔ domain mappers for the order context."""

import datetime
import decimal

from src.shared_kernel.domain import value_objects as shared_vos
from src.commerce.order.domain import aggregates, types, value_objects
from src.commerce.order.infrastructure import models


def orm_to_domain(orm: models.OrderOrm) -> aggregates.Order:
    items = [_item_orm_to_domain(i) for i in orm.items]
    delivery_date = datetime.date.fromtimestamp(orm.delivery_date / 1_000_000)
    return aggregates.Order(
        id=value_objects.OrderId(value=orm.id),
        order_number=orm.order_number,
        buyer_id=orm.buyer_id,
        order_type=types.OrderType(orm.order_type),
        status=types.OrderStatus(orm.status),
        items=items,
        subtotal_cop=decimal.Decimal(str(orm.subtotal_cop)),
        delivery_fee_cop=decimal.Decimal(str(orm.delivery_fee_cop)),
        total_cop=decimal.Decimal(str(orm.total_cop)),
        payment_method=types.PaymentMethod(orm.payment_method),
        delivery_date=delivery_date,
        delivery_address=value_objects.DeliveryAddress(
            street=orm.delivery_street,
            city=orm.delivery_city,
            department=orm.delivery_department,
            postal_code=orm.delivery_postal_code,
            notes=orm.delivery_notes,
        ),
        purchase_order_number=orm.purchase_order_number,
        version=orm.version,
        created_at=shared_vos.PosixTime(microseconds=orm.created_at),
        updated_at=shared_vos.PosixTime(microseconds=orm.updated_at),
    )


def domain_to_orm(order: aggregates.Order) -> models.OrderOrm:
    now = shared_vos.PosixTime.now().microseconds
    delivery_ts = int(
        datetime.datetime.combine(order.delivery_date, datetime.time.min)
        .replace(tzinfo=datetime.timezone.utc)
        .timestamp()
        * 1_000_000
    )
    orm = models.OrderOrm(
        id=str(order.id),
        order_number=order.order_number,
        buyer_id=order.buyer_id,
        order_type=order.order_type.value,
        status=order.status.value,
        subtotal_cop=str(order.subtotal_cop),
        delivery_fee_cop=str(order.delivery_fee_cop),
        total_cop=str(order.total_cop),
        payment_method=order.payment_method.value,
        delivery_date=delivery_ts,
        delivery_street=order.delivery_address.street,
        delivery_city=order.delivery_address.city,
        delivery_department=order.delivery_address.department,
        delivery_postal_code=order.delivery_address.postal_code,
        delivery_notes=order.delivery_address.notes,
        purchase_order_number=order.purchase_order_number,
        version=order.version,
        created_at=order.created_at.microseconds if order.created_at else now,
        updated_at=order.updated_at.microseconds if order.updated_at else now,
        items=[_item_domain_to_orm(i, str(order.id)) for i in order.items],
    )
    return orm


def _item_orm_to_domain(orm: models.OrderItemOrm) -> value_objects.OrderItem:
    return value_objects.OrderItem(
        item_id=value_objects.OrderItemId(value=orm.id),
        product_id=orm.product_id,
        product_name=orm.product_name,
        quantity=decimal.Decimal(str(orm.quantity)),
        unit_price_cop=decimal.Decimal(str(orm.unit_price_cop)),
    )


def _item_domain_to_orm(item: value_objects.OrderItem, order_id: str) -> models.OrderItemOrm:
    now = shared_vos.PosixTime.now().microseconds
    return models.OrderItemOrm(
        id=str(item.item_id),
        order_id=order_id,
        product_id=item.product_id,
        product_name=item.product_name,
        quantity=str(item.quantity),
        unit_price_cop=str(item.unit_price_cop),
        created_at=now,
    )
