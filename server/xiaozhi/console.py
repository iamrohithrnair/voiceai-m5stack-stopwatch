from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web

from xiaozhi.config import load_config, public_host
from xiaozhi.config_store import load_public_config, save_config
from xiaozhi.memory_store import clear_all, list_devices
from xiaozhi.role_templates import ROLE_TEMPLATES

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

EDGE_VOICES = [
    {"id": "en-US-JennyNeural", "label": "English (US) — Jenny"},
    {"id": "en-US-GuyNeural", "label": "English (US) — Guy"},
    {"id": "en-GB-SoniaNeural", "label": "English (UK) — Sonia"},
    {"id": "zh-CN-XiaoxiaoNeural", "label": "Chinese — Xiaoxiao"},
    {"id": "zh-CN-YunxiNeural", "label": "Chinese — Yunxi"},
    {"id": "ja-JP-NanamiNeural", "label": "Japanese — Nanami"},
    {"id": "ko-KR-SunHiNeural", "label": "Korean — SunHi"},
    {"id": "de-DE-KatjaNeural", "label": "German — Katja"},
    {"id": "fr-FR-DeniseNeural", "label": "French — Denise"},
    {"id": "es-ES-ElviraNeural", "label": "Spanish — Elvira"},
]

OPENAI_TTS_VOICES = ["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]


async def console_page(_request: web.Request) -> web.Response:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return web.Response(text=html, content_type="text/html")


async def api_get_config(_request: web.Request) -> web.Response:
    config = load_public_config()
    cfg = load_config()
    return web.json_response(
        {
            "config": config,
            "meta": {
                "config_path": str(Path(__file__).resolve().parent.parent / "config.yaml"),
                "server_host": public_host(cfg),
                "server_port": int(cfg.get("server", {}).get("port", 8000)),
            },
        }
    )


async def api_put_config(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "Expected JSON object"}, status=400)
    saved = save_config(body)
    print("[console] configuration updated")
    return web.json_response({"ok": True, "config": saved})


async def api_voices(_request: web.Request) -> web.Response:
    return web.json_response({"edge": EDGE_VOICES, "openai": OPENAI_TTS_VOICES})


async def api_templates(_request: web.Request) -> web.Response:
    templates = {
        key: {"label": value["label"], "name": value["name"], "system_prompt": value["system_prompt"]}
        for key, value in ROLE_TEMPLATES.items()
    }
    return web.json_response(templates)


async def api_get_memory(_request: web.Request) -> web.Response:
    devices = list_devices()
    return web.json_response(
        {
            "devices": devices,
            "per_speaker": "Voice-print memory is not available in the local server yet.",
        }
    )


async def api_clear_memory(_request: web.Request) -> web.Response:
    clear_all()
    print("[console] memory cleared")
    return web.json_response({"ok": True})


def register_console_routes(app: web.Application) -> None:
    app.router.add_get("/console", console_page)
    app.router.add_get("/console/", console_page)
    app.router.add_get("/api/config", api_get_config)
    app.router.add_put("/api/config", api_put_config)
    app.router.add_get("/api/voices", api_voices)
    app.router.add_get("/api/templates", api_templates)
    app.router.add_get("/api/memory", api_get_memory)
    app.router.add_delete("/api/memory", api_clear_memory)
