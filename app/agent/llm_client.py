from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.agent.prompts import VOICE_AGENT_SYSTEM_PROMPT
from app.shared.config import get_settings


class VoiceLLMClient(ABC):
    @abstractmethod
    async def generate_reply(self, history: list[dict[str, str]], user_text: str) -> str:
        raise NotImplementedError


class StubVoiceLLMClient(VoiceLLMClient):
    async def generate_reply(self, history: list[dict[str, str]], user_text: str) -> str:
        lowered = user_text.strip().lower()
        if "hello" in lowered or "hi" in lowered:
            return "Hello. I am here and listening. What do you need?"
        if "price" in lowered or "pricing" in lowered:
            return "I can help with pricing. Tell me which service or package you want."
        if "invoice" in lowered:
            return "I heard your invoice request. Tell me whether you want to cancel it, change the amount, or update the due date."
        if "meeting" in lowered or "schedule" in lowered:
            return "I can help with scheduling. Tell me the preferred day and time."
        if history:
            return f"You said: {user_text}. I am ready for the next step."
        return f"I heard: {user_text}. Tell me what you want me to do next."


class HuggingFaceVoiceLLMClient(VoiceLLMClient):
    def __init__(self):
        self.settings = get_settings()
        self.fallback = StubVoiceLLMClient()

    async def generate_reply(self, history: list[dict[str, str]], user_text: str) -> str:
        try:
            return await self._chat(history, user_text)
        except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
            return await self.fallback.generate_reply(history, user_text)

    async def _chat(self, history: list[dict[str, str]], user_text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, str]] = [{"role": "system", "content": VOICE_AGENT_SYSTEM_PROMPT}]
        for item in history[-12:]:
            role = item.get("role", "user")
            text = item.get("text", "")
            if role in {"user", "assistant"} and text:
                messages.append({"role": role, "content": text})
        messages.append({"role": "user", "content": user_text})

        body = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 220,
        }
        async with httpx.AsyncClient(
            base_url=self.settings.llm_api_base,
            timeout=self.settings.llm_timeout_seconds,
        ) as client:
            response = await client.post("/chat/completions", headers=headers, json=body)
            response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        text = self._coerce_message_content(content).strip()
        if not text:
            raise ValueError("Empty model response")
        return text

    @staticmethod
    def _coerce_message_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "".join(parts)
        raise ValueError("Unsupported response content")


def get_voice_llm_client() -> VoiceLLMClient:
    provider = get_settings().llm_provider.strip().lower()
    if provider in {"huggingface", "hf"}:
        return HuggingFaceVoiceLLMClient()
    return StubVoiceLLMClient()
