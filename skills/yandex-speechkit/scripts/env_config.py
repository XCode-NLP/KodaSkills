#!/usr/bin/env python3
"""Minimal .env loader for local project scripts."""

from __future__ import annotations

import os
from pathlib import Path


def load_project_env() -> Path | None:
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / ".env"
    if not env_path.is_file():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)
    return env_path


def has_object_storage_env() -> bool:
    required_keys = (
        "YANDEX_STORAGE_ACCESS_KEY",
        "YANDEX_STORAGE_SECRET_KEY",
        "YANDEX_STORAGE_BUCKET",
    )
    return all(os.getenv(key) for key in required_keys)
