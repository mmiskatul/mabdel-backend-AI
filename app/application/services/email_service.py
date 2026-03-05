import asyncio
import smtplib
from email.message import EmailMessage

from app.shared.config import get_settings


class EmailService:
    async def send_otp(self, to_email: str, code: str, expiry_minutes: int) -> None:
        await asyncio.to_thread(self._send, to_email, code, expiry_minutes)

    def _send(self, to_email: str, code: str, expiry_minutes: int) -> None:
        settings = get_settings()
        if not settings.smtp_host or not settings.smtp_from_email:
            return
        message = EmailMessage()
        message["Subject"] = "Mabdel verification code"
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to_email
        message.set_content(f"Your verification code is {code}. Expires in {expiry_minutes} minutes.")

        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
            return

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)

