"""Concrete message bus — routes domain events to registered handlers."""

import logging
import typing

from src.shared_kernel.application.ports import message_bus
from src.shared_kernel.domain import events

logger = logging.getLogger(__name__)


class MessageBus(message_bus.AbstractMessageBus):
    def __init__(self) -> None:
        self._handlers: dict[type, list[typing.Callable[..., typing.Any]]] = {}

    def register(
        self, event_type: type, handler: typing.Callable[..., typing.Any]
    ) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def handle(self, event: events.DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Handler %s failed for event %s", handler, event.event_name
                )
                raise
