"""Output DTOs for the farmer context."""

import pydantic

from src.catalog.farmer.domain import types


class CertificationOutput(pydantic.BaseModel):
    id: str
    certification_type: types.CertificationType
    issue_date: str
    expiry_date: str
    status: str


class FarmerSummaryOutput(pydantic.BaseModel):
    id: str
    user_id: str
    region: str
    department: str
    bio: str | None
    total_sales: str
    compliance_status: types.ComplianceStatus
    sustainability_rank: types.SustainabilityRank
    certifications: list[CertificationOutput]
    # Identity fields expected by frontend
    name: str | None = None
    avatar: str | None = None
    quote: str | None = None
    email: str | None = None
    phone: str | None = None
    active_products: int | None = 0
    joined_date: str | None = None


class FarmerDetailOutput(FarmerSummaryOutput):
    pass
