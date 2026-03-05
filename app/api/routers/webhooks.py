from fastapi import APIRouter, Depends, Header

from app.api.service_factory import get_webhook_service
from app.application.services.webhook_service import WebhookService
from app.domain.enums import Platform

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/whatsapp")
async def webhook_whatsapp(
    payload: dict,
    x_signature: str | None = Header(default=None),
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.receive_webhook(Platform.whatsapp, payload, x_signature)


@router.post("/meta")
async def webhook_meta(
    payload: dict,
    x_signature: str | None = Header(default=None),
    service: WebhookService = Depends(get_webhook_service),
):
    platform = Platform.instagram if payload.get("source") == "instagram" else Platform.meta_messenger
    return await service.receive_webhook(platform, payload, x_signature)


@router.post("/telegram")
async def webhook_telegram(
    payload: dict,
    x_signature: str | None = Header(default=None),
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.receive_webhook(Platform.telegram, payload, x_signature)


@router.post("/sms")
async def webhook_sms(
    payload: dict,
    x_signature: str | None = Header(default=None),
    service: WebhookService = Depends(get_webhook_service),
):
    return await service.receive_webhook(Platform.sms, payload, x_signature)


@router.post("/email")
async def webhook_email(
    payload: dict,
    x_signature: str | None = Header(default=None),
    service: WebhookService = Depends(get_webhook_service),
):
    source = payload.get("provider", "gmail")
    platform = Platform.email_outlook if source == "outlook" else Platform.email_gmail
    return await service.receive_webhook(platform, payload, x_signature)

