"""YAML configuration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve() if path else DEFAULT_CONFIG
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return data


def deep_get(data: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    cur: Any = data
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

