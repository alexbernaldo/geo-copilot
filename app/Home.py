"""Página de inicio de la interfaz Streamlit de GEO Copilot (F13)."""

from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import ensure_demo_run_ready, get_active_run, render_header_banner
from geo.config import BRIEF_MD
from geo.judge_llm import estimate_judge_llm_workload
from geo.loader import load_ejecuciones, load_marcas
from geo.orchestrator import Run
from geo.detection import detect

st.set_page_config(
    page_title="GEO Copilot · reload. × UFV-EPS",
    page_icon="🧭",
    layout="wide",
)

render_header_banner()

st.title("🧭 GEO Copilot · Visibilidad y Estrategia en Asistentes de IA")
st.markdown(
    """
    **GEO Copilot** transforma el brief de una marca y el estudio de citación en motores generativos
    (**ChatGPT, Gemini, Perplexity y Claude**) en un **diagnóstico riguroso, hallazgos con evidencia trazable
    y un plan de acción presupuestado y verificado normativamente**.
    """
)

col_demo, col_new = st.columns([1, 1], gap="large")

with col_demo:
    st.subheader("⚡ Modo Demo Instantáneo (Recomendado)")
    st.markdown(
        """
        Precarga el análisis completo de **Clínica Alborada Visión** (`runs/demo/`) sin depender de conexión
        a internet ni claves de API, con las **624 ejecuciones**, las **12 tablas**, los **7 hallazgos**,
        el **plan de acción de 14 iniciativas** y la **propuesta verificada (563/563 cifras trazables)**.
        """
    )
    if st.button("🚀 Abrir Run de Demo (`runs/demo/`)", type="primary", use_container_width=True):
        run_demo = ensure_demo_run_ready()
        st.session_state["active_run_id"] = run_demo.run_id
        st.success(f"Run `{run_demo.run_id}` cargado. Navega por las páginas 1 a 7 del menú izquierdo.")

with col_new:
    st.subheader("🛠️ Configurar nueva ejecución")
    modo_sel = st.selectbox(
        "Modo de análisis",
        options=["cliente", "prospecto"],
        format_func=lambda m: "Modo Cliente (con brief)" if m == "cliente" else "Modo Prospecto (captación sin brief)",
    )
    prov_sel = st.selectbox(
        "Proveedor LLM",
        options=["mock", "anthropic", "openai"],
        help="En modo 'mock' todo el pipeline se ejecuta de forma determinista sin red ni claves.",
    )

    marcas_cat = [m.nombre for m in load_marcas()]
    marca_prospecto = None
    uploaded_brief = None
    if modo_sel == "prospecto":
        marca_prospecto = st.selectbox(
            "Selecciona marca prospecto del sector",
            options=[m for m in marcas_cat if m != "Clínica Alborada Visión"],
            index=2,
        )
    else:
        uploaded_brief = st.file_uploader(
            "Subir brief (.md, .docx o .txt) — o deja vacío para usar el brief de ejemplo de Clínica Alborada Visión",
            type=["md", "docx", "txt"],
        )

    # Estimación de coste previa
    with st.expander("💰 Ver estimación previa de llamadas y coste LLM"):
        df_ej = load_ejecuciones()
        df_det = detect(df_ej, load_marcas())
        est = estimate_judge_llm_workload(df_det, df_ej)
        if prov_sel == "mock":
            st.write("**Proveedor `mock`:** 0 llamadas de red · **Coste: 0,00 €**")
        else:
            st.write(
                f"- **Llamadas máximas (juez + estrategia + revisor + redactor):** ~{int(est['n_calls']) + 4} llamadas\n"
                f"- **Tokens estimados:** ~{int(est['tokens_in_est']):,} entrada / ~{int(est['tokens_out_est']):,} salida\n"
                f"- **Coste estimado:** ~{float(est['cost_est_eur']):.4f} €"
            )

    if st.button("▶️ Ejecutar Pipeline Completo", use_container_width=True):
        brief_target = BRIEF_MD
        if uploaded_brief is not None:
            tmp_brief = Path(f"/tmp/{uploaded_brief.name}")
            tmp_brief.write_bytes(uploaded_brief.getvalue())
            brief_target = tmp_brief

        with st.spinner("Ejecutando pipeline GEO Copilot..."):
            new_run = Run(
                modo=modo_sel,  # type: ignore[arg-type]
                brief_path=brief_target,
                marca_prospecto=marca_prospecto,
                provider=prov_sel,
            )
            new_run.run_all(auto_approve=True, force=True)
            st.session_state["active_run_id"] = new_run.run_id
        st.success(f"Ejecución `{new_run.run_id}` completada con éxito.")

st.divider()
active_run = get_active_run()
ficha_actual = active_run.load_ficha()
st.markdown(f"### 📋 Estado del Run Activo (`{active_run.run_id}`) — **{ficha_actual.marca}**")
steps_cols = st.columns(len(active_run.state["steps"]))
for col, (step_name, status) in zip(steps_cols, active_run.state["steps"].items()):
    icon = "✅" if status == "done" else ("⏳" if status == "awaiting_human" else "⚪")
    col.metric(label=step_name, value=f"{icon} {status}")
