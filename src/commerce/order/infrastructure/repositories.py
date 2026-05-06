"""SQLAlchemy order repository implementation."""

import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm

from src.commerce.order.domain import aggregates, value_objects
from src.commerce.order.domain import repositories as order_repos
from src.commerce.order.infrastructure import mappers, models


class SqlAlchemyOrderRepository(order_repos.OrderRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        super().__init__()
        self._session = session
        self._seen: set[aggregates.Order] = set()

    async def put(self, order: aggregates.Order) -> None:
        orm = mappers.domain_to_orm(order)
        await self._session.merge(orm)
        self._seen.add(order)

    async def find_by_id(  # type: ignore[override]
        self, order_id: value_objects.OrderId
    ) -> aggregates.Order | None:
        stmt = (
            sqlalchemy.select(models.OrderOrm)
            .where(models.OrderOrm.id == str(order_id))
            .options(sqlalchemy.orm.selectinload(models.OrderOrm.items))
        )
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return mappers.orm_to_domain(orm) if orm else None

    async def find_by_buyer(
        self, buyer_id: str, limit: int = 20, offset: int = 0
    ) -> list[aggregates.Order]:
        stmt = (
            sqlalchemy.select(models.OrderOrm)
            .where(models.OrderOrm.buyer_id == buyer_id)
            .options(sqlalchemy.orm.selectinload(models.OrderOrm.items))
            .order_by(models.OrderOrm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [mappers.orm_to_domain(row) for row in result.scalars().all()]

    async def count_by_year(self, year: int) -> int:
        stmt = sqlalchemy.select(sqlalchemy.func.count()).where(
            models.OrderOrm.order_number.like(f"AGC-{year}-%")
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def find_all(  # type: ignore[override]
        self,
        status: str | None = None,
        order_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[aggregates.Order]:
        stmt = sqlalchemy.select(models.OrderOrm).options(
            sqlalchemy.orm.selectinload(models.OrderOrm.items)
        )
        if status:
            stmt = stmt.where(models.OrderOrm.status == status)
        if order_type:
            stmt = stmt.where(models.OrderOrm.order_type == order_type)
        stmt = stmt.order_by(models.OrderOrm.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [mappers.orm_to_domain(row) for row in result.scalars().all()]
