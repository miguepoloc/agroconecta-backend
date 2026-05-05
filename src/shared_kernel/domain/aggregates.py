"""Aggregate root — entity with domain event collection and optimistic locking."""

import pydantic

from src.shared_kernel.domain import entities, events


class BaseAggregateRoot(entities.BaseEntity):
    version: int = 1
    _domain_events: list[events.DomainEvent] = pydantic.PrivateAttr(default_factory=list)

    def record_event(self, event: events.DomainEvent) -> None:
        updated = event.model_copy(update={"aggregate_id": str(self.id)})
        self._domain_events.append(updated)

    def pull_events(self) -> list[events.DomainEvent]:
        """Returns and clears all pending domain events (pull-and-clear pattern)."""
        pending = list(self._domain_events)
        self._domain_events.clear()
        return pending

    def has_pending_events(self) -> bool:
        return len(self._domain_events) > 0

    @property
    def pending_event_count(self) -> int:
        return len(self._domain_events)

    def bump_version(self) -> None:
        """Called by repository after successful DB write."""
        object.__setattr__(self, "version", self.version + 1)
