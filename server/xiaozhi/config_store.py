from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import yaml

from xiaozhi.config import CONFIG_PATH, EXAMPLE_PATH, _expand_env
from xiaozhi.memory_store import get_summary

SECRET_KEYS = ("api_key", "password", "secret", "token")
MASK = "••••••••"

LANGUAGE_NAMES = {
    "auto": "the same language the user speaks",
    "en": "English",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
}


def _mask_secrets(data: Any, parent_key: str = "") -> Any:
    if isinstance(data, dict):
        out = {}
        for key, value in data.items():
            if key in SECRET_KEYS and isinstance(value, str) and value:
                out[key] = MASK
            else:
                out[key] = _mask_secrets(value, key)
        return out
    if isinstance(data, list):
        return [_mask_secrets(item, parent_key) for item in data]
    return data


def _merge_secrets(new_data: dict, old_data: dict) -> dict:
    merged = copy.deepcopy(new_data)
    for key, value in old_data.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_secrets(merged[key], value)
        elif key in SECRET_KEYS and merged.get(key) == MASK:
            merged[key] = value
    return merged


def load_raw_config() -> dict[str, Any]:
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_public_config() -> dict[str, Any]:
    raw = load_raw_config()
    return _mask_secrets(_expand_env(raw))


def save_config(updates: dict[str, Any]) -> dict[str, Any]:
    current = load_raw_config()
    merged = _merge_secrets(updates, current)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(merged, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return load_public_config()


def build_system_prompt(config: dict[str, Any], device_id: str | None = None) -> str:
    assistant = config.get("assistant", {})
    name = assistant.get("name", "XiaoZhi")
    prompt = assistant.get("system_prompt", "You are a helpful voice assistant.").strip()

    language = assistant.get("dialogue_language", "auto")
    lang_name = LANGUAGE_NAMES.get(language, language)
    if language != "auto":
        prompt += f"\n\nAlways respond in {lang_name}."

    memory = config.get("memory", {})
    memory_type = memory.get("type", "session" if memory.get("enabled", True) else "none")

    if memory_type == "none":
        prompt += f"\n\nYour name is {name}. Treat each user message independently."
    elif memory_type == "rolling_summary" and device_id:
        summary = get_summary(device_id)
        prompt += f"\n\nYour name is {name}."
        if summary:
            prompt += f"\n\nWhat you remember about this user from past conversations:\n{summary}"
    else:
        turns = int(memory.get("max_turns", 10))
        prompt += (
            f"\n\nYour name is {name}. Remember the last {turns} turns of this conversation."
        )

    return prompt
