from datetime import UTC, datetime

from app.application.commands.factory import CommandFactory
from app.infrastructure.db.repositories import MongoRepository
from app.shared.security import generate_execute_token, hash_secret


class CommandService:
    def __init__(self, repo: MongoRepository, services: dict):
        self.repo = repo
        self.factory = CommandFactory()
        self.services = services

    async def interpret(self, user_id: str, text: str, context: dict | None = None) -> dict:
        lowered = text.lower()
        command_type = "SUMMARIZE"
        payload = {"conversation_id": (context or {}).get("conversation_id")}
        if "cancel invoice" in lowered:
            command_type = "INVOICE_CANCEL"
            payload = {"document_id": (context or {}).get("document_id")}
        elif "change amount" in lowered:
            command_type = "INVOICE_CHANGE_AMOUNT"
            payload = {"document_id": (context or {}).get("document_id"), "amount": (context or {}).get("amount", 0)}
        elif "set due date" in lowered:
            command_type = "INVOICE_SET_DUE_DATE"
            payload = {"document_id": (context or {}).get("document_id"), "due_date": (context or {}).get("due_date")}
        elif "send message" in lowered:
            command_type = "SEND_MESSAGE"
            payload = {
                "conversation_id": (context or {}).get("conversation_id"),
                "text": (context or {}).get("text", text),
            }

        execute_token = generate_execute_token()
        await self.repo.insert_one(
            "command_drafts",
            {
                "user_id": user_id,
                "execute_token_hash": hash_secret(execute_token),
                "command_type": command_type,
                "payload": payload,
                "created_at": datetime.now(UTC),
            },
        )
        return {
            "requires_confirmation": True,
            "action_preview": {"command_type": command_type, "payload": payload},
            "draft_text": text,
            "execute_token": execute_token,
        }

    async def execute(self, user_id: str, execute_token: str) -> dict:
        draft = await self.repo.find_one(
            "command_drafts",
            {"user_id": user_id, "execute_token_hash": hash_secret(execute_token)},
        )
        if not draft:
            return {"status": "failed", "message": "Invalid execute token."}
        command = self.factory.create(draft["command_type"], user_id, draft["payload"])
        result = await command.execute(self.services)
        run_id = await self.repo.insert_one(
            "command_runs",
            {
                "user_id": user_id,
                "source": "voice",
                "category": self._category(draft["command_type"]),
                "command_text": draft["command_type"],
                "command_type": draft["command_type"],
                "status": "completed",
                "result_summary": str(result)[:280],
                "related_entities": [],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": user_id,
                "event_type": "command_run",
                "ref": {"type": "command_run", "id": run_id},
                "title": "Command executed",
                "subtitle": draft["command_type"],
                "created_at": datetime.now(UTC),
            },
        )
        return {"run_id": run_id, "result": result}

    async def history(self, user_id: str, category: str = "all", limit: int = 20) -> list[dict]:
        query = {"user_id": user_id}
        if category != "all":
            query["category"] = category
        return await self.repo.find_many("command_runs", query, limit=limit, sort=[("created_at", -1)])

    async def rerun(self, user_id: str, run_id: str) -> dict:
        run = await self.repo.find_one("command_runs", {"_id": self.repo.object_id(run_id), "user_id": user_id})
        if not run:
            return {"status": "failed", "message": "Command run not found."}
        execute_token = generate_execute_token()
        await self.repo.insert_one(
            "command_drafts",
            {
                "user_id": user_id,
                "execute_token_hash": hash_secret(execute_token),
                "command_type": run["command_type"],
                "payload": {},
                "created_at": datetime.now(UTC),
            },
        )
        return await self.execute(user_id, execute_token)

    @staticmethod
    def _category(command_type: str) -> str:
        if command_type.startswith("INVOICE"):
            return "invoices"
        if command_type in {"SEND_MESSAGE", "SUMMARIZE"}:
            return "messages"
        return "ai_voice"

