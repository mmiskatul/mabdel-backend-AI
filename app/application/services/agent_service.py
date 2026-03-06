from datetime import UTC, datetime, timedelta

from app.agent.graphs import AgentWorkflow
from app.agent.llm_client import get_llm_client
from app.agent.models import AutoReplyDecision, DraftReplyResponse, SmartFlowResponse, SummaryResponse
from app.agent.policy import enforce_auto_reply_guardrails
from app.infrastructure.db.repositories import MongoRepository
from app.shared.config import get_settings
from app.shared.errors import ForbiddenError


class AgentService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo
        self.llm = get_llm_client()
        self.workflow = AgentWorkflow(repo, self.llm)

    async def conversation_summary(self, user_id: str, conversation_id: str) -> SummaryResponse:
        state = await self.workflow.run(
            {
                "user_id": user_id,
                "run_type": "summary",
                "conversation_id": conversation_id,
            }
        )
        return SummaryResponse.model_validate(state["final_output"])

    async def draft_reply(self, user_id: str, conversation_id: str) -> DraftReplyResponse:
        state = await self.workflow.run(
            {
                "user_id": user_id,
                "run_type": "draft_reply",
                "conversation_id": conversation_id,
            }
        )
        draft = DraftReplyResponse.model_validate(state["final_output"])
        draft.requires_human_review = True
        draft.safe_to_auto_send = False
        return draft

    async def decide_inbound(self, message_id: str, user_id: str | None = None) -> AutoReplyDecision:
        message = await self.repo.find_one("messages", {"_id": self.repo.object_id(message_id)})
        if not message:
            return AutoReplyDecision(
                should_reply=False,
                reply_text="",
                reason="message_missing",
                confidence=0.0,
                safe_to_auto_send=False,
                requires_human_review=True,
            )
        if user_id and message["user_id"] != user_id:
            raise ForbiddenError()
        conversation = await self.repo.find_one(
            "conversations",
            {"_id": self.repo.object_id(message["conversation_id"])},
        )
        settings = await self.repo.find_one("user_settings", {"user_id": message["user_id"]}) or {}
        rule = await self.repo.find_one(
            "automation_rules",
            {"user_id": message["user_id"], "enabled": True},
        ) or {"enabled": False}

        state = await self.workflow.run(
            {
                "user_id": message["user_id"],
                "run_type": "auto_reply_decision",
                "conversation_id": message.get("conversation_id"),
                "message_id": message_id,
            }
        )
        llm_decision = AutoReplyDecision.model_validate(state["final_output"])
        decision = enforce_auto_reply_guardrails(
            llm_decision,
            automation_mode=(conversation or {}).get("automation_mode", "manual"),
            auto_reply_mode_enabled=bool(settings.get("auto_reply_mode", False)),
            rule_enabled=bool(rule.get("enabled", False)),
            backend_auto_send_allowed=get_settings().enable_auto_send_default,
        )

        if decision.should_reply and decision.safe_to_auto_send:
            cooldown_minutes = int((rule.get("conditions") or {}).get("cooldown_minutes", 5))
            last_auto_reply_at = (conversation or {}).get("last_auto_reply_at")
            now = datetime.now(UTC)
            if last_auto_reply_at:
                if last_auto_reply_at.tzinfo is None:
                    last_auto_reply_at = last_auto_reply_at.replace(tzinfo=UTC)
                if last_auto_reply_at + timedelta(minutes=cooldown_minutes) > now:
                    decision.safe_to_auto_send = False
                    decision.requires_human_review = True
                    decision.reason = "cooldown_active"
            if decision.safe_to_auto_send:
                await self.repo.insert_one(
                    "scheduled_jobs",
                    {
                        "user_id": message["user_id"],
                        "run_at": now,
                        "job_type": "auto_reply",
                        "payload": {"conversation_id": message["conversation_id"], "text": decision.reply_text},
                        "status": "queued",
                        "created_at": now,
                    },
                )
                await self.repo.update_one(
                    "conversations",
                    {"_id": self.repo.object_id(message["conversation_id"])},
                    {"$set": {"last_auto_reply_at": now}},
                )
        if decision.should_reply and decision.reply_text and not decision.safe_to_auto_send:
            await self._store_draft_reply(message, decision)
        return decision

    async def smartflow_ask(self, user_id: str, text: str) -> SmartFlowResponse:
        state = await self.workflow.run(
            {
                "user_id": user_id,
                "run_type": "smartflow",
                "input_text": text,
                "inbound_text": text,
            }
        )
        return SmartFlowResponse.model_validate(state["final_output"])

    async def post_send_followup(self, user_id: str, conversation_id: str, message_id: str) -> dict:
        summary = await self.conversation_summary(user_id, conversation_id)
        draft = await self.draft_reply(user_id, conversation_id)
        existing = await self.repo.find_one(
            "internal_messages",
            {
                "user_id": user_id,
                "source_message_id": message_id,
                "kind": "ai_followup",
            },
        )
        if not existing:
            now = datetime.now(UTC)
            internal_id = await self.repo.insert_one(
                "internal_messages",
                {
                    "user_id": user_id,
                    "kind": "ai_followup",
                    "source_message_id": message_id,
                    "conversation_id": conversation_id,
                    "summary": summary.model_dump(),
                    "suggested_reply": draft.model_dump(),
                    "created_at": now,
                },
            )
            await self.repo.insert_one(
                "activity_events",
                {
                    "user_id": user_id,
                    "event_type": "ai_followup_created",
                    "ref": {"type": "internal_message", "id": internal_id},
                    "title": "AI follow-up prepared",
                    "subtitle": summary.summary[:80],
                    "created_at": now,
                },
            )
        return {"summary": summary.model_dump(), "suggested_reply": draft.model_dump()}

    async def _store_draft_reply(self, message: dict, decision: AutoReplyDecision) -> None:
        existing = await self.repo.find_one(
            "internal_messages",
            {
                "user_id": message["user_id"],
                "source_message_id": message["id"],
                "kind": "ai_draft_reply",
            },
        )
        if existing:
            return
        now = datetime.now(UTC)
        await self.repo.insert_one(
            "internal_messages",
            {
                "user_id": message["user_id"],
                "kind": "ai_draft_reply",
                "source_message_id": message["id"],
                "conversation_id": message["conversation_id"],
                "text": decision.reply_text,
                "requires_human_review": decision.requires_human_review,
                "reason": decision.reason,
                "created_at": now,
            },
        )
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": message["user_id"],
                "event_type": "draft_reply_created",
                "ref": {"type": "message", "id": message["id"]},
                "title": "Draft reply created",
                "subtitle": decision.reason,
                "created_at": now,
            },
        )
