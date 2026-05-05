"""Stub email adapter — logs emails instead of sending (local/test)."""

import logging

from src.shared_kernel.application.ports import email_service

logger = logging.getLogger(__name__)


class StubEmailAdapter(email_service.AbstractEmailService):
    def __init__(self) -> None:
        self.sent: list[email_service.EmailMessage] = []

    async def send(self, message: email_service.EmailMessage) -> None:
        self.sent.append(message)
        logger.info("[STUB EMAIL] to=%s subject=%s", message.to, message.subject)
