"""Interfaz común de motores de búsqueda conversacional (ChatGPT, Gemini, Perplexity, Claude) y mini-estudio real (F15)."""

from typing import Any, Sequence
import pandas as pd

from geo.config import MAX_BUDGET_EUR
from geo.engines import claude_engine, gemini_engine, openai_engine, perplexity_engine
from geo.engines.openai_engine import extract_domain

# 6 prompts P1 espontáneos sobre una categoría pública real (nunca se mezclan con el dataset sintético del kit)
DEFAULT_MINI_STUDY_PROMPTS: list[dict[str, Any]] = [
    {
        "prompt_id": "LIVE-P01",
        "familia": "descubrimiento_generico",
        "intencion": "Descubrimiento",
        "instanciacion": "generico",
        "prompt_ejecutado": "¿Cuáles son las clínicas oftalmológicas más recomendadas en España para cirugía refractiva láser?",
        "ciudad": None,
        "espontanea": True,
    },
    {
        "prompt_id": "LIVE-P02",
        "familia": "descubrimiento_ciudad",
        "intencion": "Descubrimiento",
        "instanciacion": "ciudad",
        "prompt_ejecutado": "¿Qué clínicas de oftalmología destacan en Madrid para operarse de miopía y astigmatismo?",
        "ciudad": "Madrid",
        "espontanea": True,
    },
    {
        "prompt_id": "LIVE-P03",
        "familia": "descubrimiento_ciudad",
        "intencion": "Descubrimiento",
        "instanciacion": "ciudad",
        "prompt_ejecutado": "¿Cuáles son los mejores centros oftalmológicos en Barcelona para cirugía de cataratas?",
        "ciudad": "Barcelona",
        "espontanea": True,
    },
    {
        "prompt_id": "LIVE-P04",
        "familia": "comparacion_generica",
        "intencion": "Consideración",
        "instanciacion": "generico",
        "prompt_ejecutado": "¿Qué diferencias hay entre las principales clínicas oftalmológicas de España en tecnología láser y lentes intraoculares?",
        "ciudad": None,
        "espontanea": True,
    },
    {
        "prompt_id": "LIVE-P05",
        "familia": "decision_generica",
        "intencion": "Decisión",
        "instanciacion": "generico",
        "prompt_ejecutado": "¿Qué clínica oftalmológica elegirías en España por relación calidad-precio y seguimiento postoperatorio?",
        "ciudad": None,
        "espontanea": True,
    },
    {
        "prompt_id": "LIVE-P06",
        "familia": "validacion_generica",
        "intencion": "Validación",
        "instanciacion": "generico",
        "prompt_ejecutado": "¿Qué opiniones médicas y garantías ofrecen los grandes institutos oftalmológicos en España?",
        "ciudad": None,
        "espontanea": True,
    },
]


def estimate_mini_study_cost(
    n_prompts: int = 6,
    n_motors: int = 2,
    repeticiones: int = 2,
    *,
    tokens_in_per_call: int = 160,
    tokens_out_per_call: int = 700,
    web_search_fee_eur_per_call: float = 0.006,
    token_cost_eur_per_1k: float = 0.002,
) -> dict[str, Any]:
    """Estima el coste de un mini-estudio en vivo según la fórmula de `05_Guia_de_APIs_y_costes.md`."""
    total_calls = int(n_prompts) * int(n_motors) * int(repeticiones)
    token_cost_per_call = ((tokens_in_per_call + tokens_out_per_call) / 1000.0) * token_cost_eur_per_1k
    cost_per_call = token_cost_per_call + web_search_fee_eur_per_call
    total_cost_eur = round(total_calls * cost_per_call, 4)
    return {
        "n_prompts": n_prompts,
        "n_motors": n_motors,
        "repeticiones": repeticiones,
        "total_calls": total_calls,
        "estimated_cost_eur": total_cost_eur,
        "within_budget": total_cost_eur <= MAX_BUDGET_EUR,
        "max_budget_eur": MAX_BUDGET_EUR,
    }


