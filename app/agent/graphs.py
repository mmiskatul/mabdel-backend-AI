from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.models import AutoReplyDecision, DraftReplyResponse, SmartFlowResponse, SummaryResponse
from app.agent.prompts import analyze_inbound_text, safe_review_reply
from app.infrastructure.db.repositories import MongoRepository


class AgentGraphState(TypedDict, total=False):
    user_id: str
    run_id: str | None
    run_type: str
    conversation_id: str | None
    message_id: str | None
    input_text: str | None
    inbound_text: str | None
    conversation_context: str
    user_settings: dict[str, Any]
    policy_flags: dict[str, Any]
    llm_output: dict[str, Any]
    tool_requests: list[dict[str, Any]]
    final_output: dict[str, Any]
    errors: list[str]


class AgentWorkflow:
    def __init__(self, repo: MongoRepository, llm_client):
        self.repo = repo
        self.llm = llm_client
        self.graph = self._build_graph().compile()

    async def run(self, state: AgentGraphState) -> AgentGraphState:
        initial_state: AgentGraphState = {
            "user_id": state["user_id"],
            "run_type": state["run_type"],
            "conversation_id": state.get("conversation_id"),
            "message_id": state.get("message_id"),
            "input_text": state.get("input_text"),
            "inbound_text": state.get("inbound_text"),
            "conversation_context": state.get("conversation_context", ""),
            "user_settings": state.get("user_settings", {}),
            "policy_flags": state.get("policy_flags", {}),
            "tool_requests": state.get("tool_requests", []),
            "errors": state.get("errors", []),
        }
        return await self.graph.ainvoke(initial_state)

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentGraphState)
        graph.add_node("load_context_node", self.load_context_node)
        graph.add_node("safety_scan_node", self.safety_scan_node)
        graph.add_node("route_node", self.route_node)
        graph.add_node("summary_llm_node", self.summary_llm_node)
        graph.add_node("draft_reply_llm_node", self.draft_reply_llm_node)
        graph.add_node("auto_reply_llm_node", self.auto_reply_llm_node)
        graph.add_node("smartflow_llm_node", self.smartflow_llm_node)
        graph.add_node("guardrail_node", self.guardrail_node)
        graph.add_node("tool_execution_node", self.tool_execution_node)
        graph.add_node("persist_run_node", self.persist_run_node)
        graph.add_node("finish_node", self.finish_node)

        graph.add_edge(START, "load_context_node")
        graph.add_edge("load_context_node", "safety_scan_node")
        graph.add_edge("safety_scan_node", "route_node")
        graph.add_conditional_edges(
            "route_node",
            self._route_run_type,
            {
                "summary_llm_node": "summary_llm_node",
                "draft_reply_llm_node": "draft_reply_llm_node",
                "auto_reply_llm_node": "auto_reply_llm_node",
                "smartflow_llm_node": "smartflow_llm_node",
            },
        )
        graph.add_edge("summary_llm_node", "guardrail_node")
        graph.add_edge("draft_reply_llm_node", "guardrail_node")
        graph.add_edge("auto_reply_llm_node", "guardrail_node")
        graph.add_edge("smartflow_llm_node", "guardrail_node")
        graph.add_conditional_edges(
            "guardrail_node",
            self._route_after_guardrail,
            {
                "tool_execution_node": "tool_execution_node",
                "persist_run_node": "persist_run_node",
            },
        )
        graph.add_edge("tool_execution_node", "persist_run_node")
        graph.add_edge("persist_run_node", "finish_node")
        graph.add_edge("finish_node", END)
        return graph

    async def load_context_node(self, state: AgentGraphState) -> AgentGraphState:
        updates: AgentGraphState = {
            "errors": list(state.get("errors", [])),
            "tool_requests": list(state.get("tool_requests", [])),
        }
        user_settings = await self.repo.find_one("user_settings", {"user_id": state["user_id"]}) or {}
        updates["user_settings"] = user_settings

        conversation_id = state.get("conversation_id")
        message_id = state.get("message_id")
        if message_id:
            message = await self.repo.find_one("messages", {"_id": self.repo.object_id(message_id)})
            if not message:
                updates["errors"] = [*updates["errors"], "message_missing"]
                updates["inbound_text"] = state.get("input_text") or ""
            else:
                updates["message_id"] = message["id"]
                updates["conversation_id"] = message.get("conversation_id") or conversation_id
                updates["inbound_text"] = message.get("text", "")

        resolved_conversation_id = updates.get("conversation_id") or conversation_id
        if resolved_conversation_id:
            messages = await self.repo.find_many(
                "messages",
                {"user_id": state["user_id"], "conversation_id": resolved_conversation_id},
                limit=100,
                sort=[("timestamp", -1)],
            )
            updates["conversation_context"] = "\n".join(m.get("text", "") for m in reversed(messages))

        if not updates.get("inbound_text"):
            updates["inbound_text"] = state.get("input_text") or state.get("inbound_text") or ""
        if "conversation_context" not in updates:
            updates["conversation_context"] = state.get("conversation_context", "")
        return updates

    async def safety_scan_node(self, state: AgentGraphState) -> AgentGraphState:
        scan_target = state.get("inbound_text") or state.get("conversation_context", "")
        return {"policy_flags": analyze_inbound_text(scan_target)}

    async def route_node(self, state: AgentGraphState) -> AgentGraphState:
        return {"tool_requests": list(state.get("tool_requests", []))}

    async def summary_llm_node(self, state: AgentGraphState) -> AgentGraphState:
        summary = await self.llm.summarize(state.get("conversation_context", ""))
        return {"llm_output": summary.model_dump()}

    async def draft_reply_llm_node(self, state: AgentGraphState) -> AgentGraphState:
        source_text = state.get("conversation_context") or state.get("inbound_text", "")
        draft = await self.llm.draft_reply(source_text)
        return {"llm_output": draft.model_dump()}

    async def auto_reply_llm_node(self, state: AgentGraphState) -> AgentGraphState:
        decision = await self.llm.auto_reply_decision(state.get("inbound_text", ""))
        return {"llm_output": decision.model_dump()}

    async def smartflow_llm_node(self, state: AgentGraphState) -> AgentGraphState:
        response = await self.llm.ask(state.get("input_text") or state.get("inbound_text", ""))
        return {"llm_output": response.model_dump()}

    async def guardrail_node(self, state: AgentGraphState) -> AgentGraphState:
        policy_flags = state.get("policy_flags", {})
        tool_requests = list(state.get("tool_requests", []))
        run_type = state["run_type"]
        llm_output = state.get("llm_output", {})

        if run_type == "summary":
            summary = SummaryResponse.model_validate(llm_output)
            return {"final_output": summary.model_dump(), "tool_requests": tool_requests}

        if run_type == "draft_reply":
            draft = DraftReplyResponse.model_validate(llm_output)
            draft.requires_human_review = True
            draft.safe_to_auto_send = False
            if policy_flags.get("prompt_injection_detected") or policy_flags.get("sensitive_topic"):
                draft.reason = "review_required_untrusted_or_sensitive"
                if policy_flags.get("prompt_injection_detected") and "prompt_injection" not in draft.tags:
                    draft.tags.append("prompt_injection")
                if policy_flags.get("sensitive_topic") and "sensitive" not in draft.tags:
                    draft.tags.append("sensitive")
            return {"final_output": draft.model_dump(), "tool_requests": tool_requests}

        if run_type == "auto_reply_decision":
            decision = AutoReplyDecision.model_validate(llm_output)
            if policy_flags.get("prompt_injection_detected") or policy_flags.get("sensitive_topic"):
                decision.should_reply = False
                decision.safe_to_auto_send = False
                decision.requires_human_review = True
                decision.reason = "review_required_untrusted_or_sensitive"
                decision.prompt_injection_detected = bool(policy_flags.get("prompt_injection_detected"))
                decision.sensitive_topic = bool(policy_flags.get("sensitive_topic"))
            return {"final_output": decision.model_dump(), "tool_requests": tool_requests}

        response = SmartFlowResponse.model_validate(llm_output)
        prompt_injection = bool(policy_flags.get("prompt_injection_detected"))
        sensitive_topic = bool(policy_flags.get("sensitive_topic"))
        if prompt_injection or sensitive_topic:
            response.answer = safe_review_reply(
                state.get("input_text") or state.get("inbound_text", ""),
                secure_channel=bool(policy_flags.get("secret_request_detected")),
            )
        if "notify" in (state.get("input_text") or "").lower():
            tool_requests.append({"name": "notify_user", "payload": {"channel": "inbox_notification"}})
            response.suggested_actions.append({"type": "notify_user", "status": "prepared"})
        return {"final_output": response.model_dump(), "tool_requests": tool_requests}

    async def tool_execution_node(self, state: AgentGraphState) -> AgentGraphState:
        final_output = dict(state.get("final_output", {}))
        tool_results: list[dict[str, Any]] = []
        for request in state.get("tool_requests", []):
            if request.get("name") == "notify_user":
                tool_results.append({"name": "notify_user", "status": "prepared"})
        if tool_results:
            suggested_actions = list(final_output.get("suggested_actions", []))
            suggested_actions.extend(tool_results)
            final_output["suggested_actions"] = suggested_actions
        return {"final_output": final_output}

    async def persist_run_node(self, state: AgentGraphState) -> AgentGraphState:
        now = datetime.now(UTC)
        payload = {
            "user_id": state["user_id"],
            "run_type": state["run_type"],
            "input_ref": {
                "conversation_id": state.get("conversation_id"),
                "message_id": state.get("message_id"),
            },
            "output": state.get("final_output", {}),
            "state_snapshots": {
                "policy_flags": state.get("policy_flags", {}),
                "tool_requests": state.get("tool_requests", []),
            },
            "status": "failed" if state.get("errors") else "completed",
            "error": "; ".join(state.get("errors", [])) if state.get("errors") else None,
            "created_at": now,
        }
        run_id = await self.repo.insert_one("agent_runs", payload)
        return {"run_id": run_id}

    async def finish_node(self, state: AgentGraphState) -> AgentGraphState:
        final_output = dict(state.get("final_output", {}))
        if state.get("run_id"):
            final_output["agent_run_id"] = state["run_id"]
        return {"final_output": final_output}

    @staticmethod
    def _route_run_type(state: AgentGraphState) -> str:
        mapping = {
            "summary": "summary_llm_node",
            "draft_reply": "draft_reply_llm_node",
            "auto_reply_decision": "auto_reply_llm_node",
            "smartflow": "smartflow_llm_node",
        }
        return mapping.get(state["run_type"], "smartflow_llm_node")

    @staticmethod
    def _route_after_guardrail(state: AgentGraphState) -> str:
        return "tool_execution_node" if state.get("tool_requests") else "persist_run_node"
