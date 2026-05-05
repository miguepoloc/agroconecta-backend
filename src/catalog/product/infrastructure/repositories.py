"""SQLAlchemy implementation of ProductRepository."""

import typing

import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm

from src.shared_kernel.domain import value_objects as shared_value_objects
from src.catalog.product.domain import aggregates as product_aggregates
from src.catalog.product.domain import repositories as product_repos
from src.catalog.product.infrastructure import mappers, models


class SqlAlchemyProductRepository(product_repos.ProductRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._seen: set[product_aggregates.Product] = set()

    def _base_stmt(self) -> sqlalchemy.Select[tuple[models.ProductOrm]]:
        return sqlalchemy.select(models.ProductOrm).options(
            sqlalchemy.orm.selectinload(models.ProductOrm.volume_prices),
            sqlalchemy.orm.selectinload(models.ProductOrm.traceability_steps),
        )

    async def put(self, entity: product_aggregates.Product) -> None:
        orm = mappers.domain_to_orm(entity)
        await self._session.merge(orm)
        self._seen.add(entity)

    async def find_by_id(
        self, id: shared_value_objects.DomainId
    ) -> typing.Optional[product_aggregates.Product]:
        stmt = self._base_stmt().where(models.ProductOrm.id == str(id))
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        product = mappers.orm_to_domain(orm)
        self._seen.add(product)
        return product

    async def find_by_slug(
        self, slug: str
    ) -> typing.Optional[product_aggregates.Product]:
        stmt = self._base_stmt().where(models.ProductOrm.slug == slug)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return mappers.orm_to_domain(orm)

    async def find_by_lot_number(
        self, lot_number: str
    ) -> typing.Optional[product_aggregates.Product]:
        stmt = self._base_stmt().where(
            models.ProductOrm.lot_number == lot_number.upper()
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return mappers.orm_to_domain(orm)

    async def find_featured(self, limit: int = 8) -> list[product_aggregates.Product]:
        stmt = (
            self._base_stmt()
            .where(models.ProductOrm.featured == True)  # noqa: E712
            .where(models.ProductOrm.in_stock == True)  # noqa: E712
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.orm_to_domain(row) for row in result.scalars().all()]

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
        stmt = self._base_stmt()
        if category is not None:
            stmt = stmt.where(models.ProductOrm.category == category)
        if in_stock is not None:
            stmt = stmt.where(models.ProductOrm.in_stock == in_stock)
        if farmer_id is not None:
            stmt = stmt.where(models.ProductOrm.farmer_id == farmer_id)
        sort_column = getattr(models.ProductOrm, sort_by, models.ProductOrm.created_at)
        stmt = stmt.order_by(sort_column.desc()).limit(page_size).offset(offset)
        result = await self._session.execute(stmt)
        return [mappers.orm_to_domain(row) for row in result.scalars().all()]
