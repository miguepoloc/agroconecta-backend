"""Farmer API router — /api/v1/farmers/*"""

import typing

import fastapi

from src.catalog.farmer.application.dtos import outputs
from src.catalog.farmer.application.handlers import queries
from src.catalog.farmer.domain import types

router = fastapi.APIRouter(prefix="/farmers", tags=["farmers"])


@router.get("", response_model=list[outputs.FarmerSummaryOutput])
async def list_farmers(
    request: fastapi.Request,
    compliance_status: typing.Annotated[types.ComplianceStatus | None, fastapi.Query()] = None,
    rank: typing.Annotated[types.SustainabilityRank | None, fastapi.Query()] = None,
    page_size: typing.Annotated[int, fastapi.Query(ge=1, le=100)] = 20,
    offset: typing.Annotated[int, fastapi.Query(ge=0)] = 0,
) -> list[outputs.FarmerSummaryOutput]:
    return await queries.handle_list_farmers(
        session=request.state.db_session,
        compliance_status=compliance_status,
        rank=rank,
        page_size=page_size,
        offset=offset,
    )


@router.get("/{farmer_id}", response_model=outputs.FarmerDetailOutput)
async def get_farmer(
    farmer_id: str,
    request: fastapi.Request,
) -> outputs.FarmerDetailOutput:
    return await queries.handle_get_farmer(farmer_id, request.state.db_session)


@router.get("/{farmer_id}/products")
async def get_farmer_products(
    farmer_id: str,
    request: fastapi.Request,
) -> list[typing.Any]:
    from src.catalog.product.application.handlers import queries as product_queries

    return await product_queries.handle_list_products_by_farmer(
        farmer_id=farmer_id,
        session=request.state.db_session,
    )
