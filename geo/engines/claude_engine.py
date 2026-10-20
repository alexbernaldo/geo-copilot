"""Conector Claude (Anthropic Messages API + herramienta de servidor web_search) con caché y degradación (F15)."""

import json
import os
import time

from geo.config import LLM_PROVIDER
from geo.engines.openai_engine import _cache_path, extract_domain


def run(
    prompt: str,
    *,
    model: str = "claude-3-5-haiku-latest",
    repeticion: int = 1,
    use_cache: bool = True,
    allow_mock_fallback: bool = True,
) -> tuple[str, list[str], bool]:
    """Ejecuta un prompt en Anthropic Messages API con herramienta `web_search` (máx. 3 usos).

    Gestiona paradas intermedias (`pause_turn`) y extrae dominios de `web_search_tool_result`.
    """
    cpath = _cache_path("claude", model, prompt, repeticion)
    if use_cache and cpath.exists():
        data = json.loads(cpath.read_text(encoding="utf-8"))
        return str(data["respuesta"]), list(data["dominios"]), bool(data.get("degradado", False))

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().lower()

    if provider != "mock" and api_key:
        for attempt in range(3):
            try:
                from anthropic import Anthropic  # type: ignore[import-not-found]

                client = Anthropic(api_key=api_key)
                messages = [{"role": "user", "content": prompt}]
                text_parts: list[str] = []
                domains: list[str] = []

                for _step in range(3):
                    resp = client.messages.create(
                        model=model,
                        max_tokens=900,
                        messages=messages,
                        tools=[
                            {
                                "type": "web_search_20250305",
                                "name": "web_search",
                                "max_uses": 3,
                            }
                        ],
                    )
                    for block in getattr(resp, "content", []) or []:
                        btype = getattr(block, "type", "")
                        if btype == "text" and getattr(block, "text", None):
                            text_parts.append(str(block.text))
                        elif btype == "web_search_tool_result":
                            for item in getattr(block, "content", []) or []:
                                u = getattr(item, "url", None) or (
                                    item.get("url") if isinstance(item, dict) else None
                                )
                                if u:
                                    dom = extract_domain(str(u))
                                    if dom and dom not in domains:
                                        domains.append(dom)

                    if getattr(resp, "stop_reason", "") == "pause_turn":
                        messages.append({"role": "assistant", "content": resp.content})
                        continue
                    break

                text_out = "\n".join(text_parts).strip()
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
        raise RuntimeError("Anthropic Messages API con web_search no disponible y fallback desactivado.")

    mock_text = (
        f"[Simulación conector Claude Messages API + web_search · rep={repeticion}] "
        f"Respecto a «{prompt}», centros oftalmológicos como Centro de Oftalmología Barraquer, "
        f"IMO Grupo Miranza y Clínica Baviera cuentan con amplia trayectoria quirúrgica y publicaciones clínicas."
    )
    mock_domains = ["barraquer.com", "oftalmologia.org.es", "doctoralia.es"]
    if use_cache:
        cpath.write_text(
            json.dumps(
                {"respuesta": mock_text, "dominios": mock_domains, "degradado": True},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return mock_text, mock_domains, True
