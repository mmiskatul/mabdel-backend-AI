from __future__ import annotations

from datetime import UTC, datetime

from langgraph.graph import END, START, StateGraph

from app.agent.llm_client import VoiceLLMClient
from app.agent.models import AgentGraphState
from app.persistence.repositories import MongoRepository


class VoiceAgentGraph:
    def __init__(self, repo: MongoRepository, llm: VoiceLLMClient):
        self.repo = repo
        self.llm = llm
        self.graph = self._build_graph().compile()

    async def run(self, state: AgentGraphState) -> AgentGraphState:
        return await self.graph.ainvoke(state)

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentGraphState)
        graph.add_node("load_history", self.load_history)
        graph.add_node("reply_node", self.reply_node)
        graph.add_node("persist_turn", self.persist_turn)
        graph.add_edge(START, "load_history")
        graph.add_edge("load_history", "reply_node")
        graph.add_edge("reply_node", "persist_turn")
        graph.add_edge("persist_turn", END)
        return graph

    async def load_history(self, state: AgentGraphState) -> AgentGraphState:
        messages = await self.repo.find_many(
            "agent_messages",
            {"user_id": state["user_id"], "session_id": state["session_id"]},
            limit=20,
            sort=[("created_at", 1)],
        )
        history = [{"role": item["role"], "text": item["text"]} for item in messages]
        return {"history": history}

    async def reply_node(self, state: AgentGraphState) -> AgentGraphState:
        reply_text = await self.llm.generate_reply(state.get("history", []), state["user_text"])
        return {"reply_text": reply_text}

    async def persist_turn(self, state: AgentGraphState) -> AgentGraphState:
        now = datetime.now(UTC)
        user_turn = {
            "user_id": state["user_id"],
            "session_id": state["session_id"],
            "role": "user",
            "text": state["user_text"],
            "created_at": now,
        }
        assistant_turn = {
            "user_id": state["user_id"],
            "session_id": state["session_id"],
            "role": "assistant",
            "text": state["reply_text"],
            "created_at": now,
        }
        await self.repo.insert_one("agent_messages", user_turn)
        await self.repo.insert_one("agent_messages", assistant_turn)
        await self.repo.update_one(
            "agent_sessions",
            {"_id": self.repo.object_id(state["session_id"]), "user_id": state["user_id"]},
            {"$set": {"last_active_at": now}},
        )
        return {
            "persisted_turns": [
                {"role": "user", "text": state["user_text"]},
                {"role": "assistant", "text": state["reply_text"]},
            ]
        }
