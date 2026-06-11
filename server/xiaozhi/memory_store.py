from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MEMORY_PATH = DATA_DIR / "memory.json"


def _load_all() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return {}
    try:
        with MEMORY_PATH.open(encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with MEMORY_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def get_summary(device_id: str) -> str:
    entry = _load_all().get(device_id, {})
    return str(entry.get("summary", ""))


def set_summary(device_id: str, summary: str) -> None:
    data = _load_all()
    entry = data.setdefault(device_id, {})
    entry["summary"] = summary
    _save_all(data)


def clear_all() -> None:
    _save_all({})


def clear_device(device_id: str) -> None:
    data = _load_all()
    data.pop(device_id, None)
    _save_all(data)


def list_devices() -> dict[str, str]:
    return {device_id: str(entry.get("summary", "")) for device_id, entry in _load_all().items()}
