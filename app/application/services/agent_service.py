from datetime import UTC, datetime, timedelta

from app.agent.llm_client import get_llm_client
from app.agent.models import AutoReplyDecision, DraftReplyResponse, SmartFlowResponse, SummaryResponse
from app.agent.policy import enforce_auto_reply_guardrails
from app.infrastructure.db.repositories import MongoRepository


class AgentService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo
        self.llm = get_llm_client()

    async def conversation_summary(self, user_id: str, conversation_id: str) -> SummaryResponse:
        messages = await self.repo.find_many(
            "messages",
            {"user_id": user_id, "conversation_id": conversation_id},
            limit=100,
            sort=[("timestamp", -1)],
        )
        text = "\n".join([m.get("text", "") for m in reversed(messages)])
        return await self.llm.summarize(text)

    async def draft_reply(self, user_id: str, conversation_id: str) -> DraftReplyResponse:
        summary = await self.conversation_summary(user_id, conversation_id)
        draft = await self.llm.draft_reply(summary.summary)
        draft.requires_human_review = True
        return draft

    async def decide_inbound(self, message_id: str) -> AutoReplyDecision:
        message = await self.repo.find_one("messages", {"_id": self.repo.object_id(message_id)})
        if not message:
            return AutoReplyDecision(
                should_reply=False,
                reply_text="",
                reason="message_missing",
                confidence=0.0,
                safe_to_auto_send=False,
            )
        conversation = await self.repo.find_one(
            "conversations",
            {"_id": self.repo.object_id(message["conversation_id"])},
        )
        settings = await self.repo.find_one("user_settings", {"user_id": message["user_id"]}) or {}
        rule = await self.repo.find_one(
            "automation_rules",
            {"user_id": message["user_id"], "enabled": True},
        ) or {"enabled": False}

        llm_decision = await self.llm.auto_reply_decision(message.get("text", ""))
        decision = enforce_auto_reply_guardrails(
            llm_decision,
            automation_mode=(conversation or {}).get("automation_mode", "manual"),
            auto_reply_mode_enabled=bool(settings.get("auto_reply_mode", False)),
            rule_enabled=bool(rule.get("enabled", False)),
        )

        if decision.should_reply and decision.safe_to_auto_send:
            cooldown_minutes = int((rule.get("conditions") or {}).get("cooldown_minutes", 5))
            last_auto_reply_at = (conversation or {}).get("last_auto_reply_at")
            now = datetime.now(UTC)
            if last_auto_reply_at:
                if last_auto_reply_at.tzinfo is None:
                    last_auto_reply_at = last_auto_reply_at.replace(tzinfo=UTC)
                if last_auto_reply_at + timedelta(minutes=cooldown_minutes) > now:
                    decision.should_reply = False
                    decision.safe_to_auto_send = False
                    decision.reason = "cooldown_active"
                    return decision
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
        return decision

    async def smartflow_ask(self, user_id: str, text: str) -> SmartFlowResponse:
        _ = user_id
        return await self.llm.ask(text)

