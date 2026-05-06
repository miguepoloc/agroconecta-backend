"""Farmer repository port."""

import abc

from src.catalog.farmer.domain import aggregates as farmer_aggregates
from src.catalog.farmer.domain import types
from src.shared_kernel.application.ports import repositories


class FarmerRepository(repositories.Repository[farmer_aggregates.Farmer]):
    def model_type(self) -> type[farmer_aggregates.Farmer]:
        return farmer_aggregates.Farmer

    @abc.abstractmethod
    async def find_by_user_id(self, user_id: str) -> farmer_aggregates.Farmer | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_gold_farmers(self, limit: int = 6) -> list[farmer_aggregates.Farmer]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_all_filtered(
        self,
        compliance_status: types.ComplianceStatus | None = None,
        rank: types.SustainabilityRank | None = None,
        page_size: int = 20,
        offset: int = 0,
    ) -> list[farmer_aggregates.Farmer]:
        raise NotImplementedError
