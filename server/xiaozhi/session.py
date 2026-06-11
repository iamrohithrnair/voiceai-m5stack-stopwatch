from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from aiohttp import web

from xiaozhi.audio import mp3_to_opus_packets, opus_packets_to_wav
from xiaozhi.providers import AsrProvider, LlmProvider, TtsProvider


class DeviceSession:
    def __init__(
        self,
        ws: web.WebSocketResponse,
        config: dict[str, Any],
        device_id: str = "unknown",
    ) -> None:
        self.ws = ws
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.device_id = device_id
        self.input_sample_rate = 16000
        self.output_sample_rate = 24000
        self.frame_duration_ms = 60
        self.audio_packets: list[bytes] = []
        self.listening = False
        self.processing = False

        assistant = config.get("assistant", {})
        system_prompt = assistant.get(
            "system_prompt", "You are a helpful voice assistant."
        )
        self.asr = AsrProvider(config.get("asr", {}))
        self.llm = LlmProvider(config.get("llm", {}), system_prompt)
        self.tts = TtsProvider(config.get("tts", {}))

    async def run(self) -> None:
        async for message in self.ws:
            if message.type == web.WSMsgType.BINARY:
                if self.listening and not self.processing:
                    self.audio_packets.append(message.data)
            elif message.type == web.WSMsgType.TEXT:
                await self._handle_text(message.data)
            elif message.type in (web.WSMsgType.CLOSE, web.WSMsgType.ERROR):
                break

    async def _handle_text(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[ws] invalid json from {self.device_id}: {raw[:120]}")
            return

        msg_type = data.get("type")
        if msg_type == "hello":
            await self._handle_hello(data)
        elif msg_type == "listen":
            await self._handle_listen(data)
        elif msg_type == "abort":
            self.audio_packets.clear()
            self.listening = False
        elif msg_type == "mcp":
            await self._handle_mcp(data)
        else:
            print(f"[ws] unhandled type={msg_type}")

    async def _handle_hello(self, data: dict[str, Any]) -> None:
        audio = data.get("audio_params", {})
        self.input_sample_rate = int(audio.get("sample_rate", 16000))
        self.frame_duration_ms = int(audio.get("frame_duration", 60))

        await self._send_json(
            {
                "type": "hello",
                "transport": "websocket",
                "session_id": self.session_id,
                "audio_params": {
                    "format": "opus",
                    "sample_rate": self.output_sample_rate,
                    "channels": 1,
                    "frame_duration": self.frame_duration_ms,
                },
            }
        )
        print(f"[ws] hello device={self.device_id} session={self.session_id}")

    async def _handle_listen(self, data: dict[str, Any]) -> None:
        state = data.get("state")
        if state == "start":
            self.audio_packets.clear()
            self.listening = True
            return

        if state in ("stop", "detect"):
            self.listening = False
            if self.processing or not self.audio_packets:
                return
            asyncio.create_task(self._process_turn())

    async def _process_turn(self) -> None:
        self.processing = True
        packets = list(self.audio_packets)
        self.audio_packets.clear()
        try:
            wav = opus_packets_to_wav(packets, self.input_sample_rate)
            user_text = await self.asr.transcribe(wav)
            if not user_text:
                return

            await self._send_json(
                {"session_id": self.session_id, "type": "stt", "text": user_text}
            )
            print(f"[ws] >> {user_text}")

            reply = self.llm.chat(user_text)
            if not reply:
                return

            await self._send_json(
                {
                    "session_id": self.session_id,
                    "type": "llm",
                    "emotion": "happy",
                    "text": "😊",
                }
            )
            await self._send_json(
                {"session_id": self.session_id, "type": "tts", "state": "start"}
            )
            await self._send_json(
                {
                    "session_id": self.session_id,
                    "type": "tts",
                    "state": "sentence_start",
                    "text": reply,
                }
            )
            print(f"[ws] << {reply}")

            mp3 = await self.tts.synthesize(reply)
            for packet in mp3_to_opus_packets(
                mp3, self.output_sample_rate, self.frame_duration_ms
            ):
                await self.ws.send_bytes(packet)

            await self._send_json(
                {"session_id": self.session_id, "type": "tts", "state": "stop"}
            )
        except Exception as exc:
            print(f"[ws] turn failed: {exc}")
            await self._send_json(
                {
                    "session_id": self.session_id,
                    "type": "alert",
                    "status": "Error",
                    "message": str(exc),
                    "emotion": "sad",
                }
            )
        finally:
            self.processing = False

    async def _handle_mcp(self, data: dict[str, Any]) -> None:
        payload = data.get("payload", {})
        method = payload.get("method")
        req_id = payload.get("id")
        if req_id is None:
            return

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "local-xiaozhi", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {"tools": [], "nextCursor": ""}
        else:
            result = {"content": [{"type": "text", "text": "ok"}], "isError": False}

        await self._send_json(
            {
                "session_id": self.session_id,
                "type": "mcp",
                "payload": {"jsonrpc": "2.0", "id": req_id, "result": result},
            }
        )

    async def _send_json(self, payload: dict[str, Any]) -> None:
        await self.ws.send_str(json.dumps(payload, separators=(",", ":")))
