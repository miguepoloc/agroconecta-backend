"""Email service port — send transactional emails."""

import abc

from src.shared_kernel.domain import base_model


class EmailMessage(base_model.DomainModel):
    to: str
    subject: str
    html_body: str
    text_body: str = ""
    reply_to: str = ""


class AbstractEmailService(abc.ABC):
    @abc.abstractmethod
    async def send(self, message: EmailMessage) -> None:
        raise NotImplementedError
