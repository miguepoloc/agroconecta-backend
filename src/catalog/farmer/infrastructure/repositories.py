"""SQLAlchemy implementation of FarmerRepository."""

import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm

from src.catalog.farmer.domain import aggregates as farmer_aggregates
from src.catalog.farmer.domain import repositories as farmer_repos
from src.catalog.farmer.domain import types
from src.catalog.farmer.infrastructure import mappers, models
from src.shared_kernel.domain import value_objects as shared_value_objects


class SqlAlchemyFarmerRepository(farmer_repos.FarmerRepository):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._seen: set[farmer_aggregates.Farmer] = set()

    def _base_stmt(self) -> sqlalchemy.Select[tuple[models.FarmerOrm]]:
        return sqlalchemy.select(models.FarmerOrm).options(
            sqlalchemy.orm.selectinload(models.FarmerOrm.certifications)
        )

    async def put(self, entity: farmer_aggregates.Farmer) -> None:
        orm = mappers.domain_to_orm(entity)
        await self._session.merge(orm)
        self._seen.add(entity)

    async def find_by_id(
        self, id: shared_value_objects.DomainId
    ) -> farmer_aggregates.Farmer | None:
        stmt = self._base_stmt().where(models.FarmerOrm.id == str(id))
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        farmer = mappers.orm_to_domain(orm)
        self._seen.add(farmer)
        return farmer

    async def find_by_user_id(self, user_id: str) -> farmer_aggregates.Farmer | None:
        stmt = self._base_stmt().where(models.FarmerOrm.user_id == user_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        farmer = mappers.orm_to_domain(orm)
        self._seen.add(farmer)
        return farmer

    async def find_gold_farmers(self, limit: int = 6) -> list[farmer_aggregates.Farmer]:
        stmt = (
            self._base_stmt()
            .where(models.FarmerOrm.sustainability_rank == "gold")
            .where(models.FarmerOrm.compliance_status == "active")
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.orm_to_domain(row) for row in result.scalars().all()]

    async def find_all_filtered(
        self,
        compliance_status: types.ComplianceStatus | None = None,
        rank: types.SustainabilityRank | None = None,
        page_size: int = 20,
        offset: int = 0,
    ) -> list[farmer_aggregates.Farmer]:
        stmt = self._base_stmt()
        if compliance_status is not None:
            stmt = stmt.where(models.FarmerOrm.compliance_status == compliance_status.value)
        if rank is not None:
            stmt = stmt.where(models.FarmerOrm.sustainability_rank == rank.value)
        stmt = stmt.limit(page_size).offset(offset)
        result = await self._session.execute(stmt)
        return [mappers.orm_to_domain(row) for row in result.scalars().all()]
