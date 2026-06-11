from __future__ import annotations

from typing import Any

from openai import OpenAI


class LlmProvider:
    def __init__(self, config: dict[str, Any], system_prompt: str) -> None:
        self.config = config
        self.system_prompt = system_prompt
        self.client = OpenAI(
            api_key=self.config.get("api_key") or "not-needed",
            base_url=self.config.get("base_url"),
        )
        self.model = self.config.get("model", "gpt-4o-mini")
        self.history: list[dict[str, str]] = []

    def reset(self) -> None:
        self.history.clear()

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        messages = [{"role": "system", "content": self.system_prompt}, *self.history]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        reply = (response.choices[0].message.content or "").strip()
        self.history.append({"role": "assistant", "content": reply})
        # Keep context bounded
        if len(self.history) > 20:
            self.history = self.history[-20:]
        return reply
