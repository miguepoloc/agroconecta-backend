"""Product domain events."""

from src.shared_kernel.domain import events


class ProductPublished(events.DomainEvent):
    product_id: str
    farmer_id: str
    lot_number: str


class StockUpdated(events.DomainEvent):
    product_id: str
    in_stock: bool


class FreshnessRecalculated(events.DomainEvent):
    product_id: str
    freshness_score: int
    marked_out_of_stock: bool
