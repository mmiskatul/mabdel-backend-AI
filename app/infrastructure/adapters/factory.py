from app.domain.enums import Platform
from app.domain.interfaces.adapters import PlatformAdapter
from app.infrastructure.adapters.email_adapter import EmailAdapter
from app.infrastructure.adapters.meta_adapter import MetaAdapter
from app.infrastructure.adapters.sms_adapter import SmsAdapter
from app.infrastructure.adapters.telegram_adapter import TelegramAdapter
from app.infrastructure.adapters.whatsapp_adapter import WhatsAppAdapter


class AdapterFactory:
    def __init__(self):
        self._map: dict[Platform, PlatformAdapter] = {
            Platform.whatsapp: WhatsAppAdapter(),
            Platform.meta_messenger: MetaAdapter(),
            Platform.instagram: MetaAdapter(),
            Platform.telegram: TelegramAdapter(),
            Platform.email_gmail: EmailAdapter(),
            Platform.email_outlook: EmailAdapter(),
            Platform.sms: SmsAdapter(),
            Platform.linkedin: MetaAdapter(),
            Platform.x: MetaAdapter(),
            Platform.tiktok: MetaAdapter(),
            Platform.google_business: MetaAdapter(),
        }

    def get(self, platform: Platform) -> PlatformAdapter:
        return self._map[platform]

