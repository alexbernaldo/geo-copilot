"""Motor conversacional del estudio en vivo vía OpenRouter (ChatGPT, Gemini, Claude y Perplexity) con búsqueda web."""

from __future__ import annotations

import hashlib
import json
import re
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

from geo import openrouter as _openrouter
from geo import settings as _settings
from geo.config import CACHE_DIR
from geo.engines.openai_engine import extract_domain

ENGINE_SETTING_KEYS: dict[str, str] = {
    "ChatGPT": "ENGINE_MODEL_CHATGPT",
    "Gemini": "ENGINE_MODEL_GEMINI",
    "Claude": "ENGINE_MODEL_CLAUDE",
    "Perplexity": "ENGINE_MODEL_PERPLEXITY",
}
DEFAULT_ENGINE_MODELS: dict[str, str] = {
    "ChatGPT": "openai/gpt-4o-mini",
    "Gemini": "google/gemini-2.5-flash",
    "Claude": "anthropic/claude-haiku-4.5",
    "Perplexity": "perplexity/sonar",
}
ENGINE_TEMPERATURE = 0.7
ENGINE_MAX_TOKENS = 1500

_URL_RE = re.compile(r"https?://[^\s)\]>\"']+")


@dataclass
class EngineResult:
    """Resultado de una consulta a un motor."""

    motor: str
    model: str
    texto: str
    urls: list[str] = field(default_factory=list)
    dominios: list[str] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float | None = None
    cached: bool = False
    simulado: bool = False


def engine_model(motor: str) -> str:
    """Modelo de OpenRouter configurado para el motor (Ajustes → ENGINE_MODEL_*)."""
    if motor not in ENGINE_SETTING_KEYS:
        raise ValueError(f"Motor no soportado: {motor}")
    return _settings.get(ENGINE_SETTING_KEYS[motor]).strip() or DEFAULT_ENGINE_MODELS[motor]


def _cache_file(model: str, repeticion: int, prompt: str, cache_dir: Path | None) -> Path:
    base = Path(cache_dir) if cache_dir is not None else CACHE_DIR / "engines"
    base.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(f"openrouter|{model}|{repeticion}|{prompt}".encode("utf-8")).hexdigest()[:32]
    return base / f"or_{digest}.json"


def _domains_from(urls: Sequence[str]) -> list[str]:
    out: list[str] = []
    for u in urls:
        d = extract_domain(u)
        if d and d not in out:
            out.append(d)
    return out


def mock_run(motor: str, prompt: str, repeticion: int, marcas: Sequence[str] | None = None) -> EngineResult:
    """Respuesta simulada determinista (proveedor mock): sin red ni claves."""
    seed = zlib.crc32(f"{motor}|{repeticion}|{prompt}".encode("utf-8"))
    nombres = list(marcas or [])
    if nombres:
        k = (seed % len(nombres))
        orden = nombres[k:] + nombres[:k]
    else:
        orden = []
    if orden:
        lista = "; ".join(f"{i + 1}. {n}" for i, n in enumerate(orden[:5]))
        texto = f"[Respuesta simulada de {motor}, repetición {repeticion}] Opciones a considerar: {lista}."
    else:
        texto = f"[Respuesta simulada de {motor}, repetición {repeticion}] No hay datos suficientes."
    urls = [f"https://fuente-simulada-{(seed % 5) + 1}.example/articulo"]
    return EngineResult(
        motor=motor,
        model="mock",
        texto=texto,
        urls=urls,
        dominios=_domains_from(urls),
        tokens_in=max(1, len(prompt) // 4),
        tokens_out=max(1, len(texto) // 4),
        cost_usd=0.0,
        simulado=True,
    )


def run(
    motor: str,
    prompt: str,
    repeticion: int = 1,
    *,
    model: str | None = None,
    use_cache: bool = True,
    cache_dir: Path | None = None,
    retries: int = 2,
    api_key: str | None = None,
) -> EngineResult:
    """Consulta `prompt` al motor con búsqueda web activa y devuelve texto, URLs citadas, dominios y coste.

    Caché en disco por (modelo, repetición, prompt). Los fallos no se cachean y se propagan como
    `geo.openrouter.OpenRouterError` (el llamador decide si reintenta o excluye la llamada).
    """
    chosen = model or engine_model(motor)
    cpath = _cache_file(chosen, repeticion, prompt, cache_dir)
    if use_cache and cpath.exists():
        try:
            data = json.loads(cpath.read_text(encoding="utf-8"))
            res = EngineResult(**data)
            res.cached = True
            return res
        except Exception:
            pass

    res_chat = _openrouter.chat(
        [{"role": "user", "content": prompt}],
        model=chosen,
        temperature=ENGINE_TEMPERATURE,
        json_mode=False,
        web_search=True,
        max_tokens=ENGINE_MAX_TOKENS,
        api_key=api_key,
        retries=retries,
    )
    urls = list(res_chat.citations)
    for u in _URL_RE.findall(res_chat.text or ""):
        u = u.rstrip(".,;")
        if u not in urls:
            urls.append(u)
    result = EngineResult(
        motor=motor,
        model=res_chat.model or chosen,
        texto=res_chat.text,
        urls=urls,
        dominios=_domains_from(urls),
        tokens_in=res_chat.tokens_in,
        tokens_out=res_chat.tokens_out,
        cost_usd=res_chat.cost_usd,
    )
    if use_cache:
        payload = asdict(result)
        payload["cached"] = False
        cpath.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return result
