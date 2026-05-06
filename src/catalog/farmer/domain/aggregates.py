"""Farmer aggregate root."""

from decimal import Decimal

import pydantic

from src.catalog.farmer.domain import events as farmer_events
from src.catalog.farmer.domain import types, value_objects
from src.shared_kernel.domain import aggregates
from src.shared_kernel.domain import value_objects as shared_value_objects


class Certification(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    certification_type: types.CertificationType
    issue_date: shared_value_objects.PosixTime
    expiry_date: shared_value_objects.PosixTime
    status: str = "active"


class Farmer(aggregates.BaseAggregateRoot):
    id: value_objects.FarmerId
    user_id: str
    region: value_objects.Region
    department: value_objects.Department
    bio: str | None = None
    total_sales: Decimal = Decimal("0")
    compliance_status: types.ComplianceStatus = types.ComplianceStatus.ACTIVE
    sustainability_rank: types.SustainabilityRank = types.SustainabilityRank.BRONZE
    certifications: list[Certification] = pydantic.Field(default_factory=list)

    def suspend(self, reason: str) -> None:
        old_status = self.compliance_status
        self.compliance_status = types.ComplianceStatus.EXPIRED
        self.touch()
        self.record_event(
            farmer_events.FarmerSuspended(
                aggregate_id=str(self.id), farmer_id=str(self.id), reason=reason
            )
        )
        self.record_event(
            farmer_events.ComplianceStatusChanged(
                aggregate_id=str(self.id),
                farmer_id=str(self.id),
                old_status=old_status.value,
                new_status=self.compliance_status.value,
            )
        )

    def reactivate(self) -> None:
        old_status = self.compliance_status
        self.compliance_status = types.ComplianceStatus.ACTIVE
        self.touch()
        self.record_event(
            farmer_events.FarmerReactivated(aggregate_id=str(self.id), farmer_id=str(self.id))
        )
        self.record_event(
            farmer_events.ComplianceStatusChanged(
                aggregate_id=str(self.id),
                farmer_id=str(self.id),
                old_status=old_status.value,
                new_status=self.compliance_status.value,
            )
        )

    def can_sell(self) -> bool:
        return self.compliance_status != types.ComplianceStatus.EXPIRED
