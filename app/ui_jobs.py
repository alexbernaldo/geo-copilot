"""Componentes de progreso de ejecución para la UI (agente E)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

from app.ui_shared import chip, panel, section, page_header, render_empty
from geo.config import RUNS_DIR
from geo import jobs

STEP_LABELS = {
    "intake": "Intake del brief",
    "market": "Contraste de mercado",
    "detect": "Detección de menciones",
    "judge": "Juez LLM",
    "metrics": "Métricas",
    "findings": "Hallazgos",
    "plan": "Plan estratégico",
    "review": "Revisión normativa",
    "write": "Redacción",
    "export": "Exportación",
}


def _status_chip(status: str) -> str:
    if status == "done":
        return "good"
    if status == "running":
        return "info"
    if status == "degraded":
        return "warn"
    if status == "error":
        return "bad"
    return ""


def guard_active_run() -> None:
    active = jobs.any_running()
    if active is not None and active != st.session_state.get("active_run_id"):
        # show progress for running run
        pass
    run_id = st.session_state.get("active_run_id", "demo")
    prog = RUNS_DIR / str(run_id) / "progress.json"
    # if run in progress, block analysis pages
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        get_script_run_ctx = None
    # Determine if current page is an analysis page
    page = st.session_state.get("_current_page", "")
    # Simple: if progress running, render progress and stop on analysis pages
    if prog.exists():
        try:
            d = json.loads(prog.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        if d.get("status") == "running":
            # block heavy pages by checking query params? We'll rely on caller.
            pass
    return None


@st.fragment(run_every=1)
def _progress_fragment(run_id: str) -> None:
    prog = jobs.read_progress(run_id)
    if not prog:
        st.warning("Sin progreso.")
        return
    status = prog.get("status", "running")
    st.markdown(f"**{run_id}** · {prog.get('provider')} · {prog.get('elapsed_s', 0)} s · {prog.get('llm_calls', 0)} llamadas · {prog.get('cost_eur', 0)} €")
    # steps
    steps = prog.get("steps", {})
    for key, label in STEP_LABELS.items():
        s = (steps.get(key) or {}).get("status", "pending")
        dur = (steps.get(key) or {}).get("duration_s")
        calls = (steps.get(key) or {}).get("llm_calls")
        extra = ""
        if dur is not None:
            extra += f" · {dur}s"
        if calls is not None:
            extra += f" · {calls} llamadas"
        err = (steps.get(key) or {}).get("error")
        if s == "degraded" and err:
            st.caption(f"{label}: simulado por error — {err}")
        else:
            st.markdown(f"{chip(label, _status_chip(s))} {extra}", unsafe_allow_html=True)
    # judge progress
    if status == "running":
        j = prog.get("judge", {})
        total = j.get("total", 0)
        done = j.get("done", 0)
        if total:
            st.progress(min(done / max(1, total), 1.0), text=f"Evaluando respuestas: {done} de {total}")
    if status == "done":
        st.success("Análisis completado.")
        degradados = prog.get("degradados", {})
        if degradados:
            st.warning("Pasos en modo simulado: " + ", ".join(degradados.keys()))
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Ver diagnóstico", key=f"diag_{run_id}"):
                st.session_state["active_run_id"] = run_id
                st.switch_page("pages/3_Diagnostico.py")
        with c2:
            if st.button("Ver propuesta", key=f"prop_{run_id}"):
                st.session_state["active_run_id"] = run_id
                st.switch_page("pages/6_Propuesta.py")
    elif status == "error":
        st.error(prog.get("error") or "Error")
    elif status == "interrupted":
        st.warning("Análisis interrumpido.")
        if st.button("Relanzar", key=f"rel_{run_id}"):
            st.rerun()


def render_progress(run_id: str) -> None:
    prog = jobs.read_progress(run_id)
    if not prog or prog.get("status") != "running":
        _progress_fragment(run_id)
        return
    _progress_fragment(run_id)
