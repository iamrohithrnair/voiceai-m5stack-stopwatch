from __future__ import annotations

from typing import Any

from openai import OpenAI

from xiaozhi.memory_store import get_summary, set_summary


class LlmProvider:
    def __init__(
        self,
        config: dict[str, Any],
        system_prompt: str,
        memory: dict[str, Any] | None = None,
        device_id: str = "unknown",
    ) -> None:
        self.config = config
        self.system_prompt = system_prompt
        self.device_id = device_id
        self.client = OpenAI(
            api_key=self.config.get("api_key") or "not-needed",
            base_url=self.config.get("base_url"),
        )
        self.model = self.config.get("model", "gpt-4o-mini")
        self.history: list[dict[str, str]] = []
        memory = memory or {}
        self.memory_type = memory.get("type", "session")
        if self.memory_type == "none":
            self.memory_type = "none"
        elif memory.get("enabled") is False:
            self.memory_type = "none"
        self.max_turns = max(1, int(memory.get("max_turns", 10)))

    def reset(self) -> None:
        self.history.clear()

    def chat(self, user_text: str) -> str:
        if self.memory_type in ("none", "rolling_summary"):
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_text},
            ]
        else:
            self.history.append({"role": "user", "content": user_text})
            messages = [{"role": "system", "content": self.system_prompt}, *self.history]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        reply = (response.choices[0].message.content or "").strip()

        if self.memory_type == "session":
            self.history.append({"role": "assistant", "content": reply})
            max_messages = self.max_turns * 2
            if len(self.history) > max_messages:
                self.history = self.history[-max_messages:]
        elif self.memory_type == "rolling_summary":
            self._update_rolling_summary(user_text, reply)

        return reply

    def _update_rolling_summary(self, user_text: str, reply: str) -> None:
        previous = get_summary(self.device_id)
        prompt = (
            "Update the user memory summary. Keep it concise (under 200 words), third-person, "
            "factual, and focused on user interests and conversation themes. "
            "Do not invent facts.\n\n"
            f"Previous summary:\n{previous or '(none)'}\n\n"
            f"Latest exchange:\nUser: {user_text}\nAssistant: {reply}\n\n"
            "Write the updated summary only."
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        summary = (response.choices[0].message.content or "").strip()
        if summary:
            set_summary(self.device_id, summary)
