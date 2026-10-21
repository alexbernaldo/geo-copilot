"""Cliente LLM con complete_json(), caché en disco, tope de llamadas y estimación de coste."""

from collections.abc import Callable
import hashlib
import json
import os
import re
from typing import Any, TypeVar
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

import threading

from geo.config import (
    ANTHROPIC_API_KEY,
    CACHE_DIR,
    LLM_MODEL,
    LLM_PROVIDER,
    MAX_LLM_CALLS,
    OPENAI_API_KEY,
)
from geo import settings as _settings
from geo import openrouter as _openrouter

T = TypeVar("T", bound=BaseModel)

# Precios orientativos por millón de tokens (USD/EUR aprox. para modelos rápidos tipo Haiku / GPT-4o-mini)
DEFAULT_PRICE_IN_PER_M: float = 0.25
DEFAULT_PRICE_OUT_PER_M: float = 1.25


class LLMConfigError(RuntimeError):
    """Error no recuperable de configuración o del proveedor (clave, saldo, modelo)."""


class LLMCallLimitError(RuntimeError):
    """Se lanza cuando se supera el tope duro MAX_LLM_CALLS."""


class LLMProviderError(RuntimeError):
    """Se lanza cuando falla la llamada al proveedor LLM o no hay credenciales."""


class _LLMTracker:
    """Registro global en memoria de llamadas, tokens y aciertos de caché."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        self.calls: int = 0
        self.cache_hits: int = 0
        self.tokens_in: int = 0
        self.tokens_out: int = 0
        self.records: list[dict[str, Any]] = []
        self.cost_eur: float = 0.0
        self.cost_is_real: bool = False


_TRACKER = _LLMTracker()


def get_llm_stats() -> dict[str, Any]:
    """Devuelve estadísticas acumuladas de uso del cliente LLM en el proceso actual."""
    with _TRACKER.lock:
        calls = _TRACKER.calls
        cache_hits = _TRACKER.cache_hits
        tokens_in = _TRACKER.tokens_in
        tokens_out = _TRACKER.tokens_out
        records = list(_TRACKER.records)
        cost_eur = _TRACKER.cost_eur
        cost_is_real = _TRACKER.cost_is_real
    if cost_eur > 0:
        estimated = cost_eur
    else:
        estimated = estimate_cost(calls, tokens_in, tokens_out)
    return {
        "calls": calls,
        "cache_hits": cache_hits,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "estimated_cost_eur": round(estimated, 6),
        "cost_is_real": cost_is_real,
        "records": records,
    }


def reset_llm_stats() -> None:
    """Reinicia los contadores globales de llamadas y tokens."""
    _TRACKER.reset()


def estimate_cost(
    n_calls: int,
    tok_in: int,
    tok_out: int,
    price_in: float = DEFAULT_PRICE_IN_PER_M,
    price_out: float = DEFAULT_PRICE_OUT_PER_M,
) -> float:
    """Estima el coste total para un volumen total de tokens de entrada y salida (o por llamada si n_calls>0 y tok son medios).

    Si tok_in y tok_out ya representan el total acumulado (o bien si se pasa n_calls=1), calcula:
    (tok_in * price_in + tok_out * price_out) / 1_000_000.
    """
    if n_calls <= 0:
        return 0.0
    return (tok_in * price_in + tok_out * price_out) / 1_000_000.0


def resolve_model(provider: str, prompt_version: str, model: str | None = None) -> str:
    if model:
        return model
    if (provider or "").strip().lower() == "mock":
        return "mock"
    pv = (prompt_version or "").lower()
    if pv.startswith("strategy") or pv.startswith("writer"):
        w = _settings.get("LLM_MODEL_WRITER").strip()
        if w:
            return w
    m = _settings.get("LLM_MODEL").strip()
    return m or "mock"


def estimate_cost_for_model(model: str, tok_in: int, tok_out: int) -> float:
    price = _openrouter.model_price(model)
    if price is None:
        try:
            price = (_settings.get_float("USD_EUR") and None) or None
        except Exception:
            price = None
    if price is None:
        pin = DEFAULT_PRICE_IN_PER_M / 1_000_000.0
        pout = DEFAULT_PRICE_OUT_PER_M / 1_000_000.0
    else:
        pin, pout = price
    usd = (tok_in * pin + tok_out * pout)
    eur_rate = _settings.get_float("USD_EUR")
    return usd * eur_rate




def _compute_cache_key(
    provider: str,
    model: str,
    prompt_version: str,
    system: str,
    user: str,
    explicit_key: str | None = None,
) -> str:
    """Calcula el hash SHA-256 para la caché en disco: cache/<sha256>.json."""
    if explicit_key:
        raw = f"{provider}|{model}|{prompt_version}|{explicit_key}"
    else:
        raw = f"{provider}|{model}|{prompt_version}|{system}|{user}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _extract_json_str(raw_text: str) -> str:
    """Extrae el bloque JSON de una respuesta de texto del LLM."""
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return text[start : end + 1]
    return text


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(LLMProviderError),
)
def _call_provider_raw(
    provider: str,
    model: str,
    system: str,
    user: str,
    temperature: float,
) -> tuple[str, int, int, float | None]:
    """Realiza una llamada al proveedor con reintentos tenacity. Devuelve (texto, tok_in, tok_out, coste_usd)."""
    active_provider = (provider or "").strip().lower()

    if active_provider == "openrouter":
        try:
            res = _openrouter.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                model=model,
                temperature=temperature,
                json_mode=True,
                retries=2,
            )
            return res.text, res.tokens_in, res.tokens_out, res.cost_usd
        except _openrouter.OpenRouterError as exc:
            if not getattr(exc, "retryable", False):
                raise LLMConfigError(str(exc)) from exc
            raise LLMProviderError(str(exc)) from exc

    if active_provider == "anthropic":
        api_key = _settings.get("ANTHROPIC_API_KEY").strip() or os.getenv("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY).strip()
        if not api_key:
            raise LLMConfigError("Falta ANTHROPIC_API_KEY para usar LLM_PROVIDER=anthropic.")
        try:
            import anthropic  # type: ignore[import-not-found]

            client = anthropic.Anthropic(api_key=api_key)
            chosen_model = model or "claude-3-5-haiku-latest"
            resp = client.messages.create(
                model=chosen_model,
                max_tokens=4096,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text_out = "".join(
                block.text for block in resp.content if hasattr(block, "text")
            )
            tok_in = int(getattr(resp.usage, "input_tokens", len(system + user) // 4))
            tok_out = int(getattr(resp.usage, "output_tokens", len(text_out) // 4))
            return text_out, tok_in, tok_out, None
        except Exception as exc:
            raise LLMProviderError(f"Error en llamada Anthropic: {exc}") from exc

    if active_provider == "openai":
        api_key = _settings.get("OPENAI_API_KEY").strip() or os.getenv("OPENAI_API_KEY", OPENAI_API_KEY).strip()
        if not api_key:
            raise LLMConfigError("Falta OPENAI_API_KEY para usar LLM_PROVIDER=openai.")
        try:
            import openai  # type: ignore[import-not-found]

            client = openai.OpenAI(api_key=api_key)
            chosen_model = model or "gpt-4o-mini"
            resp = client.chat.completions.create(
                model=chosen_model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text_out = resp.choices[0].message.content or "{}"
            usage = resp.usage
            tok_in = int(usage.prompt_tokens if usage else len(system + user) // 4)
            tok_out = int(usage.completion_tokens if usage else len(text_out) // 4)
            return text_out, tok_in, tok_out, None
        except Exception as exc:
            raise LLMProviderError(f"Error en llamada OpenAI: {exc}") from exc

    raise LLMProviderError(f"Proveedor LLM desconocido: {provider}")


def complete_json(
    system: str,
    user: str,
    schema: type[T],
    *,
    model: str | None = None,
    temperature: float = 0.0,
    cache_key: str | None = None,
    prompt_version: str = "v1",
    mock_builder: Callable[[], T | dict[str, Any]] | None = None,
    provider: str | None = None,
    use_cache: bool = True,
) -> T:
    """Obtiene una respuesta estructurada validada con Pydantic, usando caché en disco y control de límites.

    - En modo `mock` (por defecto), construye una respuesta determinista mediante `mock_builder` o valores por defecto.
    - Si la respuesta ya está en `cache/<sha256>.json`, la devuelve sin consumir llamadas nuevas (`cache_hits += 1`).
    - Si el JSON devuelto por el proveedor no valida contra `schema`, reintenta una vez pasando el error de validación.
    """
    active_provider = (provider or _settings.get("LLM_PROVIDER") or LLM_PROVIDER or "mock").strip().lower()
    if model is None:
        active_model = resolve_model(active_provider, prompt_version, None)
    else:
        active_model = resolve_model(active_provider, prompt_version, model)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    digest = _compute_cache_key(
        provider=active_provider,
        model=active_model,
        prompt_version=prompt_version,
        system=system,
        user=user,
        explicit_key=cache_key,
    )
    cache_file = CACHE_DIR / f"{digest}.json"

    if use_cache and cache_file.exists():
        try:
            cached_payload = json.loads(cache_file.read_text(encoding="utf-8"))
            validated = schema.model_validate(cached_payload["data"])
            with _TRACKER.lock:
                _TRACKER.cache_hits += 1
            return validated
        except Exception:
            pass

    max_calls = int(_settings.get("MAX_LLM_CALLS") or MAX_LLM_CALLS)
    with _TRACKER.lock:
        cur_calls = _TRACKER.calls
        cur_cost = _TRACKER.cost_eur
    if cur_calls >= max_calls:
        raise LLMCallLimitError(
            f"Se alcanzó el tope máximo de llamadas LLM ({max_calls})."
        )
    if active_provider != "mock":
        try:
            budget = float(_settings.get("MAX_BUDGET_EUR") or 0)
        except ValueError:
            budget = 0.0
        if budget > 0 and cur_cost >= budget:
            raise LLMCallLimitError(f"Se alcanzó el tope de gasto de la ejecución ({budget} €).")

    if active_provider == "mock":
        if mock_builder is not None:
            built = mock_builder()
            validated = (
                built
                if isinstance(built, schema)
                else schema.model_validate(built)
            )
        else:
            validated = schema.model_validate({})

        tok_in = max(1, len(system + user) // 4)
        tok_out = max(1, len(validated.model_dump_json()) // 4)
        with _TRACKER.lock:
            _TRACKER.calls += 1
            _TRACKER.tokens_in += tok_in
            _TRACKER.tokens_out += tok_out
            _TRACKER.records.append(
            {
                "provider": "mock",
                "model": "mock",
                "prompt_version": prompt_version,
                "tokens_in": tok_in,
                "tokens_out": tok_out,
                "cache_file": cache_file.name,
            }
        )
        if use_cache:
            cache_file.write_text(
                json.dumps(
                    {
                        "provider": "mock",
                        "model": "mock",
                        "prompt_version": prompt_version,
                        "data": validated.model_dump(mode="json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        return validated

    # Proveedor real (anthropic / openai) con 1 reintento si falla la validación Pydantic
    schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    enriched_system = (
        f"{system}\n\n"
        "Devuelve EXCLUSIVAMENTE un objeto JSON válido que cumpla este JSON Schema:\n"
        f"{schema_hint}"
    )

    raw_text, tok_in, tok_out, cost_usd = _call_provider_raw(
        provider=active_provider,
        model=active_model,
        system=enriched_system,
        user=user,
        temperature=temperature,
    )
    with _TRACKER.lock:
        _TRACKER.calls += 1
        _TRACKER.tokens_in += tok_in
        _TRACKER.tokens_out += tok_out
        if cost_usd is not None:
            _TRACKER.cost_eur += cost_usd * _settings.get_float("USD_EUR")
            _TRACKER.cost_is_real = True
        else:
            _TRACKER.cost_eur += estimate_cost_for_model(active_model, tok_in, tok_out)
        _TRACKER.records.append(
            {
                "provider": active_provider,
                "model": active_model,
                "prompt_version": prompt_version,
                "tokens_in": tok_in,
                "tokens_out": tok_out,
                "cache_file": cache_file.name,
            }
        )

    try:
        parsed = json.loads(_extract_json_str(raw_text))
        validated = schema.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as err:
        if _TRACKER.calls >= max_calls:
            raise LLMCallLimitError(
                f"Se alcanzó el tope máximo de llamadas LLM ({max_calls}) durante reintento."
            ) from err
        retry_user = (
            f"{user}\n\n"
            f"Tu respuesta anterior falló la validación JSON/Pydantic con este error:\n{err}\n"
            "Corrige y devuelve únicamente el JSON válido."
        )
        raw_text2, tok_in2, tok_out2, cost_usd2 = _call_provider_raw(
            provider=active_provider,
            model=active_model,
            system=enriched_system,
            user=retry_user,
            temperature=temperature,
        )
        with _TRACKER.lock:
            _TRACKER.calls += 1
            _TRACKER.tokens_in += tok_in2
            _TRACKER.tokens_out += tok_out2
            if cost_usd2 is not None:
                _TRACKER.cost_eur += cost_usd2 * _settings.get_float("USD_EUR")
                _TRACKER.cost_is_real = True
            else:
                _TRACKER.cost_eur += estimate_cost_for_model(active_model, tok_in2, tok_out2)
        tok_in += tok_in2
        tok_out += tok_out2
        parsed2 = json.loads(_extract_json_str(raw_text2))
        validated = schema.model_validate(parsed2)

    _TRACKER.records.append(
        {
            "provider": active_provider,
            "model": active_model,
            "prompt_version": prompt_version,
            "tokens_in": tok_in,
            "tokens_out": tok_out,
            "cache_file": cache_file.name,
        }
    )
    if use_cache:
        cache_file.write_text(
            json.dumps(
                {
                    "provider": active_provider,
                    "model": active_model,
                    "prompt_version": prompt_version,
                    "data": validated.model_dump(mode="json"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return validated
