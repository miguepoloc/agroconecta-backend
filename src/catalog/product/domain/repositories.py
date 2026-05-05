"""Product repository port."""

import abc
import typing

from src.shared_kernel.application.ports import repositories
from src.catalog.product.domain import aggregates as product_aggregates


class ProductRepository(repositories.Repository[product_aggregates.Product]):
    def model_type(self) -> type[product_aggregates.Product]:
        return product_aggregates.Product

    @abc.abstractmethod
    async def find_by_slug(
        self, slug: str
    ) -> typing.Optional[product_aggregates.Product]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_lot_number(
        self, lot_number: str
    ) -> typing.Optional[product_aggregates.Product]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_featured(
        self, limit: int = 8
    ) -> list[product_aggregates.Product]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_all_filtered(
        self,
        category: typing.Optional[str] = None,
        certification: typing.Optional[str] = None,
        in_stock: typing.Optional[bool] = None,
        farmer_id: typing.Optional[str] = None,
        sort_by: str = "created_at",
        page_size: int = 20,
        offset: int = 0,
    ) -> list[product_aggregates.Product]:
        raise NotImplementedError
