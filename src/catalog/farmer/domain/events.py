"""Farmer domain events."""

from src.shared_kernel.domain import events


class FarmerSuspended(events.DomainEvent):
    farmer_id: str
    reason: str


class FarmerReactivated(events.DomainEvent):
    farmer_id: str


class ComplianceStatusChanged(events.DomainEvent):
    farmer_id: str
    old_status: str
    new_status: str
