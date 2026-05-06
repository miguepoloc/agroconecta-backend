"""Unit of Work for the order context."""

import sqlalchemy.ext.asyncio

from src.commerce.order.domain import repositories as order_repos
from src.commerce.order.infrastructure import repositories as order_infra_repos
from src.shared_kernel.infrastructure import uow


class OrderUnitOfWork(uow.FastAPIUnitOfWork):
    orders: order_repos.OrderRepository

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__(session)
        self.orders = order_infra_repos.SqlAlchemyOrderRepository(session)

    def _repositories(self) -> list[order_repos.OrderRepository]:  # type: ignore[override]
        return [self.orders]
