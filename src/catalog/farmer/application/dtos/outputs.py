"""Output DTOs for the farmer context."""

import typing

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
    bio: typing.Optional[str]
    total_sales: str
    compliance_status: types.ComplianceStatus
    sustainability_rank: types.SustainabilityRank
    certifications: list[CertificationOutput]
    # Identity fields expected by frontend
    name: typing.Optional[str] = None
    avatar: typing.Optional[str] = None
    quote: typing.Optional[str] = None
    email: typing.Optional[str] = None
    phone: typing.Optional[str] = None
    active_products: typing.Optional[int] = 0
    joined_date: typing.Optional[str] = None


class FarmerDetailOutput(FarmerSummaryOutput):
    pass
