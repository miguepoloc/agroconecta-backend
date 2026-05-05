"""Order repository port."""

import abc

from src.shared_kernel.application.ports import repositories
from src.commerce.order.domain import aggregates, value_objects


class OrderRepository(repositories.Repository[aggregates.Order]):
    def model_type(self) -> type[aggregates.Order]:
        return aggregates.Order

    @abc.abstractmethod
    async def find_by_id(
        self, order_id: value_objects.OrderId
    ) -> aggregates.Order | None: ...

    @abc.abstractmethod
    async def find_by_buyer(
        self, buyer_id: str, limit: int = 20, offset: int = 0
    ) -> list[aggregates.Order]: ...

    @abc.abstractmethod
    async def count_by_year(self, year: int) -> int: ...

    @abc.abstractmethod
    async def find_all(
        self,
        status: str | None = None,
        order_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[aggregates.Order]: ...
