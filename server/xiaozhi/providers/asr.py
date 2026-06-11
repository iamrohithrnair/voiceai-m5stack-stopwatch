from __future__ import annotations

import io
from typing import Any

from openai import OpenAI


class AsrProvider:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.provider = config.get("provider", "openai")

    async def transcribe(self, wav_bytes: bytes) -> str:
        if self.provider == "local_whisper":
            return await self._local_whisper(wav_bytes)
        return await self._openai_whisper(wav_bytes)

    async def _openai_whisper(self, wav_bytes: bytes) -> str:
        client = OpenAI(
            api_key=self.config.get("api_key") or "not-needed",
            base_url=self.config.get("base_url"),
        )
        model = self.config.get("model", "whisper-1")
        audio = io.BytesIO(wav_bytes)
        audio.name = "audio.wav"
        result = client.audio.transcriptions.create(model=model, file=audio)
        return (result.text or "").strip()

    async def _local_whisper(self, wav_bytes: bytes) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Install faster-whisper for local ASR: pip install faster-whisper"
            ) from exc

        import tempfile
        from pathlib import Path

        model_name = self.config.get("model", "base")
        device = self.config.get("device", "cpu")
        model = WhisperModel(model_name, device=device, compute_type="int8")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            path = Path(tmp.name)

        segments, _info = model.transcribe(str(path), beam_size=1)
        text = "".join(seg.text for seg in segments).strip()
        path.unlink(missing_ok=True)
        return text
