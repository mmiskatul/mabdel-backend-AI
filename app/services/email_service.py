import asyncio
import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

from app.core.config import settings


class IEmailService(ABC):
    @abstractmethod
    async def send_otp(self, to_email: str, code: str, expiry_minutes: int) -> None:
        raise NotImplementedError


class SMTPEmailService(IEmailService):
    async def send_otp(self, to_email: str, code: str, expiry_minutes: int) -> None:
        await asyncio.to_thread(self._send_otp_sync, to_email, code, expiry_minutes)

    def _send_otp_sync(self, to_email: str, code: str, expiry_minutes: int) -> None:
        if not settings.smtp_host or not settings.smtp_from_email:
            raise ValueError("SMTP is not configured.")

        subject = "Your Mabdel verification code"
        body = (
            f"Your verification code is: {code}\n\n"
            f"This code will expire in {expiry_minutes} minutes.\n"
            "If you did not request this code, ignore this message."
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to_email
        message.set_content(body)

        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                self._authenticate(server)
                server.send_message(message)
            return

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            self._authenticate(server)
            server.send_message(message)

    @staticmethod
    def _authenticate(server: smtplib.SMTP) -> None:
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)

