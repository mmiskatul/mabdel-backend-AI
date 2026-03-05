from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.schemas import InvoiceCreateBody, InvoicePatchBody, SendDocumentBody
from app.api.service_factory import get_documents_service
from app.application.services.documents_service import DocumentsService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    type: str | None = None,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    return await service.list_documents(user_id, doc_type=type)


@router.post("/invoices")
async def create_invoice(
    body: InvoiceCreateBody,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    return await service.create_invoice(user_id, body.model_dump())


@router.patch("/invoices/{document_id}")
async def patch_invoice(
    document_id: str,
    body: InvoicePatchBody,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    patch: dict = {}
    if body.amount is not None:
        patch["metadata.amount"] = body.amount
    if body.due_date is not None:
        patch["metadata.due_date"] = body.due_date
    if body.line_items is not None:
        patch["metadata.line_items"] = body.line_items
    return await service.patch_invoice(user_id, document_id, patch)


@router.post("/invoices/{document_id}/cancel")
async def cancel_invoice(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    return await service.cancel_invoice(user_id, document_id)


@router.post("/{document_id}/export_pdf")
async def export_pdf(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    return await service.export_pdf(user_id, document_id)


@router.post("/{document_id}/send")
async def send_document(
    document_id: str,
    body: SendDocumentBody,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    return await service.send_document(user_id, document_id, body.channel)


@router.post("/{document_id}/docusign/send")
async def docusign_send(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DocumentsService = Depends(get_documents_service),
):
    return await service.send_docusign(user_id, document_id)

