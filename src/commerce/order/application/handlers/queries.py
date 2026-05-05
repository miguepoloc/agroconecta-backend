"""Order query handlers."""

import sqlalchemy.ext.asyncio

from src.commerce.order.application import unit_of_work as order_uow
from src.commerce.order.application.dtos import outputs
from src.commerce.order.application.handlers import commands as cmd_handlers
from src.commerce.order.domain import exceptions, value_objects


async def handle_get_order(
    order_id: str,
    buyer_id: str,
    is_admin: bool,
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> outputs.OrderOutput:
    async with order_uow.OrderUnitOfWork(session) as uow:
        order = await uow.orders.find_by_id(value_objects.OrderId(value=order_id))
    if order is None:
        raise exceptions.OrderNotFoundError(order_id)
    if not is_admin and order.buyer_id != buyer_id:
        raise exceptions.OrderNotFoundError(order_id)
    return cmd_handlers._build_order_output(order)


async def handle_list_my_orders(
    buyer_id: str,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    limit: int = 20,
    offset: int = 0,
) -> list[outputs.OrderSummaryOutput]:
    async with order_uow.OrderUnitOfWork(session) as uow:
        orders = await uow.orders.find_by_buyer(buyer_id, limit=limit, offset=offset)
    return [
        outputs.OrderSummaryOutput(
            id=str(o.id),
            order_number=o.order_number,
            type=o.order_type.value,
            status=o.status.value,
            total=o.total_cop,
            item_count=len(o.items),
            created_at=o.created_at.to_isoformat() if o.created_at else "",
        )
        for o in orders
    ]


async def handle_list_all_orders(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    status: str | None = None,
    order_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[outputs.OrderSummaryOutput]:
    async with order_uow.OrderUnitOfWork(session) as uow:
        orders = await uow.orders.find_all(
            status=status, order_type=order_type, limit=limit, offset=offset
        )
    return [
        outputs.OrderSummaryOutput(
            id=str(o.id),
            order_number=o.order_number,
            type=o.order_type.value,
            status=o.status.value,
            total=o.total_cop,
            item_count=len(o.items),
            created_at=o.created_at.to_isoformat() if o.created_at else "",
        )
        for o in orders
    ]
