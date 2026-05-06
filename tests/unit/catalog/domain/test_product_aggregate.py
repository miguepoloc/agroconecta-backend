"""Unit tests for the Product aggregate."""

import uuid
from decimal import Decimal

import pydantic
import pytest

from src.catalog.product.domain import aggregates, events, types, value_objects
from src.shared_kernel.domain import value_objects as shared_vos


def make_product() -> aggregates.Product:
    return aggregates.Product(
        id=value_objects.ProductId(value=str(uuid.uuid4())),
        slug=value_objects.Slug(value="tomate-organico-cundinamarca"),
        name="Tomate Orgánico",
        category=types.ProductCategory.VERDURAS,
        price=Decimal("4500"),
        institutional_price=Decimal("3800"),
        minimum_lot=Decimal("5"),
        unit=types.ProductUnit.KG,
        farmer_id=str(uuid.uuid4()),
        lot_number=value_objects.LotNumber(value="LOT-2026-0501-01"),
        harvest_date=shared_vos.PosixTime.now(),
        freshness_score=value_objects.FreshnessScore(value=100),
    )


class TestFreshnessScore:
    def test_calculate_from_days(self) -> None:
        score = value_objects.FreshnessScore.calculate(days_since_harvest=10)
        assert score.value == 70

    def test_stale_at_33_days(self) -> None:
        score = value_objects.FreshnessScore.calculate(days_since_harvest=34)
        assert score.is_stale()

    def test_freshness_never_negative(self) -> None:
        score = value_objects.FreshnessScore.calculate(days_since_harvest=100)
        assert score.value == 0

    def test_invalid_score_raises(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            value_objects.FreshnessScore(value=101)


class TestProductRecalculateFreshness:
    def test_recalculate_emits_event(self) -> None:
        product = make_product()
        product.recalculate_freshness(days_since_harvest=15)
        pending = product.pull_events()

        assert len(pending) == 1
        assert isinstance(pending[0], events.FreshnessRecalculated)
        assert pending[0].freshness_score == 55

    def test_recalculate_marks_out_of_stock_when_stale(self) -> None:
        product = make_product()
        product.recalculate_freshness(days_since_harvest=40)

        assert not product.in_stock
        pending = product.pull_events()
        assert pending[0].marked_out_of_stock

    def test_recalculate_does_not_double_mark_out_of_stock(self) -> None:
        product = make_product()
        product.in_stock = False
        product.recalculate_freshness(days_since_harvest=40)

        pending = product.pull_events()
        assert not pending[0].marked_out_of_stock


class TestProductStockUpdate:
    def test_update_stock_emits_event(self) -> None:
        product = make_product()
        product.update_stock(False)
        pending = product.pull_events()

        assert len(pending) == 1
        assert isinstance(pending[0], events.StockUpdated)
        assert not pending[0].in_stock


class TestVolumePricing:
    def test_price_for_quantity_uses_volume_price(self) -> None:
        product = make_product()
        product.volume_prices.append(
            aggregates.VolumePrice(
                id=str(uuid.uuid4()),
                min_kg=Decimal("10"),
                max_kg=Decimal("50"),
                price_per_kg=Decimal("3500"),
            )
        )
        assert product.price_for_quantity(Decimal("20")) == Decimal("3500")

    def test_price_for_quantity_falls_back_to_base_price(self) -> None:
        product = make_product()
        assert product.price_for_quantity(Decimal("2")) == product.price


class TestLotNumber:
    def test_valid_lot_number(self) -> None:
        lot = value_objects.LotNumber(value="LOT-2026-0501-01")
        assert str(lot) == "LOT-2026-0501-01"

    def test_invalid_lot_number_raises(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            value_objects.LotNumber(value="INVALID-FORMAT")

    def test_lot_number_is_uppercased(self) -> None:
        lot = value_objects.LotNumber(value="lot-2026-0501-01")
        assert str(lot) == "LOT-2026-0501-01"
