"""Página de nuevo análisis."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.ui_shared import page_header, panel, section, kpi_strip, chip
from app.ui_jobs import render_progress, STEP_LABELS
from geo import settings, jobs
from geo.config import RUNS_DIR, MARCAS_CSV
from geo.orchestrator import estimate_pipeline
import pandas as pd

page_header("Nuevo análisis", "Lanza un análisis con IA real o simulada.")

# If a run is running, show progress
running = jobs.any_running()
if running is not None:
    st.info("Hay un análisis en curso.")
    render_progress(running)
    st.stop()

# Prefill
prefill = st.session_state.get("nuevo_prefill")

with st.form("nuevo_analisis"):
    col1, col2 = st.columns(2)
    with col1:
        section("Qué analizar")
        modo = st.segmented_control("Tipo de análisis", ["Cliente (con brief)", "Prospecto (sin brief)"], default="Cliente (con brief)")
        is_cliente = modo.startswith("Cliente")
        if is_cliente:
            brief_opt = st.radio("Brief", ["Usar el brief de ejemplo (Clínica Alborada Visión)", "Subir archivo (.md, .docx, .txt)", "Pegar texto"])
            brief_path = None
            if brief_opt.startswith("Subir"):
                up = st.file_uploader("Archivo", type=["md", "docx", "txt"])
                if up is not None:
                    tmp = RUNS_DIR / "uploads"
                    tmp.mkdir(parents=True, exist_ok=True)
                    p = tmp / up.name
                    p.write_bytes(up.getvalue())
                    brief_path = str(p)
            elif brief_opt.startswith("Pegar"):
                txt = st.text_area("Pega el brief", height=200)
                if txt.strip():
                    tmp = RUNS_DIR / "uploads"
                    tmp.mkdir(parents=True, exist_ok=True)
                    p = tmp / "brief_original.md"
                    p.write_text(txt, encoding="utf-8")
                    brief_path = str(p)
            if brief_path is None and brief_opt.startswith("Usar"):
                from geo.config import BRIEF_MD
                brief_path = str(BRIEF_MD)
        else:
            try:
                marcas_df = pd.read_csv(MARCAS_CSV, encoding="utf-8-sig")
                opciones = [m for m in marcas_df["marca"].tolist() if m != "Alborada"]
            except Exception:
                opciones = []
            marca_sel = st.selectbox("Marca prospecto", opciones)
            brief_path = None
        st.caption("El estudio de citación es el del kit: 624 respuestas de ChatGPT, Gemini, Perplexity y Claude. La IA real se usa para interpretar el brief, evaluar cada respuesta, diseñar el plan, redactar y revisar.")
    with col2:
        section("Cómo ejecutarlo")
        provider_opt = st.radio("Motor de IA", ["Simulado", "OpenRouter"], horizontal=True)
        if provider_opt == "OpenRouter" and not settings.has_openrouter_key():
            st.page_link("pages/8_Ajustes.py", label="Configura OpenRouter en Ajustes")
        models_active = (settings.get("LLM_MODEL"), settings.get("LLM_MODEL_WRITER"))
        st.caption(f"Modelos activos: {models_active[0]} / {models_active[1]}")
        est = None
        if provider_opt == "OpenRouter":
            try:
                est = estimate_pipeline("openrouter", {"juez_y_revisor": models_active[0], "estrategia_y_redaccion": models_active[1]})
                kpi_strip([
                    {"label": "Llamadas previstas", "value": est.get("total_llamadas", 0)},
                    {"label": "Coste estimado (€)", "value": round(est.get("total_eur", 0.0), 4)},
                    {"label": "Tiempo estimado (min)", "value": est.get("minutos", 0)},
                ])
            except Exception as exc:
                st.caption(str(exc))
            budget = float(settings.get("MAX_BUDGET_EUR") or 5.0)
            if est and est.get("total_eur", 0) > budget:
                st.warning("El coste supera el tope. Ajusta en Ajustes.")
            confirm = st.checkbox("He revisado el coste estimado")
        else:
            confirm = True
        submitted = st.form_submit_button("Lanzar análisis", type="primary")

    if submitted:
        if provider_opt == "OpenRouter" and not settings.has_openrouter_key():
            st.error("Falta la clave de OpenRouter.")
        elif provider_opt == "OpenRouter" and not confirm:
            st.error("Debes confirmar el coste estimado.")
        else:
            modo_val = "cliente" if is_cliente else "prospecto"
            provider_val = "openrouter" if provider_opt == "OpenRouter" else "mock"
            marca_prospecto = marca_sel if not is_cliente else None
            try:
                rid = jobs.start(
                    modo=modo_val,
                    provider=provider_val,
                    brief_path=brief_path,
                    marca_prospecto=marca_prospecto,
                )
                st.session_state["active_run_id"] = rid
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
