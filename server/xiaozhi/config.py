from __future__ import annotations

import os
import re
import socket
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "config.example.yaml"


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(
            r"\$\{([^}]+)\}",
            lambda m: os.environ.get(m.group(1), ""),
            value,
        )
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        cfg_path = EXAMPLE_PATH
    with cfg_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return _expand_env(data)


def public_host(config: dict[str, Any]) -> str:
    server = config.get("server", {})
    return server.get("public_host") or get_local_ip()


def websocket_url(config: dict[str, Any]) -> str:
    server = config.get("server", {})
    port = int(server.get("port", 8000))
    return f"ws://{public_host(config)}:{port}/xiaozhi/v1/"
