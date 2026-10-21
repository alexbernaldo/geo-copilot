"""Página de ajustes: conexión OpenRouter, modelos y límites."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.ui_shared import page_header, panel, section, chip, kpi_strip, render_empty
from geo import settings
from geo import openrouter
from geo.orchestrator import estimate_pipeline, Run

st.set_page_config(page_title="Ajustes", layout="wide")
page_header("Ajustes", "Conexión con OpenRouter, modelos y límites de gasto.")


def _load_models():
    try:
        return openrouter.list_models()
    except Exception as exc:
        st.warning(f"No se pudo cargar el catálogo: {exc}")
        return []


# Panel 1: Conexión
with panel("Conexión"):
    section("Motor de IA por defecto")
    provider_choice = st.radio(
        "Motor de IA por defecto",
        ["Simulado (sin red ni coste)", "OpenRouter (IA real)"],
        horizontal=True,
        key="provider_choice",
    )
    has_key = settings.has_openrouter_key()
    if provider_choice.startswith("OpenRouter") and not has_key:
        st.caption("Configura una clave para habilitar OpenRouter.")

    current_key = settings.get("OPENROUTER_API_KEY")
    if current_key:
        st.caption(f"Clave guardada: {settings.mask(current_key)}")

    new_key = st.text_input("Clave de OpenRouter (vacío = conservar la actual)", type="password")
    st.caption("Crea una en https://openrouter.ai/keys")

    if st.button("Probar conexión"):
        api_key = new_key.strip() or current_key.strip() or None
        model = settings.get("LLM_MODEL")
        try:
            with st.spinner("Probando conexión..."):
                info = openrouter.test_connection(model, api_key=api_key)
            st.success(
                f"Clave: {info['key'].get('label')} · gasto {info['key'].get('usage')} / límite {info['key'].get('limit')} · "
                f"modelo {info['model']} · {info['latency_s']} s · coste {info['cost_usd']}"
            )
        except Exception as exc:
            st.error(str(exc))

# Panel 2: Modelos
with panel("Modelos"):
    models = _load_models()
    if models:
        ids = [m["id"] for m in models]
        def fmt(mid):
            for m in models:
                if m["id"] == mid:
                    return f"{m['name']} · {m['id']} · ${m['price_in_per_m']:.2f} / ${m['price_out_per_m']:.2f} por M"
            return mid

        current_judge = settings.get("LLM_MODEL")
        if current_judge not in ids:
            st.warning(f"El modelo {current_judge} no existe en OpenRouter")
        judge_model = st.selectbox("Juez, intake y revisor", ids, index=ids.index(current_judge) if current_judge in ids else 0, format_func=fmt)

        current_writer = settings.get("LLM_MODEL_WRITER")
        if current_writer not in ids:
            st.warning(f"El modelo {current_writer} no existe en OpenRouter")
        writer_model = st.selectbox("Estrategia y redacción", ids, index=ids.index(current_writer) if current_writer in ids else 0, format_func=fmt)
    else:
        judge_model = st.text_input("Juez, intake y revisor", value=settings.get("LLM_MODEL"))
        writer_model = st.text_input("Estrategia y redacción", value=settings.get("LLM_MODEL_WRITER"))

    # estimación
    try:
        est = estimate_pipeline("openrouter", {"juez_y_revisor": judge_model, "estrategia_y_redaccion": writer_model})
        kpi_strip([
            {"label": "Llamadas", "value": est.get("total_llamadas", 0)},
            {"label": "Coste estimado (€)", "value": round(est.get("total_eur", 0.0), 4)},
            {"label": "Minutos", "value": est.get("minutos", 0)},
        ])
    except Exception as exc:
        st.caption(f"Estimación no disponible: {exc}")

    with st.expander("Motores del estudio en vivo"):
        for k in ["ENGINE_MODEL_CHATGPT", "ENGINE_MODEL_GEMINI", "ENGINE_MODEL_CLAUDE", "ENGINE_MODEL_PERPLEXITY"]:
            st.text_input(k, value=settings.get(k), key=k)

# Panel 3: Límites
with panel("Límites"):
    conc = st.slider("Concurrencia del juez", 1, 16, int(settings.get("LLM_CONCURRENCY") or 8))
    max_calls = st.number_input("Tope de llamadas por análisis", value=int(settings.get("MAX_LLM_CALLS") or 1500), min_value=1)
    max_budget = st.number_input("Tope de gasto (€) por análisis", value=float(settings.get("MAX_BUDGET_EUR") or 5.0), min_value=0.0)
    usd_eur = st.number_input("USD→EUR", value=float(settings.get("USD_EUR") or 0.92), min_value=0.0)

if st.button("Guardar ajustes", type="primary"):
    values = {
        "LLM_PROVIDER": "openrouter" if provider_choice.startswith("OpenRouter") else "mock",
        "LLM_MODEL": judge_model,
        "LLM_MODEL_WRITER": writer_model,
        "LLM_CONCURRENCY": str(conc),
        "MAX_LLM_CALLS": str(int(max_calls)),
        "MAX_BUDGET_EUR": str(max_budget),
        "USD_EUR": str(usd_eur),
    }
    if new_key.strip():
        values["OPENROUTER_API_KEY"] = new_key.strip()
    for k in ["ENGINE_MODEL_CHATGPT", "ENGINE_MODEL_GEMINI", "ENGINE_MODEL_CLAUDE", "ENGINE_MODEL_PERPLEXITY"]:
        values[k] = st.session_state.get(k, settings.get(k))
    settings.save(values)
    st.toast("Ajustes guardados")
    st.rerun()
