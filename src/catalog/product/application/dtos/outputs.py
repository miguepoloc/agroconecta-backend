"""Output DTOs for the product context."""

from decimal import Decimal

import pydantic

from src.catalog.farmer.application.dtos import outputs as farmer_outputs
from src.catalog.product.domain import types


class VolumePriceOutput(pydantic.BaseModel):
    id: str
    min_kg: Decimal
    max_kg: Decimal
    price_per_kg: Decimal
    label: str


class TraceabilityStepOutput(pydantic.BaseModel):
    id: str
    stage: str
    date: str
    location: str
    responsible: str
    notes: str | None = None


class ProductSummaryOutput(pydantic.BaseModel):
    id: str
    slug: str
    name: str
    category: types.ProductCategory
    price: Decimal
    institutional_price: Decimal
    minimum_lot: Decimal
    unit: types.ProductUnit
    images: list[str]
    farmer_id: str
    lot_number: str
    harvest_date: str
    freshness_score: int
    in_stock: bool
    featured: bool


class ProductDetailOutput(ProductSummaryOutput):
    description: str | None
    farmer: farmer_outputs.FarmerSummaryOutput | None = None
    volume_prices: list[VolumePriceOutput]
    traceability_chain: list[TraceabilityStepOutput]
