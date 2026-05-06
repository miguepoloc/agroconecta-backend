"""Product API router — /api/v1/products/* and /api/v1/traceability/*"""

import typing

import fastapi

from src.catalog.product.application.dtos import outputs
from src.catalog.product.application.handlers import queries

router = fastapi.APIRouter(tags=["products"])
traceability_router = fastapi.APIRouter(tags=["traceability"])


@router.get("/products/featured", response_model=list[outputs.ProductSummaryOutput])
async def list_featured_products(
    request: fastapi.Request,
    limit: typing.Annotated[int, fastapi.Query(ge=1, le=20)] = 8,
) -> list[outputs.ProductSummaryOutput]:
    return await queries.handle_list_featured(request.state.db_session, limit=limit)


@router.get("/products", response_model=list[outputs.ProductSummaryOutput])
async def list_products(
    request: fastapi.Request,
    category: typing.Annotated[str | None, fastapi.Query()] = None,
    in_stock: typing.Annotated[bool | None, fastapi.Query()] = None,
    sort_by: typing.Annotated[str, fastapi.Query()] = "created_at",
    page_size: typing.Annotated[int, fastapi.Query(ge=1, le=100)] = 20,
    offset: typing.Annotated[int, fastapi.Query(ge=0)] = 0,
) -> list[outputs.ProductSummaryOutput]:
    return await queries.handle_list_products(
        session=request.state.db_session,
        category=category,
        in_stock=in_stock,
        sort_by=sort_by,
        page_size=page_size,
        offset=offset,
    )


@router.get("/products/lot/{lot_number}", response_model=outputs.ProductDetailOutput)
async def get_product_by_lot(
    lot_number: str,
    request: fastapi.Request,
) -> outputs.ProductDetailOutput:
    return await queries.handle_get_product_by_lot(lot_number, request.state.db_session)


@router.get("/products/{slug}", response_model=outputs.ProductDetailOutput)
async def get_product_by_slug(
    slug: str,
    request: fastapi.Request,
) -> outputs.ProductDetailOutput:
    return await queries.handle_get_product_by_slug(slug, request.state.db_session)


@traceability_router.get(
    "/traceability/{lot_number}", response_model=list[outputs.TraceabilityStepOutput]
)
async def get_traceability(
    lot_number: str,
    request: fastapi.Request,
) -> list[outputs.TraceabilityStepOutput]:
    detail = await queries.handle_get_product_by_lot(lot_number, request.state.db_session)
    return detail.traceability_chain
