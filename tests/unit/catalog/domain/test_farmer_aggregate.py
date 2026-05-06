"""Unit tests for the Farmer aggregate."""

import uuid

from src.catalog.farmer.domain import aggregates, events, types, value_objects


def make_farmer() -> aggregates.Farmer:
    return aggregates.Farmer(
        id=value_objects.FarmerId(value=str(uuid.uuid4())),
        user_id=str(uuid.uuid4()),
        region=value_objects.Region(value="Cundinamarca"),
        department=value_objects.Department(value="Cundinamarca"),
    )


class TestFarmerCompliance:
    def test_new_farmer_is_active(self) -> None:
        farmer = make_farmer()
        assert farmer.compliance_status == types.ComplianceStatus.ACTIVE
        assert farmer.can_sell()

    def test_suspend_marks_expired(self) -> None:
        farmer = make_farmer()
        farmer.suspend(reason="Certifications expired")
        assert farmer.compliance_status == types.ComplianceStatus.EXPIRED
        assert not farmer.can_sell()

    def test_suspend_emits_events(self) -> None:
        farmer = make_farmer()
        farmer.suspend(reason="Annual review")
        pending = farmer.pull_events()

        event_types = [type(e) for e in pending]
        assert events.FarmerSuspended in event_types
        assert events.ComplianceStatusChanged in event_types

    def test_reactivate_restores_active(self) -> None:
        farmer = make_farmer()
        farmer.suspend(reason="Test")
        farmer.pull_events()

        farmer.reactivate()
        assert farmer.compliance_status == types.ComplianceStatus.ACTIVE
        assert farmer.can_sell()

    def test_reactivate_emits_events(self) -> None:
        farmer = make_farmer()
        farmer.suspend(reason="Test")
        farmer.pull_events()

        farmer.reactivate()
        pending = farmer.pull_events()
        event_types = [type(e) for e in pending]
        assert events.FarmerReactivated in event_types
        assert events.ComplianceStatusChanged in event_types


class TestFarmerSustainabilityRank:
    def test_new_farmer_is_bronze(self) -> None:
        farmer = make_farmer()
        assert farmer.sustainability_rank == types.SustainabilityRank.BRONZE
