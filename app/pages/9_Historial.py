"""Página de historial de análisis."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from app.ui_shared import page_header, panel, chip
from geo import jobs
from geo.config import RUNS_DIR

page_header("Historial", "Análisis anteriores.")

runs = jobs.list_runs()
if not runs:
    st.info("No hay análisis.")
else:
    for r in runs:
        with panel(f"{r['run_id']}"):
            st.markdown(
                f"{chip(r['run_id'], '')} {chip('IA real' if r['provider'] == 'openrouter' else 'Simulado', 'good' if r['provider'] == 'openrouter' else '')} "
                f"· {r.get('modo')} · {r.get('created_at')} · {r.get('status')} · {r.get('cost_eur')} €",
                unsafe_allow_html=True,
            )
            degradados = r.get("degradados") or {}
            if degradados:
                st.caption("Pasos simulados: " + ", ".join(degradados.keys()))
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Abrir", key=f"open_{r['run_id']}"):
                    st.session_state["active_run_id"] = r["run_id"]
                    st.switch_page("pages/3_Diagnostico.py")
            with c2:
                prop = RUNS_DIR / r["run_id"] / ("propuesta_cliente.docx" if r.get("modo") == "cliente" else f"propuesta_prospecto_*.docx")
                # find any docx
                docxs = list((RUNS_DIR / r["run_id"]).glob("*.docx"))
                if docxs:
                    st.download_button("Descargar propuesta", data=docxs[0].read_bytes(), file_name=docxs[0].name, key=f"dl_{r['run_id']}")
            with c3:
                if r.get("provider") != "openrouter":
                    if st.button("Duplicar con IA real", key=f"dup_{r['run_id']}"):
                        st.session_state["nuevo_prefill"] = r
                        st.switch_page("pages/00_Nuevo_analisis.py")
