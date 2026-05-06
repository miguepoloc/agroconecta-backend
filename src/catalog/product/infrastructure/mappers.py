"""Data Mapper — Product ORM ↔ domain."""

from decimal import Decimal

from src.catalog.product.domain import aggregates as product_aggregates
from src.catalog.product.domain import types, value_objects
from src.catalog.product.infrastructure import models
from src.shared_kernel.domain import value_objects as shared_value_objects


def volume_price_orm_to_domain(orm: models.VolumePriceOrm) -> product_aggregates.VolumePrice:
    return product_aggregates.VolumePrice(
        id=orm.id,
        min_kg=Decimal(str(orm.min_kg)),
        max_kg=Decimal(str(orm.max_kg)),
        price_per_kg=Decimal(str(orm.price_per_kg)),
    )


def traceability_step_orm_to_domain(
    orm: models.TraceabilityStepOrm,
) -> product_aggregates.TraceabilityStep:
    return product_aggregates.TraceabilityStep(
        id=orm.id,
        stage=orm.stage,
        date=shared_value_objects.PosixTime(microseconds=orm.date),
        location=orm.location,
        responsible=orm.responsible,
        notes=orm.notes,
    )


def orm_to_domain(orm: models.ProductOrm) -> product_aggregates.Product:
    return product_aggregates.Product(
        id=value_objects.ProductId(value=orm.id),
        slug=value_objects.Slug(value=orm.slug),
        name=orm.name,
        description=orm.description,
        category=types.ProductCategory(orm.category),
        price=Decimal(str(orm.price)),
        institutional_price=Decimal(str(orm.institutional_price)),
        minimum_lot=Decimal(str(orm.minimum_lot)),
        unit=types.ProductUnit(orm.unit),
        images=orm.images or [],
        farmer_id=orm.farmer_id,
        lot_number=value_objects.LotNumber(value=orm.lot_number),
        harvest_date=shared_value_objects.PosixTime(microseconds=orm.harvest_date),
        freshness_score=value_objects.FreshnessScore(value=orm.freshness_score),
        in_stock=orm.in_stock,
        featured=orm.featured,
        volume_prices=[volume_price_orm_to_domain(vp) for vp in orm.volume_prices],
        traceability_chain=[traceability_step_orm_to_domain(ts) for ts in orm.traceability_steps],
        version=orm.version,
        created_at=shared_value_objects.PosixTime(microseconds=orm.created_at),
        updated_at=shared_value_objects.PosixTime(microseconds=orm.updated_at),
    )


def domain_to_orm(product: product_aggregates.Product) -> models.ProductOrm:
    return models.ProductOrm(
        id=str(product.id),
        slug=str(product.slug),
        name=product.name,
        description=product.description,
        category=product.category.value,
        price=str(product.price),
        institutional_price=str(product.institutional_price),
        minimum_lot=str(product.minimum_lot),
        unit=product.unit.value,
        images=product.images,
        farmer_id=product.farmer_id,
        lot_number=str(product.lot_number),
        harvest_date=product.harvest_date.microseconds,
        freshness_score=product.freshness_score.value,
        in_stock=product.in_stock,
        featured=product.featured,
        version=product.version,
        created_at=product.created_at.microseconds,
        updated_at=product.updated_at.microseconds,
    )
