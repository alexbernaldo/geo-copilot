"""Conector Perplexity (API Sonar con búsqueda web nativa por defecto) con caché y degradación (F15)."""

import json
import os
import time
from urllib.request import Request, urlopen

from geo.config import LLM_PROVIDER
from geo.engines.openai_engine import _cache_path, extract_domain


def run(
    prompt: str,
    *,
    model: str = "sonar",
    repeticion: int = 1,
    use_cache: bool = True,
    allow_mock_fallback: bool = True,
) -> tuple[str, list[str], bool]:
    """Ejecuta un prompt en Perplexity Sonar API (busca en la web por defecto).

    Extrae las fuentes de `citations` y `search_results` y devuelve `(respuesta, dominios, degradado)`.
    """
    cpath = _cache_path("perplexity", model, prompt, repeticion)
    if use_cache and cpath.exists():
        data = json.loads(cpath.read_text(encoding="utf-8"))
        return str(data["respuesta"]), list(data["dominios"]), bool(data.get("degradado", False))

    api_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().lower()

    if provider != "mock" and api_key:
        for attempt in range(3):
            try:
                url = "https://api.perplexity.ai/chat/completions"
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                }
                req = Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urlopen(req, timeout=30) as resp:  # noqa: S310
                    raw = json.loads(resp.read().decode("utf-8"))

                choices = raw.get("choices", [])
                text_out = ""
                if choices:
                    text_out = str(choices[0].get("message", {}).get("content", "")).strip()

                domains: list[str] = []
                for cit in raw.get("citations", []) or []:
                    dom = extract_domain(str(cit))
                    if dom and dom not in domains:
                        domains.append(dom)
                for sr in raw.get("search_results", []) or []:
                    if isinstance(sr, dict) and sr.get("url"):
                        dom = extract_domain(str(sr["url"]))
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
        raise RuntimeError("Perplexity Sonar API no disponible y fallback desactivado.")

    mock_text = (
        f"[Simulación conector Perplexity Sonar · rep={repeticion}] "
        f"Ante la consulta «{prompt}», los resultados indexados destacan a Clínica Baviera, "
        f"IMO Grupo Miranza y Centro de Oftalmología Barraquer en cirugía refractiva y cataratas."
    )
    mock_domains = ["clinicabaviera.com", "imo.es", "cuidateplus.marca.com", "ocu.org"]
    if use_cache:
        cpath.write_text(
            json.dumps(
                {"respuesta": mock_text, "dominios": mock_domains, "degradado": True},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return mock_text, mock_domains, True
