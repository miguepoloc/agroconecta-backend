"""DynamoDB audit event publisher — wraps another publisher and persists to events_log table."""

import json
import typing

import aioboto3

from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.shared_kernel.domain import events


class DynamoAuditEventPublisher(event_publisher_port.AbstractEventPublisher):
    def __init__(
        self,
        inner: event_publisher_port.AbstractEventPublisher,
        table_name: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ) -> None:
        self._inner = inner
        self._table_name = table_name
        self._session = aioboto3.Session()
        self._kwargs: dict[str, typing.Any] = {"region_name": region}
        if endpoint_url:
            self._kwargs["endpoint_url"] = endpoint_url

    async def publish(self, event: events.DomainEvent) -> None:
        await self._inner.publish(event)
        await self._persist(event)

    async def _persist(self, event: events.DomainEvent) -> None:
        async with self._session.resource("dynamodb", **self._kwargs) as dynamo:
            table = await dynamo.Table(self._table_name)
            await table.put_item(
                Item={
                    "aggregate_id": event.aggregate_id or "global",
                    "occurred_on": event.occurred_on.to_isoformat(),
                    "event_type": type(event).__name__,
                    "payload": json.dumps(event.model_dump(mode="json")),
                }
            )
