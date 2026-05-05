"""Order command handlers."""

import datetime
import decimal

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.shared_kernel.infrastructure import config as app_config
from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.catalog.product.infrastructure import models as product_models
from src.commerce.order.application import unit_of_work as order_uow
from src.commerce.order.application.dtos import inputs, outputs
from src.commerce.order.domain import aggregates, exceptions, types, value_objects
from src.identity.user.domain import types as user_types


def _build_order_output(order: aggregates.Order) -> outputs.OrderOutput:
    return outputs.OrderOutput(
        id=str(order.id),
        order_number=order.order_number,
        type=order.order_type.value,
        status=order.status.value,
        buyer_id=order.buyer_id,
        items=[
            outputs.OrderItemOutput(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price_cop,
                subtotal=item.subtotal,
            )
            for item in order.items
        ],
        subtotal=order.subtotal_cop,
        delivery_fee=order.delivery_fee_cop,
        total=order.total_cop,
        payment_method=order.payment_method.value,
        delivery_date=order.delivery_date,
        delivery_address=outputs.DeliveryAddressOutput(
            street=order.delivery_address.street,
            city=order.delivery_address.city,
            department=order.delivery_address.department,
            postal_code=order.delivery_address.postal_code,
            notes=order.delivery_address.notes,
        ),
        purchase_order_number=order.purchase_order_number,
        created_at=order.created_at.to_isoformat() if order.created_at else "",
        updated_at=order.updated_at.to_isoformat() if order.updated_at else "",
    )


def _resolve_unit_price(
    product: product_models.ProductOrm,
    quantity: decimal.Decimal,
    is_institutional: bool,
) -> decimal.Decimal:
    for vp in sorted(product.volume_prices, key=lambda v: decimal.Decimal(str(v.min_kg)), reverse=True):
        min_kg = decimal.Decimal(str(vp.min_kg))
        max_kg = decimal.Decimal(str(vp.max_kg)) if vp.max_kg else None
        if quantity >= min_kg and (max_kg is None or quantity <= max_kg):
            return decimal.Decimal(str(vp.price_per_kg))
    if is_institutional and product.institutional_price:
        return decimal.Decimal(str(product.institutional_price))
    return decimal.Decimal(str(product.price))


async def handle_place_order(
    command: inputs.PlaceOrderInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    settings: app_config.Settings,
    publisher: event_publisher_port.AbstractEventPublisher,
    buyer_id: str,
    buyer_role: str,
) -> outputs.OrderOutput:
    is_institutional = buyer_role == user_types.UserRole.INSTITUCION.value

    product_ids = [item.product_id for item in command.items]
    stmt = (
        sqlalchemy.select(product_models.ProductOrm)
        .where(product_models.ProductOrm.id.in_(product_ids))
        .options(sqlalchemy.orm.selectinload(product_models.ProductOrm.volume_prices))
    )
    result = await session.execute(stmt)
    products_by_id = {p.id: p for p in result.scalars().all()}

    for item_input in command.items:
        product = products_by_id.get(item_input.product_id)
        if product is None or not product.in_stock:
            raise exceptions.ProductOutOfStockError(item_input.product_id)
        min_lot = decimal.Decimal(str(product.minimum_lot))
        if item_input.quantity < min_lot:
            raise exceptions.MinimumLotNotMetError(
                item_input.product_id, float(min_lot), float(item_input.quantity)
            )

    async with order_uow.OrderUnitOfWork(session) as uow:
        year = datetime.datetime.now(datetime.timezone.utc).year
        count = await uow.orders.count_by_year(year)
        order_number = f"AGC-{year}-{count + 1:05d}"

        order_items = [
            value_objects.OrderItem(
                item_id=value_objects.OrderItemId.generate(),
                product_id=item_input.product_id,
                product_name=products_by_id[item_input.product_id].name,
                quantity=item_input.quantity,
                unit_price_cop=_resolve_unit_price(
                    products_by_id[item_input.product_id],
                    item_input.quantity,
                    is_institutional,
                ),
            )
            for item_input in command.items
        ]

        order = aggregates.Order.place(
            order_number=order_number,
            buyer_id=buyer_id,
            buyer_role=buyer_role,
            items=order_items,
            payment_method=command.payment_method,
            delivery_date=command.delivery_date,
            delivery_address=value_objects.DeliveryAddress(
                street=command.delivery_address.street,
                city=command.delivery_address.city,
                department=command.delivery_address.department,
                postal_code=command.delivery_address.postal_code,
                notes=command.delivery_address.notes,
            ),
            purchase_order_number=command.purchase_order_number,
        )
        await uow.orders.put(order)
        await uow.commit()
        pending_events = list(uow.collect_new_events())

    await publisher.publish_many(pending_events)
    return _build_order_output(order)


async def handle_change_status(
    order_id: str,
    command: inputs.ChangeOrderStatusInput,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    publisher: event_publisher_port.AbstractEventPublisher,
) -> outputs.OrderOutput:
    async with order_uow.OrderUnitOfWork(session) as uow:
        order = await uow.orders.find_by_id(value_objects.OrderId(value=order_id))
        if order is None:
            raise exceptions.OrderNotFoundError(order_id)
        order.change_status(command.status)
        await uow.orders.put(order)
        await uow.commit()
        pending_events = list(uow.collect_new_events())

    await publisher.publish_many(pending_events)
    return _build_order_output(order)
