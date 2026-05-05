"""EventBridge publisher — publishes domain events to AWS EventBridge."""

import asyncio
import typing

import boto3

from src.shared_kernel.application.ports import event_publisher
from src.shared_kernel.domain import events


class EventBridgePublisher(event_publisher.AbstractEventPublisher):
    def __init__(
        self,
        bus_name: str,
        source: str = "agroconecta.backend",
        region: str = "us-east-1",
        endpoint_url: typing.Optional[str] = None,
    ) -> None:
        self._bus_name = bus_name
        self._source = source
        kwargs: dict[str, typing.Any] = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self._client = boto3.client("events", **kwargs)

    async def publish(self, event: events.DomainEvent) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._put_event, event)

    def _put_event(self, event: events.DomainEvent) -> None:
        entry: dict[str, typing.Any] = {
            "Source": self._source,
            "DetailType": event.event_name,
            "Detail": event.to_json(),
            "EventBusName": self._bus_name,
        }
        self._client.put_events(Entries=[entry])
