"""Product repository port."""

import abc

from src.catalog.product.domain import aggregates as product_aggregates
from src.shared_kernel.application.ports import repositories


class ProductRepository(repositories.Repository[product_aggregates.Product]):
    def model_type(self) -> type[product_aggregates.Product]:
        return product_aggregates.Product

    @abc.abstractmethod
    async def find_by_slug(self, slug: str) -> product_aggregates.Product | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_lot_number(self, lot_number: str) -> product_aggregates.Product | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_featured(self, limit: int = 8) -> list[product_aggregates.Product]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_all_filtered(
        self,
        category: str | None = None,
        certification: str | None = None,
        in_stock: bool | None = None,
        farmer_id: str | None = None,
        sort_by: str = "created_at",
        page_size: int = 20,
        offset: int = 0,
    ) -> list[product_aggregates.Product]:
        raise NotImplementedError