def run_engine(
    motor: str,
    prompt: str,
    *,
    repeticion: int = 1,
    use_cache: bool = True,
    allow_mock_fallback: bool = True,
) -> tuple[str, list[str], bool]:
    """Interfaz unificada: ejecuta `prompt` en el motor indicado y devuelve `(respuesta, dominios, degradado)`."""
    m = motor.strip().lower()
    if m in ("chatgpt", "openai"):
        return openai_engine.run(
            prompt,
            repeticion=repeticion,
            use_cache=use_cache,
            allow_mock_fallback=allow_mock_fallback,
        )
    if m in ("gemini", "google"):
        return gemini_engine.run(
            prompt,
            repeticion=repeticion,
            use_cache=use_cache,
            allow_mock_fallback=allow_mock_fallback,
        )
    if m in ("perplexity", "sonar"):
        return perplexity_engine.run(
            prompt,
            repeticion=repeticion,
            use_cache=use_cache,
            allow_mock_fallback=allow_mock_fallback,
        )
    if m in ("claude", "anthropic"):
        return claude_engine.run(
            prompt,
            repeticion=repeticion,
            use_cache=use_cache,
            allow_mock_fallback=allow_mock_fallback,
        )
    raise ValueError(f"Motor no soportado: {motor}")


def run_mini_study(
    prompts: Sequence[dict[str, Any]] | None = None,
    motores: Sequence[str] = ("ChatGPT", "Perplexity"),
    repeticiones: int = 2,
    *,
    use_cache: bool = True,
    max_budget_eur: float = MAX_BUDGET_EUR,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Ejecuta el mini-estudio demostrativo (por defecto 6 prompts P1 × 2 motores × 2 repeticiones = 24 llamadas).

    Devuelve `(df_ejecuciones, metadata)` con el mismo esquema de columnas que `load_ejecuciones()`,
    pero etiquetado como estudio de conectores sobre marcas reales públicas para no mezclarse nunca
    con el dataset sintético del kit.
    """
    prompt_list = list(prompts) if prompts is not None else DEFAULT_MINI_STUDY_PROMPTS
    est = estimate_mini_study_cost(
        n_prompts=len(prompt_list),
        n_motors=len(motores),
        repeticiones=repeticiones,
    )
    budget_exceeded = est["estimated_cost_eur"] > max_budget_eur

    rows: list[dict[str, Any]] = []
    any_degraded = budget_exceeded
    idx = 1

    for p_item in prompt_list:
        for motor in motores:
            for rep in range(1, repeticiones + 1):
                if budget_exceeded:
                    # Si supera el tope, degradar directamente a simulación local sin llamada de red
                    resp_text, doms, deg = run_engine(
                        motor,
                        str(p_item["prompt_ejecutado"]),
                        repeticion=rep,
                        use_cache=use_cache,
                        allow_mock_fallback=True,
                    )
                    any_degraded = True
                else:
                    resp_text, doms, deg = run_engine(
                        motor,
                        str(p_item["prompt_ejecutado"]),
                        repeticion=rep,
                        use_cache=use_cache,
                        allow_mock_fallback=True,
                    )
                    if deg:
                        any_degraded = True

                rows.append(
                    {
                        "ejecucion_id": f"LIVE-{idx:04d}",
                        "prompt_id": str(p_item["prompt_id"]),
                        "familia": str(p_item.get("familia", "descubrimiento_generico")),
                        "intencion": str(p_item.get("intencion", "Descubrimiento")),
                        "instanciacion": str(p_item.get("instanciacion", "generico")),
                        "prompt_ejecutado": str(p_item["prompt_ejecutado"]),
                        "motor": str(motor),
                        "repeticion": int(rep),
                        "respuesta": resp_text,
                        "fuentes": list(doms),
                        "ciudad": p_item.get("ciudad"),
                        "espontanea": bool(p_item.get("espontanea", True)),
                    }
                )
                idx += 1

    df_out = pd.DataFrame(rows)
    meta = {
        **est,
        "degradado": any_degraded,
        "budget_exceeded": budget_exceeded,
        "aislado_del_kit": True,
    }
    return df_out, meta


__all__ = [
    "DEFAULT_MINI_STUDY_PROMPTS",
    "estimate_mini_study_cost",
    "extract_domain",
    "run_engine",
    "run_mini_study",
]
