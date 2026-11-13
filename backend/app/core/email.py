import asyncio
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OutboundEmail:
    to: str
    subject: str
    text: str


class EmailSender(Protocol):
    async def send(self, message: OutboundEmail) -> None: ...


class ConsoleEmailSender:
    async def send(self, message: OutboundEmail) -> None:
        logger.info(
            "Email (console backend) to=%s subject=%s\n%s",
            message.to,
            message.subject,
            message.text,
        )


class SmtpEmailSender:
    def __init__(self) -> None:
        settings = get_settings()
        self.host = settings.smtp_host or ""
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.sender = settings.smtp_from
        self.use_tls = settings.smtp_use_tls

    async def send(self, message: OutboundEmail) -> None:
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: OutboundEmail) -> None:
        email = EmailMessage()
        email["From"] = self.sender
        email["To"] = message.to
        email["Subject"] = message.subject
        email.set_content(message.text)
        with smtplib.SMTP(self.host, self.port, timeout=15) as client:
            client.ehlo()
            if self.use_tls:
                client.starttls()
                client.ehlo()
            if self.username:
                client.login(self.username, self.password or "")
            client.send_message(email)


@lru_cache
def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.email_backend == "smtp":
        return SmtpEmailSender()
    return ConsoleEmailSender()


async def send_email(*, to: str, subject: str, text: str) -> None:
    await get_email_sender().send(OutboundEmail(to=to, subject=subject, text=text))
