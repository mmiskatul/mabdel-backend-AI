from app.application.commands.base import Command


class InvoiceCancelCommand(Command):
    async def execute(self, services: dict) -> dict:
        documents = services["documents"]
        result = await documents.cancel_invoice(self.user_id, self.payload["document_id"])
        return {"result": "completed", "document": result}


class InvoiceChangeAmountCommand(Command):
    async def execute(self, services: dict) -> dict:
        documents = services["documents"]
        patch = {"metadata.amount": self.payload["amount"]}
        result = await documents.patch_invoice(self.user_id, self.payload["document_id"], patch)
        return {"result": "completed", "document": result}


class InvoiceSetDueDateCommand(Command):
    async def execute(self, services: dict) -> dict:
        documents = services["documents"]
        patch = {"metadata.due_date": self.payload["due_date"]}
        result = await documents.patch_invoice(self.user_id, self.payload["document_id"], patch)
        return {"result": "completed", "document": result}

