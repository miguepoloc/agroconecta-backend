"""EventBridge Lambda handler — processes domain events from the bus."""

import asyncio
import logging
import typing

from src.notifications import user_events
from src.shared_kernel.infrastructure import config as app_config
from src.shared_kernel.infrastructure.adapters import ses as ses_adapter

logger = logging.getLogger(__name__)

_HANDLERS: dict[str, typing.Callable[..., typing.Any]] = {
    "UserRegistered": user_events.handle_user_registered,
}


def handler(event: dict[str, typing.Any], context: typing.Any) -> None:
    detail_type: str = event.get("detail-type", "")
    detail: dict[str, typing.Any] = event.get("detail", {})

    logger.info("Received event: %s", detail_type)

    handle_fn = _HANDLERS.get(detail_type)
    if handle_fn is None:
        logger.warning("No handler registered for event type: %s", detail_type)
        return

    settings = app_config.get_settings()
    email_svc = ses_adapter.SesEmailAdapter(
        sender_email=settings.sender_email,
        region=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url or None,
    )

    asyncio.run(handle_fn(detail, email_svc))
