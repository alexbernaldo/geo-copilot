"""Conector ChatGPT (OpenAI Responses API + herramienta web_search) con caché y degradación (F15)."""

import hashlib
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

from geo.config import CACHE_DIR, LLM_PROVIDER

ENGINE_CACHE_DIR = CACHE_DIR / "engines"


def extract_domain(url: str) -> str:
    """Extrae el dominio limpio (sin www.) a partir de una URL o cadena de dominio."""
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = (parsed.netloc or parsed.path).lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host.split("/")[0].split(":")[0]


def _cache_path(engine_name: str, model: str, prompt: str, repeticion: int) -> Any:
    ENGINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{engine_name}|{model}|{repeticion}|{prompt}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return ENGINE_CACHE_DIR / f"{engine_name}_{digest}.json"


def run(
    prompt: str,
    *,
    model: str = "gpt-4o-mini",
    repeticion: int = 1,
    use_cache: bool = True,
    allow_mock_fallback: bool = True,
) -> tuple[str, list[str], bool]:
    """Ejecuta un prompt en OpenAI Responses API con `web_search` activo.

    Devuelve `(respuesta, dominios_citados, degradado)`.
    Si falta `OPENAI_API_KEY`, `LLM_PROVIDER=mock` o la API falla, degrada limpiamente (`degradado=True`).
    """
    cpath = _cache_path("openai", model, prompt, repeticion)
    if use_cache and cpath.exists():
        data = json.loads(cpath.read_text(encoding="utf-8"))
        return str(data["respuesta"]), list(data["dominios"]), bool(data.get("degradado", False))

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().lower()

    if provider != "mock" and api_key:
        for attempt in range(3):
            try:
                from openai import OpenAI  # type: ignore[import-not-found]

                client = OpenAI(api_key=api_key)
                resp = client.responses.create(
                    model=model,
                    input=prompt,
                    tools=[{"type": "web_search_preview"}],
                )
                text_out = getattr(resp, "output_text", "") or ""
                domains: list[str] = []
                for item in getattr(resp, "output", []) or []:
                    for content in getattr(item, "content", []) or []:
                        if not text_out and getattr(content, "text", None):
                            text_out += str(content.text)
                        for ann in getattr(content, "annotations", []) or []:
                            url = getattr(ann, "url", None) or (
                                ann.get("url") if isinstance(ann, dict) else None
                            )
                            if url:
                                dom = extract_domain(str(url))
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
        raise RuntimeError("OpenAI Responses API no disponible y fallback desactivado.")

    mock_text = (
        f"[Simulación conector OpenAI Responses API + web_search · rep={repeticion}] "
        f"Para la consulta «{prompt}», entre los centros oftalmológicos públicos de referencia en España "
        f"destacan Instituto Oftalmológico Fernández-ega, IMO Grupo Miranza y Clínica Baviera, "
        f"según publicaciones de sociedades científicas y portales sanitarios."
    )
    mock_domains = ["oftalmologia.org.es", "cuidateplus.marca.com", "clinicabaviera.com"]
    if use_cache:
        cpath.write_text(
            json.dumps(
                {"respuesta": mock_text, "dominios": mock_domains, "degradado": True},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return mock_text, mock_domains, True
