"""Resend email adapter — sends transactional emails via Resend."""

import asyncio

import resend

from src.shared_kernel.application.ports import email_service


class ResendEmailAdapter(email_service.AbstractEmailService):
    def __init__(self, api_key: str, sender_email: str) -> None:
        resend.api_key = api_key
        self._sender = sender_email

    async def send(self, message: email_service.EmailMessage) -> None:
        params: resend.Emails.SendParams = {
            "from": self._sender,
            "to": [message.to],
            "subject": message.subject,
            "html": message.html_body,
        }
        if message.text_body:
            params["text"] = message.text_body
        if message.reply_to:
            params["reply_to"] = message.reply_to
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: resend.Emails.send(params))
