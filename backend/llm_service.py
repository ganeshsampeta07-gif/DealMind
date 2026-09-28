from __future__ import annotations

from typing import Any, Dict

from groq import Groq

from .config import GROQ_API_KEY, GROQ_MODEL


class LLMService:
    """Service wrapper for Groq-based conversations."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            raise ValueError("GROQ_API_KEY is missing.")

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            return completion.choices[0].message.content
        except Exception as exc:  # pragma: no cover - runtime validation to be added later
            raise RuntimeError("The AI service is temporarily unavailable.") from exc

    def generate_text(self, user_prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        return self.generate_response(system_prompt, user_prompt)


llm_service = LLMService()


def generate_response(system_prompt: str, user_prompt: str) -> str:
    return llm_service.generate_response(system_prompt, user_prompt)


def generate_text(user_prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    return llm_service.generate_text(user_prompt, system_prompt)
