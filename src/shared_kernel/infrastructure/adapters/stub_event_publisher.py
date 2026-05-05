"""Stub event publisher — logs events instead of publishing (local/test)."""

import logging

from src.shared_kernel.application.ports import event_publisher
from src.shared_kernel.domain import events

logger = logging.getLogger(__name__)


class StubEventPublisher(event_publisher.AbstractEventPublisher):
    def __init__(self) -> None:
        self.published: list[events.DomainEvent] = []

    async def publish(self, event: events.DomainEvent) -> None:
        self.published.append(event)
        logger.info("[STUB EVENT] %s aggregate=%s", event.event_name, event.aggregate_id)
