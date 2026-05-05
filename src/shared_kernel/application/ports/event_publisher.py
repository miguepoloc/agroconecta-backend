"""Event publisher port — publishes domain events to an external bus."""

import abc

from src.shared_kernel.domain import events


class AbstractEventPublisher(abc.ABC):
    @abc.abstractmethod
    async def publish(self, event: events.DomainEvent) -> None:
        raise NotImplementedError

    async def publish_many(self, domain_events: list[events.DomainEvent]) -> None:
        for event in domain_events:
            await self.publish(event)
