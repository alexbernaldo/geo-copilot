"""Ajustes persistentes: lectura/escritura de .env en tiempo de llamada."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT_DIR: Path = Path(__file__).resolve().parent.parent
ENV_PATH: Path = ROOT_DIR / ".env"

DEFAULTS: dict[str, str] = {
    "LLM_PROVIDER": "mock",
    "OPENROUTER_API_KEY": "",
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "LLM_MODEL": "google/gemini-2.5-flash",
    "LLM_MODEL_WRITER": "anthropic/claude-sonnet-4.5",
    "LLM_MODEL_PROPOSER": "google/gemini-2.5-flash",
    "GEO_DATA_DIR": "./data",
    "GEO_EJEMPLO": "1",
    "LLM_CONCURRENCY": "8",
    "MAX_LLM_CALLS": "1500",
    "MAX_BUDGET_EUR": "5.0",
    "USD_EUR": "0.92",
    "ENGINE_MODEL_CHATGPT": "openai/gpt-4o-mini",
    "ENGINE_MODEL_GEMINI": "google/gemini-2.5-flash",
    "ENGINE_MODEL_CLAUDE": "anthropic/claude-haiku-4.5",
    "ENGINE_MODEL_PERPLEXITY": "perplexity/sonar",
    "ANTHROPIC_API_KEY": "",
    "OPENAI_API_KEY": "",
}

SECRET_KEYS: set[str] = {"OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"}


def _strip_inline_comment(value: str) -> str:
    if " #" in value:
        return value.split(" #", 1)[0].rstrip()
    return value


def get(key: str) -> str:
    raw = os.environ.get(key)
    if raw is None:
        raw = DEFAULTS.get(key, "")
    if key not in SECRET_KEYS:
        raw = _strip_inline_comment(raw)
    return raw.strip() if key not in SECRET_KEYS else raw


def get_int(key: str) -> int:
    v = get(key).strip()
    # quitar comentarios
    v = v.split("#")[0].strip() if key not in SECRET_KEYS else v.strip()
    return int(v) if v else int(DEFAULTS.get(key, "0") or 0)


def get_float(key: str) -> float:
    v = get(key).strip()
    v = v.split("#")[0].strip() if key not in SECRET_KEYS else v.strip()
    return float(v) if v else float(DEFAULTS.get(key, "0") or 0)


def current() -> dict[str, str]:
    out: dict[str, str] = {}
    for k in DEFAULTS:
        out[k] = get(k)
    return out


def mask(secret: str) -> str:
    s = (secret or "").strip()
    if not s:
        return ""
    if len(s) <= 8:
        return "…" + s[-4:] if len(s) >= 4 else "…"
    return s[:6] + "…" + s[-4:]


def has_openrouter_key() -> bool:
    return bool(get("OPENROUTER_API_KEY").strip())


def save(values: dict[str, str]) -> Path:
    # leer lineas existentes
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    # mapear claves existentes
    existing: dict[str, int] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            existing[k] = i
    for key, val in values.items():
        new_line = f"{key}={val}"
        if key in existing:
            lines[existing[key]] = new_line
        else:
            lines.append(new_line)
            existing[key] = len(lines) - 1
    # chmod 600
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        ENV_PATH.chmod(0o600)
    except Exception:
        pass
    # actualizar os.environ
    for key, val in values.items():
        os.environ[key] = val
    return ENV_PATH