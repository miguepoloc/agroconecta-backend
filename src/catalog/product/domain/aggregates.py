"""Product aggregate root."""

import typing
from decimal import Decimal

import pydantic

from src.shared_kernel.domain import aggregates, value_objects as shared_value_objects
from src.catalog.product.domain import events as product_events
from src.catalog.product.domain import types, value_objects


class VolumePrice(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    min_kg: Decimal
    max_kg: Decimal
    price_per_kg: Decimal

    @property
    def label(self) -> str:
        return f"{self.min_kg}kg – {self.max_kg}kg"


class TraceabilityStep(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    stage: str
    date: shared_value_objects.PosixTime
    location: str
    responsible: str
    notes: typing.Optional[str] = None


class Product(aggregates.BaseAggregateRoot):
    id: value_objects.ProductId
    slug: value_objects.Slug
    name: str
    description: typing.Optional[str] = None
    category: types.ProductCategory
    price: Decimal
    institutional_price: Decimal
    minimum_lot: Decimal
    unit: types.ProductUnit
    images: list[str] = pydantic.Field(default_factory=list)
    farmer_id: str
    lot_number: value_objects.LotNumber
    harvest_date: shared_value_objects.PosixTime
    freshness_score: value_objects.FreshnessScore
    in_stock: bool = True
    featured: bool = False
    volume_prices: list[VolumePrice] = pydantic.Field(default_factory=list)
    traceability_chain: list[TraceabilityStep] = pydantic.Field(default_factory=list)

    def update_stock(self, in_stock: bool) -> None:
        self.in_stock = in_stock
        self.touch()
        self.record_event(
            product_events.StockUpdated(
                aggregate_id=str(self.id), product_id=str(self.id), in_stock=in_stock
            )
        )

    def recalculate_freshness(self, days_since_harvest: int) -> None:
        score = value_objects.FreshnessScore.calculate(days_since_harvest)
        self.freshness_score = score
        marked_out_of_stock = False
        if score.is_stale() and self.in_stock:
            self.in_stock = False
            marked_out_of_stock = True
        self.touch()
        self.record_event(
            product_events.FreshnessRecalculated(
                aggregate_id=str(self.id),
                product_id=str(self.id),
                freshness_score=score.value,
                marked_out_of_stock=marked_out_of_stock,
            )
        )

    def price_for_quantity(self, quantity_kg: Decimal) -> Decimal:
        for vp in sorted(self.volume_prices, key=lambda v: v.min_kg):
            if vp.min_kg <= quantity_kg <= vp.max_kg:
                return vp.price_per_kg
        return self.price
