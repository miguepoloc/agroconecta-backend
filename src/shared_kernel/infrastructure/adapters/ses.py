"""SES email adapter — sends emails via AWS Simple Email Service."""

import asyncio
import typing

import boto3
import botocore.client

from src.shared_kernel.application.ports import email_service


class SesEmailAdapter(email_service.AbstractEmailService):
    def __init__(
        self,
        sender_email: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ) -> None:
        self._sender = sender_email
        kwargs: dict[str, typing.Any] = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self._client: botocore.client.BaseClient = boto3.client("ses", **kwargs)

    async def send(self, message: email_service.EmailMessage) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sync, message)

    def _send_sync(self, message: email_service.EmailMessage) -> None:
        body: dict[str, typing.Any] = {
            "Html": {"Data": message.html_body, "Charset": "UTF-8"},
        }
        if message.text_body:
            body["Text"] = {"Data": message.text_body, "Charset": "UTF-8"}
        destination: dict[str, typing.Any] = {"ToAddresses": [message.to]}
        msg: dict[str, typing.Any] = {
            "Subject": {"Data": message.subject, "Charset": "UTF-8"},
            "Body": body,
        }
        kwargs: dict[str, typing.Any] = {
            "Source": self._sender,
            "Destination": destination,
            "Message": msg,
        }
        self._client.send_email(**kwargs)
