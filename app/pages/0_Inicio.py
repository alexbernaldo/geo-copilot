"""Inicio: abrir el análisis de demostración, seguir el recorrido o configurar una ejecución propia."""

from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import (
    chip,
    ensure_demo_run_ready,
    get_active_run,
    page_header,
    panel,
    section,
)
from geo.config import BRIEF_MD
from geo.detection import detect
from geo.judge_llm import estimate_judge_llm_workload
from geo.loader import load_ejecuciones, load_marcas
from geo.orchestrator import Run

STEP_LABELS = {
    "intake": "Ficha del brief",
    "market": "Mercado",
    "detect": "Detección de marcas",
    "judge": "Juez de menciones",
    "metrics": "Métricas",
    "findings": "Hallazgos",
    "plan": "Plan",
    "review": "Revisión",
    "write": "Redacción",
    "export": "Exportación",
}
STATUS_UI = {
    "done": ("Completado", "good dot"),
    "awaiting_human": ("Espera aprobación", "warn dot"),
}
# (página, título, icono, descripción, punto de control)
JOURNEY = [
    ("pages/1_Brief.py", "Ficha", ":material/assignment:", "Revisa y confirma los datos que el código extrajo del brief.", "checkpoint_0_brief"),
    ("pages/2_Competidores.py", "Competencia", ":material/groups:", "Contrasta los competidores del brief con los que citan los motores.", "checkpoint_1_competidores"),
    ("pages/3_Diagnostico.py", "Diagnóstico", ":material/monitoring:", "Visibilidad espontánea y asistida por motor, ciudad y fase.", None),
    ("pages/4_Hallazgos.py", "Hallazgos", ":material/lightbulb:", "Problemas y fortalezas con cifra, origen y evidencia.", "checkpoint_2_hallazgos"),
    ("pages/5_Plan.py", "Plan", ":material/route:", "Iniciativas, presupuesto, calendario y simulador de impacto.", "checkpoint_3_plan"),
    ("pages/6_Propuesta.py", "Propuesta", ":material/description:", "Documento ejecutivo verificado, listo para exportar.", None),
    ("pages/7_Calidad_y_trazas.py", "Calidad y trazas", ":material/verified:", "Exactitud del juez, discrepancias y trazas de los agentes.", None),
]

page_header(
    "Análisis GEO",
    "Convierte el brief de una marca y el estudio de citación en ChatGPT, Gemini, Perplexity y Claude en un diagnóstico "
    "trazable, hallazgos con evidencia y un plan presupuestado y verificado.",
)

with panel("Análisis de demostración", "runs/demo/"):
    c_txt, c_btn = st.columns([3, 2], gap="large", vertical_alignment="center")
    with c_txt:
        st.markdown("Estudio completo de **Clínica Alborada Visión**, sin conexión ni claves de API.")
        st.caption("624 ejecuciones · 12 tablas · 7 hallazgos · plan de 14 iniciativas · 563/563 cifras trazables en la propuesta.")
    with c_btn:
        if st.button("Abrir demostración", type="primary", icon=":material/play_arrow:", use_container_width=True):
            run_demo = ensure_demo_run_ready()
            st.session_state["active_run_id"] = run_demo.run_id
            st.toast(f"Análisis «{run_demo.run_id}» cargado.", icon=":material/check_circle:")
            st.rerun()

active_run = get_active_run()
ficha_actual = active_run.load_ficha()
cps = active_run.state.get("checkpoints", {})

pendientes = [(t, k) for _, t, _, _, k in JOURNEY if k and not cps.get(k)]
siguiente = (
    f"Siguiente paso: {pendientes[0][0]}." if pendientes else "Los cuatro puntos de control están aprobados. Ya puedes descargar la propuesta."
)
section("Recorrido del análisis", f"{ficha_actual.marca} · {active_run.run_id}", siguiente)

with st.container(border=True, key="journey"):
    for i, (path, title, icon, desc, cp) in enumerate(JOURNEY):
        with st.container(key=f"jrow_{i}"):
            c_link, c_desc, c_state = st.columns([2, 5, 2], vertical_alignment="center")
            c_link.page_link(path, label=title, icon=icon)
            c_desc.caption(desc)
            if cp:
                if cps.get(cp):
                    c_state.badge("Aprobado", icon=":material/check:", color="blue")
                else:
                    c_state.badge("Pendiente", icon=":material/schedule:", color="orange")

with st.expander("Estado técnico del pipeline", icon=":material/account_tree:"):
    items = []
    for step_name, status in active_run.state["steps"].items():
        label, kind = STATUS_UI.get(status, ("Pendiente", ""))
        items.append(f"<li><span>{STEP_LABELS.get(step_name, step_name)}</span>{chip(label, kind)}</li>")
    st.markdown(f'<ul class="geo-list">{"".join(items)}</ul>', unsafe_allow_html=True)

with st.expander("Configurar una ejecución propia", icon=":material/tune:"):
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        modo_sel = st.selectbox(
            "Modo de análisis",
            options=["cliente", "prospecto"],
            format_func=lambda m: "Cliente (con brief)" if m == "cliente" else "Prospecto (captación sin brief)",
        )
        prov_sel = st.selectbox(
            "Proveedor LLM",
            options=["mock", "anthropic", "openai"],
            help="Con «mock» todo el pipeline se ejecuta de forma determinista, sin red ni claves.",
        )
    with col_b:
        marcas_cat = [m.nombre for m in load_marcas()]
        marca_prospecto = None
        uploaded_brief = None
        if modo_sel == "prospecto":
            marca_prospecto = st.selectbox(
                "Marca prospecto del sector",
                options=[m for m in marcas_cat if m != "Clínica Alborada Visión"],
                index=2,
            )
        else:
            uploaded_brief = st.file_uploader(
                "Brief (.md, .docx o .txt)",
                type=["md", "docx", "txt"],
                help="Si lo dejas vacío se usa el brief de ejemplo de Clínica Alborada Visión.",
            )

    df_ej = load_ejecuciones()
    df_det = detect(df_ej, load_marcas())
    est = estimate_judge_llm_workload(df_det, df_ej)
    if prov_sel == "mock":
        st.info("Proveedor `mock`: 0 llamadas de red y coste de 0,00 €.", icon=":material/payments:")
    else:
        st.info(
            f"Estimación: ~{int(est['n_calls']) + 4} llamadas (juez, estrategia, revisor y redactor), "
            f"~{int(est['tokens_in_est']):,} tokens de entrada y ~{int(est['tokens_out_est']):,} de salida. "
            f"Coste estimado: ~{float(est['cost_est_eur']):.4f} €.",
            icon=":material/payments:",
        )

    if st.button("Ejecutar pipeline completo", type="primary", icon=":material/rocket_launch:"):
        brief_target = BRIEF_MD
        if uploaded_brief is not None:
            tmp_brief = Path(f"/tmp/{uploaded_brief.name}")
            tmp_brief.write_bytes(uploaded_brief.getvalue())
            brief_target = tmp_brief

        with st.spinner("Ejecutando el pipeline…"):
            new_run = Run(
                modo=modo_sel,  # type: ignore[arg-type]
                brief_path=brief_target,
                marca_prospecto=marca_prospecto,
                provider=prov_sel,
            )
            new_run.run_all(auto_approve=True, force=True)
            st.session_state["active_run_id"] = new_run.run_id
        st.toast(f"Ejecución «{new_run.run_id}» completada.", icon=":material/check_circle:")
        st.rerun()
