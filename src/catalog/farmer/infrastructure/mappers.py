"""Data Mapper — Farmer ORM ↔ domain."""

from src.shared_kernel.domain import value_objects as shared_value_objects
from src.catalog.farmer.domain import aggregates as farmer_aggregates
from src.catalog.farmer.domain import types, value_objects
from src.catalog.farmer.infrastructure import models


def certification_orm_to_domain(
    orm: models.CertificationOrm,
) -> farmer_aggregates.Certification:
    return farmer_aggregates.Certification(
        id=orm.id,
        certification_type=types.CertificationType(orm.certification_type),
        issue_date=shared_value_objects.PosixTime(microseconds=orm.issue_date),
        expiry_date=shared_value_objects.PosixTime(microseconds=orm.expiry_date),
        status=orm.status,
    )


def orm_to_domain(orm: models.FarmerOrm) -> farmer_aggregates.Farmer:
    from decimal import Decimal

    return farmer_aggregates.Farmer(
        id=value_objects.FarmerId(value=orm.id),
        user_id=orm.user_id,
        region=value_objects.Region(value=orm.region),
        department=value_objects.Department(value=orm.department),
        bio=orm.bio,
        total_sales=Decimal(str(orm.total_sales)),
        compliance_status=types.ComplianceStatus(orm.compliance_status),
        sustainability_rank=types.SustainabilityRank(orm.sustainability_rank),
        certifications=[certification_orm_to_domain(c) for c in orm.certifications],
        version=orm.version,
        created_at=shared_value_objects.PosixTime(microseconds=orm.created_at),
        updated_at=shared_value_objects.PosixTime(microseconds=orm.updated_at),
    )


def domain_to_orm(farmer: farmer_aggregates.Farmer) -> models.FarmerOrm:
    return models.FarmerOrm(
        id=str(farmer.id),
        user_id=farmer.user_id,
        region=str(farmer.region),
        department=str(farmer.department),
        bio=farmer.bio,
        total_sales=str(farmer.total_sales),
        compliance_status=farmer.compliance_status.value,
        sustainability_rank=farmer.sustainability_rank.value,
        version=farmer.version,
        created_at=farmer.created_at.microseconds,
        updated_at=farmer.updated_at.microseconds,
    )
