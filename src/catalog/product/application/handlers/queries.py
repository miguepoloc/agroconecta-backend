"""Query handlers for the product context."""

import typing

import sqlalchemy.ext.asyncio

from src.catalog.product.application.dtos import outputs
from src.catalog.product.domain import aggregates as product_aggregates
from src.catalog.product.domain import exceptions as product_exceptions
from src.catalog.product.infrastructure import repositories as product_repos


def _to_summary(product: product_aggregates.Product) -> outputs.ProductSummaryOutput:
    return outputs.ProductSummaryOutput(
        id=str(product.id),
        slug=str(product.slug),
        name=product.name,
        category=product.category,
        price=product.price,
        institutional_price=product.institutional_price,
        minimum_lot=product.minimum_lot,
        unit=product.unit,
        images=product.images,
        farmer_id=product.farmer_id,
        lot_number=str(product.lot_number),
        harvest_date=product.harvest_date.to_isoformat(),
        freshness_score=product.freshness_score.value,
        in_stock=product.in_stock,
        featured=product.featured,
    )


def _to_detail(product: product_aggregates.Product) -> outputs.ProductDetailOutput:
    return outputs.ProductDetailOutput(
        **_to_summary(product).model_dump(),
        description=product.description,
        volume_prices=[
            outputs.VolumePriceOutput(
                id=vp.id,
                min_kg=vp.min_kg,
                max_kg=vp.max_kg,
                price_per_kg=vp.price_per_kg,
                label=vp.label,
            )
            for vp in product.volume_prices
        ],
        traceability_chain=[
            outputs.TraceabilityStepOutput(
                id=ts.id,
                stage=ts.stage,
                date=ts.date.to_isoformat(),
                location=ts.location,
                responsible=ts.responsible,
                notes=ts.notes,
            )
            for ts in product.traceability_chain
        ],
    )


async def handle_list_products(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    category: typing.Optional[str] = None,
    in_stock: typing.Optional[bool] = None,
    sort_by: str = "created_at",
    page_size: int = 20,
    offset: int = 0,
) -> list[outputs.ProductSummaryOutput]:
    repo = product_repos.SqlAlchemyProductRepository(session)
    products = await repo.find_all_filtered(
        category=category,
        in_stock=in_stock,
        sort_by=sort_by,
        page_size=page_size,
        offset=offset,
    )
    return [_to_summary(p) for p in products]


async def handle_list_products_by_farmer(
    farmer_id: str,
    session: sqlalchemy.ext.asyncio.AsyncSession,
    page_size: int = 20,
    offset: int = 0,
) -> list[outputs.ProductSummaryOutput]:
    repo = product_repos.SqlAlchemyProductRepository(session)
    products = await repo.find_all_filtered(
        farmer_id=farmer_id,
        page_size=page_size,
        offset=offset,
    )
    return [_to_summary(p) for p in products]


async def handle_get_product_by_slug(
    slug: str,
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> outputs.ProductDetailOutput:
    repo = product_repos.SqlAlchemyProductRepository(session)
    product = await repo.find_by_slug(slug)
    if product is None:
        raise product_exceptions.ProductNotFoundError(slug)
    return _to_detail(product)


async def handle_get_product_by_lot(
    lot_number: str,
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> outputs.ProductDetailOutput:
    repo = product_repos.SqlAlchemyProductRepository(session)
    product = await repo.find_by_lot_number(lot_number)
    if product is None:
        raise product_exceptions.ProductNotFoundError(lot_number)
    return _to_detail(product)


async def handle_list_featured(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    limit: int = 8,
) -> list[outputs.ProductSummaryOutput]:
    repo = product_repos.SqlAlchemyProductRepository(session)
    products = await repo.find_featured(limit=limit)
    return [_to_summary(p) for p in products]
