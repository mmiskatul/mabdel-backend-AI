from datetime import UTC, datetime

from app.domain.enums import DocumentStatus, DocumentType
from app.infrastructure.db.repositories import MongoRepository
from app.infrastructure.storage.file_storage import LocalObjectStorage
from app.shared.errors import NotFoundError


class DocumentsService:
    def __init__(self, repo: MongoRepository, storage: LocalObjectStorage):
        self.repo = repo
        self.storage = storage

    async def list_documents(self, user_id: str, doc_type: str | None = None) -> list[dict]:
        query = {"user_id": user_id}
        if doc_type:
            query["doc_type"] = doc_type
        return await self.repo.find_many("documents", query, limit=100, sort=[("updated_at", -1)])

    async def create_invoice(self, user_id: str, payload: dict) -> dict:
        doc_id = await self.repo.insert_one(
            "documents",
            {
                "user_id": user_id,
                "doc_type": DocumentType.invoice.value,
                "title": payload.get("title", "Invoice Draft"),
                "status": DocumentStatus.draft.value,
                "file_url": None,
                "metadata": {
                    "invoice_number": payload.get("invoice_number", "INV-0001"),
                    "amount": payload.get("amount", 0),
                    "currency": payload.get("currency", "USD"),
                    "due_date": payload.get("due_date"),
                    "recipient": payload.get("recipient"),
                    "line_items": payload.get("line_items", []),
                },
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )
        await self._activity(user_id, "document_created", doc_id, "Invoice created")
        return await self.repo.find_one("documents", {"_id": self.repo.object_id(doc_id)})

    async def patch_invoice(self, user_id: str, document_id: str, patch: dict) -> dict:
        await self.repo.update_one(
            "documents",
            {"_id": self.repo.object_id(document_id), "user_id": user_id, "doc_type": "invoice"},
            {"$set": {**patch, "updated_at": datetime.now(UTC)}},
        )
        await self._activity(user_id, "invoice_updated", document_id, "Invoice updated")
        doc = await self.repo.find_one("documents", {"_id": self.repo.object_id(document_id)})
        if not doc:
            raise NotFoundError("Invoice not found.")
        return doc

    async def cancel_invoice(self, user_id: str, document_id: str) -> dict:
        await self.repo.update_one(
            "documents",
            {"_id": self.repo.object_id(document_id), "user_id": user_id},
            {"$set": {"status": DocumentStatus.cancelled.value, "updated_at": datetime.now(UTC)}},
        )
        await self._activity(user_id, "invoice_updated", document_id, "Invoice cancelled")
        return await self.repo.find_one("documents", {"_id": self.repo.object_id(document_id)})

    async def export_pdf(self, user_id: str, document_id: str) -> dict:
        document = await self.repo.find_one("documents", {"_id": self.repo.object_id(document_id), "user_id": user_id})
        if not document:
            raise NotFoundError("Document not found.")
        content = f"PDF export for {document['title']}".encode("utf-8")
        file_url = await self.storage.put_pdf(content)
        await self.repo.update_one(
            "documents",
            {"_id": self.repo.object_id(document_id)},
            {"$set": {"file_url": file_url, "updated_at": datetime.now(UTC)}},
        )
        await self._activity(user_id, "document_created", document_id, "PDF exported")
        return {"document_id": document_id, "file_url": file_url}

    async def send_document(self, user_id: str, document_id: str, channel: str = "email") -> dict:
        await self.repo.update_one(
            "documents",
            {"_id": self.repo.object_id(document_id), "user_id": user_id},
            {"$set": {"status": DocumentStatus.sent.value, "updated_at": datetime.now(UTC)}},
        )
        await self._activity(user_id, "document_created", document_id, f"Document sent via {channel}")
        return {"status": "sent", "channel": channel}

    async def send_docusign(self, user_id: str, document_id: str) -> dict:
        await self._activity(user_id, "document_created", document_id, "DocuSign send stub")
        return {"status": "queued", "provider": "docusign_stub"}

    async def _activity(self, user_id: str, event_type: str, entity_id: str, title: str) -> None:
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": user_id,
                "event_type": event_type,
                "ref": {"type": "document", "id": entity_id},
                "title": title,
                "subtitle": "",
                "created_at": datetime.now(UTC),
            },
        )

