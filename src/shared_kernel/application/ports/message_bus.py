"""Message bus port — routes domain events to handlers."""

import abc
import typing

from src.shared_kernel.domain import events


class AbstractMessageBus(abc.ABC):
    @abc.abstractmethod
    async def handle(self, event: events.DomainEvent) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def register(
        self, event_type: type, handler: typing.Callable[..., typing.Any]
    ) -> None:
        raise NotImplementedError
