"""Query handlers for the farmer context."""

import typing

import sqlalchemy.ext.asyncio

from src.catalog.farmer.application.dtos import outputs
from src.catalog.farmer.domain import aggregates as farmer_aggregates
from src.catalog.farmer.domain import exceptions as farmer_exceptions
from src.catalog.farmer.domain import types
from src.catalog.farmer.infrastructure import repositories as farmer_repos


def _to_output(farmer: farmer_aggregates.Farmer) -> outputs.FarmerSummaryOutput:
    return outputs.FarmerSummaryOutput(
        id=str(farmer.id),
        user_id=farmer.user_id,
        region=str(farmer.region),
        department=str(farmer.department),
        bio=farmer.bio,
        total_sales=str(farmer.total_sales),
        compliance_status=farmer.compliance_status,
        sustainability_rank=farmer.sustainability_rank,
        certifications=[
            outputs.CertificationOutput(
                id=cert.id,
                certification_type=cert.certification_type,
                issue_date=cert.issue_date.to_isoformat(),
                expiry_date=cert.expiry_date.to_isoformat(),
                status=cert.status,
            )
            for cert in farmer.certifications
        ],
    )


async def handle_list_farmers(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    compliance_status: typing.Optional[types.ComplianceStatus] = None,
    rank: typing.Optional[types.SustainabilityRank] = None,
    page_size: int = 20,
    offset: int = 0,
) -> list[outputs.FarmerSummaryOutput]:
    repo = farmer_repos.SqlAlchemyFarmerRepository(session)
    farmers = await repo.find_all_filtered(
        compliance_status=compliance_status,
        rank=rank,
        page_size=page_size,
        offset=offset,
    )
    return [_to_output(f) for f in farmers]


async def handle_get_farmer(
    farmer_id: str,
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> outputs.FarmerDetailOutput:
    from src.catalog.farmer.domain import value_objects

    repo = farmer_repos.SqlAlchemyFarmerRepository(session)
    farmer = await repo.find_by_id(value_objects.FarmerId(value=farmer_id))
    if farmer is None:
        raise farmer_exceptions.FarmerNotFoundError(farmer_id)
    summary = _to_output(farmer)
    return outputs.FarmerDetailOutput(**summary.model_dump())


async def handle_get_gold_farmers(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    limit: int = 6,
) -> list[outputs.FarmerSummaryOutput]:
    repo = farmer_repos.SqlAlchemyFarmerRepository(session)
    farmers = await repo.find_gold_farmers(limit=limit)
    return [_to_output(f) for f in farmers]
