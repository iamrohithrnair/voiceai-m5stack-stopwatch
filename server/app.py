#!/usr/bin/env python3
"""Local XiaoZhi server — OTA config + WebSocket voice chat."""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
import sys
import time
from pathlib import Path

from aiohttp import web

sys.path.insert(0, str(Path(__file__).resolve().parent))

from xiaozhi.config import load_config, public_host, websocket_url
from xiaozhi.session import DeviceSession


def _ota_json(config: dict) -> str:
    server_cfg = config.get("server", {})
    tz = int(server_cfg.get("timezone_offset", 0))
    return json.dumps(
        {
            "server_time": {
                "timestamp": int(time.time() * 1000),
                "timezone_offset": tz * 60,
            },
            "firmware": {"version": "0.0.0", "url": ""},
            "websocket": {
                "url": websocket_url(config),
                "token": "",
                "version": 1,
            },
        },
        separators=(",", ":"),
    )


async def ota_get(_request: web.Request) -> web.Response:
    config = load_config()
    return web.Response(text=f"Local XiaoZhi OTA OK. WebSocket: {websocket_url(config)}")


async def ota_post(request: web.Request) -> web.Response:
    config = load_config()
    device_id = request.headers.get("Device-Id") or request.headers.get("device-id", "")
    if not device_id:
        return web.Response(status=400, text="Device-Id required")
    print(f"[ota] device={device_id}")
    return web.Response(text=_ota_json(config), content_type="application/json")


async def ota_options(_request: web.Request) -> web.Response:
    return web.Response(status=204)


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    config = load_config()
    device_id = request.headers.get("Device-Id", "unknown")
    session = DeviceSession(ws, config, device_id)
    try:
        await session.run()
    except Exception as exc:
        print(f"[ws] disconnected ({exc})")
    return ws


def _port_in_use_message(port: int) -> str:
    return (
        f"Port {port} is already in use.\n"
        f"  • Stop the other server (Ctrl+C in its terminal), or\n"
        f"  • Kill it: lsof -ti:{port} | xargs kill\n"
        f"  • Use another port: python app.py --port {port + 1}"
    )


async def main(port_override: int | None = None) -> None:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    if not config_path.exists():
        print("Copy config.example.yaml to config.yaml and set your model API keys.")

    config = load_config()
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = port_override or int(config.get("server", {}).get("port", 8000))
    if port_override:
        config.setdefault("server", {})["port"] = port

    llm = config.get("llm", {})
    print(
        f"Local XiaoZhi | LLM={llm.get('model')} | "
        f"ASR={config.get('asr', {}).get('provider')} | "
        f"TTS={config.get('tts', {}).get('provider')}"
    )

    app = web.Application()
    app.router.add_get("/xiaozhi/ota/", ota_get)
    app.router.add_post("/xiaozhi/ota/", ota_post)
    app.router.add_route("OPTIONS", "/xiaozhi/ota/", ota_options)
    app.router.add_get("/xiaozhi/v1/", websocket_handler)
    app.router.add_get("/xiaozhi/v1", websocket_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port, reuse_address=True)

    stop = asyncio.Event()

    def _request_stop() -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            pass

    try:
        await site.start()
    except OSError as exc:
        if exc.errno in (48, 98):  # macOS / Linux "address already in use"
            print(_port_in_use_message(port), file=sys.stderr)
            await runner.cleanup()
            sys.exit(1)
        raise

    lan = public_host(config)
    print(f"[server] ready on {lan}:{port}")
    print(f"  OTA:       http://{lan}:{port}/xiaozhi/ota/")
    print(f"  WebSocket: ws://{lan}:{port}/xiaozhi/v1/")
    print("  Press Ctrl+C to stop")

    await stop.wait()
    print("\n[server] shutting down...")
    await runner.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local XiaoZhi voice server")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Listen port (default: server.port in config.yaml, usually 8000)",
    )
    args = parser.parse_args()
    try:
        asyncio.run(main(port_override=args.port))
    except KeyboardInterrupt:
        print("\n[server] stopped")
