"""PostgreSQL event publisher — persists events to event_log and triggers handlers synchronously."""

import json
import uuid

import sqlalchemy.ext.asyncio

from src.shared_kernel.application.ports import email_service as email_port
from src.shared_kernel.application.ports import event_publisher as event_publisher_port
from src.shared_kernel.domain import events
from src.shared_kernel.infrastructure.database import models
from src.notifications import user_events


class PostgresEventPublisher(event_publisher_port.AbstractEventPublisher):
    def __init__(
        self,
        session_factory: sqlalchemy.ext.asyncio.async_sessionmaker[
            sqlalchemy.ext.asyncio.AsyncSession
        ],
        email_svc: email_port.AbstractEmailService,
    ) -> None:
        self._session_factory = session_factory
        self._email_svc = email_svc

    async def publish(self, event: events.DomainEvent) -> None:
        await self._persist(event)
        await self._dispatch(event)

    async def _persist(self, event: events.DomainEvent) -> None:
        record = models.EventLogOrm(
            id=str(uuid.uuid4()),
            aggregate_id=event.aggregate_id or "global",
            event_type=type(event).__name__,
            payload=json.dumps(event.model_dump(mode="json")),
            occurred_on=event.occurred_on.to_isoformat(),
        )
        async with self._session_factory() as session:
            session.add(record)
            await session.commit()

    async def _dispatch(self, event: events.DomainEvent) -> None:
        import logging
        logger = logging.getLogger(__name__)
        event_type = type(event).__name__
        try:
            if event_type == "UserRegistered":
                detail = event.model_dump(mode="json")
                await user_events.handle_user_registered(detail, self._email_svc)
        except Exception as exc:
            logger.warning("Event dispatch failed for %s: %s", event_type, exc)
