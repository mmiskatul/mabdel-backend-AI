from __future__ import annotations

from datetime import UTC, datetime

from app.agent.graphs import VoiceAgentGraph
from app.agent.llm_client import get_voice_llm_client
from app.agent.models import AgentMessage, AgentReplyResponse, AgentSessionResponse
from app.persistence.repositories import MongoRepository
from app.shared.errors import ForbiddenError, NotFoundError


class AgentService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo
        self.graph = VoiceAgentGraph(repo, get_voice_llm_client())

    async def create_session(self, user_id: str) -> AgentSessionResponse:
        now = datetime.now(UTC)
        session_id = await self.repo.insert_one(
            "agent_sessions",
            {
                "user_id": user_id,
                "created_at": now,
                "last_active_at": now,
            },
        )
        return AgentSessionResponse(session_id=session_id, created_at=now)

    async def get_messages(self, user_id: str, session_id: str) -> list[AgentMessage]:
        await self._ensure_session(user_id, session_id)
        messages = await self.repo.find_many(
            "agent_messages",
            {"user_id": user_id, "session_id": session_id},
            limit=100,
            sort=[("created_at", 1)],
        )
        return [AgentMessage.model_validate(item) for item in messages]

    async def respond(self, user_id: str, session_id: str, text: str) -> AgentReplyResponse:
        await self._ensure_session(user_id, session_id)
        state = await self.graph.run(
            {
                "user_id": user_id,
                "session_id": session_id,
                "user_text": text,
            }
        )
        turns = [AgentMessage(role=item["role"], text=item["text"]) for item in state.get("persisted_turns", [])]
        return AgentReplyResponse(
            session_id=session_id,
            reply_text=state["reply_text"],
            turns=turns,
        )

    async def _ensure_session(self, user_id: str, session_id: str) -> dict:
        session = await self.repo.find_one(
            "agent_sessions",
            {"_id": self.repo.object_id(session_id)},
        )
        if not session:
            raise NotFoundError("Agent session not found")
        if session["user_id"] != user_id:
            raise ForbiddenError()
        return session
