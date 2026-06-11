from __future__ import annotations

import io
from typing import Any

import edge_tts
from openai import OpenAI


class TtsProvider:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.provider = config.get("provider", "edge")

    async def synthesize(self, text: str) -> bytes:
        if self.provider == "openai":
            return await self._openai_tts(text)
        return await self._edge_tts(text)

    def _edge_rate(self) -> str:
        speed = int(self.config.get("speech_speed", 0))
        speed = max(-50, min(50, speed))
        return f"{speed:+d}%"

    def _edge_pitch(self) -> str:
        pitch = int(self.config.get("pitch", 0))
        pitch = max(-50, min(50, pitch))
        return f"{pitch:+d}Hz"

    async def _edge_tts(self, text: str) -> bytes:
        voice = self.config.get("voice", "en-US-JennyNeural")
        communicate = edge_tts.Communicate(
            text, voice, rate=self._edge_rate(), pitch=self._edge_pitch()
        )
        mp3 = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3.write(chunk["data"])
        return mp3.getvalue()

    async def _openai_tts(self, text: str) -> bytes:
        client = OpenAI(
            api_key=self.config.get("api_key") or "not-needed",
            base_url=self.config.get("base_url"),
        )
        model = self.config.get("model", "gpt-4o-mini-tts")
        voice = self.config.get("voice", "alloy")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        return response.content
