"""Conector Gemini (Google GenAI SDK + Grounding with Google Search) con caché y degradación (F15)."""

import json
import os
import time
from urllib.request import Request, urlopen

from geo.config import LLM_PROVIDER
from geo.engines.openai_engine import _cache_path, extract_domain


def run(
    prompt: str,
    *,
    model: str = "gemini-2.0-flash",
    repeticion: int = 1,
    use_cache: bool = True,
    allow_mock_fallback: bool = True,
) -> tuple[str, list[str], bool]:
    """Ejecuta un prompt en Gemini API activando `google_search` grounding.

    Extrae las URLs de `grounding_metadata.grounding_chunks` y devuelve `(respuesta, dominios, degradado)`.
    """
    cpath = _cache_path("gemini", model, prompt, repeticion)
    if use_cache and cpath.exists():
        data = json.loads(cpath.read_text(encoding="utf-8"))
        return str(data["respuesta"]), list(data["dominios"]), bool(data.get("degradado", False))

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().lower()

    if provider != "mock" and api_key:
        for attempt in range(3):
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                    f"?key={api_key}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "tools": [{"google_search": {}}],
                }
                req = Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(req, timeout=30) as resp:  # noqa: S310
                    raw = json.loads(resp.read().decode("utf-8"))

                candidates = raw.get("candidates", [])
                text_out = ""
                domains: list[str] = []
                if candidates:
                    cand = candidates[0]
                    for part in cand.get("content", {}).get("parts", []):
                        if "text" in part:
                            text_out += str(part["text"])
                    gm = cand.get("groundingMetadata") or cand.get("grounding_metadata") or {}
                    chunks = gm.get("groundingChunks") or gm.get("grounding_chunks") or []
                    for ch in chunks:
                        web_info = ch.get("web", {}) if isinstance(ch, dict) else {}
                        u = web_info.get("uri") or web_info.get("url") or ""
                        dom = extract_domain(str(u))
                        if dom and dom not in domains:
                            domains.append(dom)

                if text_out:
                    cpath.write_text(
                        json.dumps(
                            {"respuesta": text_out, "dominios": domains, "degradado": False},
                            ensure_ascii=False,
                        ),
                        encoding="utf-8",
                    )
                    return text_out, domains, False
            except Exception:
                if attempt < 2:
                    time.sleep(0.5 * (2**attempt))

    if not allow_mock_fallback:
        raise RuntimeError("Gemini API con google_search grounding no disponible y fallback desactivado.")

    mock_text = (
        f"[Simulación conector Gemini + google_search grounding · rep={repeticion}] "
        f"En respuesta a «{prompt}», las principales referencias clínicas de oftalmología en España incluyen "
        f"IMO Grupo Miranza, Clínica Baviera y Barraquer, respaldadas por directorios médicos y sociedades científicas."
    )
    mock_domains = ["imo.es", "barraquer.com", "topdoctors.es"]
    if use_cache:
        cpath.write_text(
            json.dumps(
                {"respuesta": mock_text, "dominios": mock_domains, "degradado": True},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return mock_text, mock_domains, True
