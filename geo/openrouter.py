"""Cliente HTTP mínimo para OpenRouter (API compatible con OpenAI)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from geo.settings import get, get_float

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
APP_TITLE = "GEO Copilot"

NON_RETRYABLE = {400, 401, 402, 403, 404}
RETRYABLE = {408, 429, 500, 502, 503, 504}


class OpenRouterError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status = status
        self.retryable = retryable


@dataclass
class ChatResult:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    citations: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def _base_url() -> str:
    return (os.getenv("OPENROUTER_BASE_URL") or get("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def _api_key(api_key: str | None) -> str:
    if api_key is not None:
        return api_key.strip()
    env = os.getenv("OPENROUTER_API_KEY")
    if env is not None and env.strip() != "":
        return env.strip()
    return get("OPENROUTER_API_KEY").strip()


def _headers(api_key: str) -> dict[str, str]:
    h = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    referer = os.getenv("OPENROUTER_HTTP_REFERER", "https://geo-copilot.local")
    h["HTTP-Referer"] = referer
    h["X-Title"] = APP_TITLE
    return h


def _extract_citations(data: dict) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    try:
        msg = data["choices"][0]["message"]
    except Exception:
        msg = {}
    annotations = msg.get("annotations") or []
    for a in annotations:
        if isinstance(a, dict) and a.get("type") == "url_citation":
            url = (a.get("url_citation") or {}).get("url")
            if url and url not in seen:
                seen.add(url)
                out.append(url)
    # perplexity style
    for c in data.get("citations") or []:
        if isinstance(c, str) and c not in seen:
            seen.add(c)
            out.append(c)
        elif isinstance(c, dict):
            url = c.get("url")
            if url and url not in seen:
                seen.add(url)
                out.append(url)
    return out


def chat(messages, *, model, temperature=0.0, json_mode=False, web_search=False,
         max_tokens=4096, api_key=None, retries=4) -> ChatResult:
    key = _api_key(api_key)
    if not key:
        raise OpenRouterError("Falta OPENROUTER_API_KEY.", status=401, retryable=False)

    url = f"{_base_url()}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "usage": {"include": True},
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if web_search and not str(model).startswith("perplexity/"):
        payload["plugins"] = [{"id": "web", "max_results": 5}]

    had_response_format = json_mode
    attempt = 0
    last_exc: Exception | None = None
    while attempt <= retries:
        try:
            resp = requests.post(url, json=payload, headers=_headers(key), timeout=120)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= retries:
                raise OpenRouterError(f"Error de red: {exc}", status=None, retryable=True) from exc
            time.sleep(min(2 ** attempt, 10))
            attempt += 1
            continue

        # HTTP 200 con error en cuerpo
        try:
            data = resp.json()
        except Exception:
            data = {}
        if isinstance(data, dict) and "error" in data and resp.status_code == 200:
            # tratar como recuperable
            if attempt >= retries:
                raise OpenRouterError(str(data.get("error")), status=429, retryable=True)
            time.sleep(min(2 ** attempt, 10))
            attempt += 1
            continue

        if resp.status_code in NON_RETRYABLE:
            # 400 con response_format: reintentar una vez sin
            if resp.status_code == 400 and had_response_format and "response_format" in payload:
                del payload["response_format"]
                had_response_format = False
                # no cuenta como reintento
                continue
            msg = ""
            try:
                msg = (data.get("error") or {}).get("message", "") if isinstance(data, dict) else ""
            except Exception:
                msg = ""
            hint = ""
            if resp.status_code == 401:
                hint = "Clave inválida o revocada"
            elif resp.status_code == 402:
                hint = "Sin saldo en OpenRouter"
            elif resp.status_code == 404:
                hint = "Modelo no encontrado"
            full = f"{hint or 'Error del proveedor'}: {msg}".strip(": ").strip()
            # ensure hint present
            if hint and hint not in full:
                full = f"{hint}: {msg}".strip()
            raise OpenRouterError(full or hint or "Error", status=resp.status_code, retryable=False)

        if resp.status_code not in (200,) and resp.status_code not in RETRYABLE:
            # desconocido -> recuperable por defecto si 5xx-ish
            if resp.status_code >= 500:
                pass
            else:
                msg = ""
                try:
                    msg = (data.get("error") or {}).get("message", "") if isinstance(data, dict) else ""
                except Exception:
                    msg = ""
                raise OpenRouterError(msg or f"HTTP {resp.status_code}", status=resp.status_code, retryable=False)

        if resp.status_code in RETRYABLE:
            if attempt >= retries:
                msg = ""
                try:
                    msg = (data.get("error") or {}).get("message", "") if isinstance(data, dict) else ""
                except Exception:
                    msg = ""
                raise OpenRouterError(msg or f"HTTP {resp.status_code}", status=resp.status_code, retryable=True)
            time.sleep(min(2 ** attempt, 10))
            attempt += 1
            continue

        # 200 OK
        if not isinstance(data, dict) or "choices" not in data or not data["choices"]:
            if attempt >= retries:
                raise OpenRouterError("Respuesta sin choices", status=resp.status_code, retryable=True)
            time.sleep(min(2 ** attempt, 10))
            attempt += 1
            continue

        choice = data["choices"][0]
        msg_obj = choice.get("message") or {}
        text = msg_obj.get("content") or ""
        usage = data.get("usage") or {}
        tok_in = int(usage.get("prompt_tokens") or 0)
        tok_out = int(usage.get("completion_tokens") or 0)
        cost = usage.get("cost")
        cost_usd = float(cost) if cost is not None else None
        citations = _extract_citations(data)
        model_ret = data.get("model") or model
        return ChatResult(text=text, model=model_ret, tokens_in=tok_in, tokens_out=tok_out, cost_usd=cost_usd, citations=citations, raw=data)

    raise OpenRouterError("Error inesperado", status=None, retryable=True)


# ---- list_models, model_price, key_info, test_connection ----

_models_cache: dict[str, Any] = {"ts": 0.0, "data": None}
_models_lock = None
try:
    import threading

    _models_lock = threading.Lock()
except Exception:
    _models_lock = None


def _lock():
    if _models_lock is None:
        import threading

        return threading.Lock()
    return _models_lock


def list_models(force: bool = False) -> list[dict]:
    global _models_cache
    now = time.time()
    with _lock():
        if (not force) and _models_cache["data"] is not None and (now - _models_cache["ts"] < 3600):
            return list(_models_cache["data"])
    url = f"{_base_url()}/models"
    # /models no necesita clave, pero enviamos si hay
    key = _api_key(None)
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    raw_models = data.get("data") or data.get("models") or []
    out: list[dict] = []
    for m in raw_models:
        pricing = m.get("pricing") or {}
        pin = pricing.get("prompt")
        pout = pricing.get("completion")
        try:
            price_in_per_m = float(pin) * 1_000_000 if pin is not None else 0.0
        except (TypeError, ValueError):
            price_in_per_m = 0.0
        try:
            price_out_per_m = float(pout) * 1_000_000 if pout is not None else 0.0
        except (TypeError, ValueError):
            price_out_per_m = 0.0
        out.append(
            {
                "id": m.get("id"),
                "name": m.get("name") or m.get("id"),
                "price_in_per_m": price_in_per_m,
                "price_out_per_m": price_out_per_m,
                "context": m.get("context_length") or m.get("context"),
            }
        )
    with _lock():
        _models_cache["ts"] = now
        _models_cache["data"] = out
    return list(out)


def model_price(model_id: str) -> tuple[float, float] | None:
    for m in list_models():
        if m.get("id") == model_id:
            return (m["price_in_per_m"] / 1_000_000.0, m["price_out_per_m"] / 1_000_000.0)
    return None


def key_info(api_key: str | None = None) -> dict:
    key = _api_key(api_key)
    url = f"{_base_url()}/key"
    resp = requests.get(url, headers=_headers(key), timeout=60)
    if resp.status_code != 200:
        raise OpenRouterError("No se pudo consultar la clave", status=resp.status_code, retryable=False)
    data = resp.json()
    d = data.get("data") or data
    return {
        "label": d.get("label"),
        "usage": d.get("usage"),
        "limit": d.get("limit"),
        "is_free_tier": d.get("is_free_tier", False),
    }


def test_connection(model: str, api_key: str | None = None) -> dict:
    import time as _t

    info = key_info(api_key)
    key = _api_key(api_key)
    t0 = _t.time()
    res = chat(
        [{"role": "user", "content": "Responde solo con {\"ok\": true}"}],
        model=model,
        temperature=0.0,
        json_mode=True,
        api_key=key,
        retries=1,
    )
    latency = _t.time() - t0
    return {
        "key": info,
        "model": res.model,
        "latency_s": round(latency, 3),
        "reply": res.text,
        "cost_usd": res.cost_usd,
    }
