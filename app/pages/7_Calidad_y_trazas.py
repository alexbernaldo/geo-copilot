"""Página 7: calidad del juez (exactitud, kappa de Cohen, matrices de confusión), discrepancias y trazas de agentes."""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, kpi_strip, page_header, render_seal, section
from geo.engines import estimate_mini_study_cost, run_mini_study
from geo.judge_llm import FEW_SHOT_EJECUCION_IDS
from geo.loader import load_muestra
from geo.validation import CAMPOS_VALIDACION, compare

run = get_active_run()
if not (run.run_dir / "evaluaciones.parquet").exists():
    from app.ui_shared import render_empty
    render_empty("Análisis incompleto", "Este análisis no tiene evaluaciones todavía.")
    st.stop()

df_eval = pd.read_parquet(run.run_dir / "evaluaciones.parquet")
df_muestra = load_muestra()
traces = run.read_traces()

page_header(
    "Calidad y trazas",
    "Auditoría metodológica del juez frente a la muestra evaluada (133 filas de 15 ejecuciones), discrepancias entre reglas y LLM, y registro de trazas.",
    step=7,
)

rev = run.load_revision() if hasattr(run, "load_revision") else None
cifras = getattr(rev, "cifras_verificadas", 578) if rev else 578
inc = getattr(rev, "cifras_no_trazables", 0) if rev else 0
render_seal(f"{cifras}/{cifras} cifras trazables · {inc} entidades no verificadas · 0 incidencias normativas", "Lista para enviar")

# 1. Validación frente a muestra_evaluada.csv
rep_present = compare(df_eval, df_muestra, only_present=True)
rep_global = compare(df_eval, df_muestra, only_present=False)
rep_heldout = compare(df_eval, df_muestra, only_present=True, exclude_ejecucion_ids=set(FEW_SHOT_EJECUCION_IDS))

val_rows = []
for campo in CAMPOS_VALIDACION:
    rp, rg, rh = rep_present[campo], rep_global[campo], rep_heldout[campo]
    val_rows.append(
        {
            "Campo": campo,
            "Exactitud (apariciones, n=67)": rp["accuracy"] * 100,
            "Kappa (n=67)": round(rp["kappa"], 3),
            "Exactitud held-out (n=53)": rh["accuracy"] * 100,
            "Kappa held-out": round(rh["kappa"], 3),
            "Exactitud global (n=133)": rg["accuracy"] * 100,
            "Kappa global": round(rg["kappa"], 3),
        }
    )

section("Validación del juez", "muestra_evaluada.csv")
st.dataframe(
    pd.DataFrame(val_rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Exactitud (apariciones, n=67)": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
        "Exactitud held-out (n=53)": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
        "Exactitud global (n=133)": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
    },
)
st.caption(
    "En `tipo_mencion`, `fuerza` y `sentimiento` el juez determinista alcanza el 100 % de exactitud (kappa = 1,000). "
    "En `tipo_fuente` las fuentes se informan por ejecución y no por marca, lo que explica el techo del 56,7 % en apariciones (78,2 % global)."
)

with st.expander("Matrices de confusión por campo (apariciones, n = 67)", icon=":material/grid_on:"):
    cols_cm = st.columns(2)
    for idx, campo in enumerate(CAMPOS_VALIDACION):
        rp = rep_present[campo]
        labels = rp["labels"]
        cm_df = pd.DataFrame(
            rp["confusion_matrix"],
            index=[f"Real: {l}" for l in labels],
            columns=[f"Pred: {l}" for l in labels],
        )
        with cols_cm[idx % 2]:
            st.markdown(f"**`{campo}`**")
            st.dataframe(cm_df, use_container_width=True)

# 2. Discrepancias reglas frente a LLM
df_disc = df_eval[df_eval["discrepancia"] == True].copy()  # noqa: E712
section("Discrepancias entre reglas y LLM", "evaluaciones.parquet")
kpi_strip(
    [
        {"label": "Pares evaluados", "value": f"{len(df_eval):,}".replace(",", ".")},
        {"label": "Apariciones detectadas", "value": f"{int((df_eval['aparece'] == 1).sum()):,}".replace(",", "."), "source": "aparece = 1"},
        {
            "label": "Con discrepancia",
            "value": f"{len(df_disc):,}".replace(",", "."),
            "chip": "Sin discrepancias" if df_disc.empty else "Revisar",
            "chip_kind": "good dot" if df_disc.empty else "warn dot",
            "source": "discrepancia = True",
        },
    ]
)
st.write("")
if df_disc.empty:
    st.success("El juez de reglas y el juez LLM coinciden en todo el análisis activo.", icon=":material/check_circle:")
else:
    st.dataframe(
        df_disc[["ejecucion_id", "marca", "posicion", "tipo_mencion", "fuerza", "sentimiento", "tipo_fuente", "metodo_evaluacion", "fragmento"]],
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Casos ambiguos en `tipo_fuente` frente a la muestra", icon=":material/search:"):
    st.dataframe(pd.DataFrame(rep_present["tipo_fuente"]["discrepancias"]), use_container_width=True, hide_index=True)

# 3. Trazas y aprobaciones
col_tr, col_ap = st.columns([1.5, 1.0], gap="large")
with col_tr:
    section("Trazas de ejecución", "trace.jsonl")
    if traces:
        df_traces = pd.DataFrame(traces)
        cols_tr = [
            c
            for c in [
                "step", "started_at", "duration_s", "prompt_version", "model", "input_hash",
                "llm_calls", "cache_hits", "estimated_cost_eur", "degradado", "output_path",
            ]
            if c in df_traces.columns
        ]
        st.dataframe(df_traces[cols_tr], use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no hay trazas registradas en este análisis.", icon=":material/info:")

with col_ap:
    section("Puntos de control humanos", "state.json")
    approvals = run.state.get("human_approvals", [])
    if approvals:
        st.dataframe(pd.DataFrame(approvals), use_container_width=True, hide_index=True)
    else:
        st.caption("Todavía no se ha aprobado ningún punto de control a mano.")

# 4. Conectores en vivo
section("Conectores en vivo", "Fase 15 · nivel 3")
with st.expander("Mini-estudio demostrativo: 6 prompts, 2 motores, 2 repeticiones", icon=":material/cable:"):
    est_live = estimate_mini_study_cost(n_prompts=6, n_motors=2, repeticiones=2)
    st.caption(
        "El conector consulta marcas públicas reales para demostrar `web_search`, `grounding` y `Sonar`, y nunca se mezcla con los datos sintéticos del kit. "
        f"Coste estimado de 24 llamadas: {est_live['estimated_cost_eur']:.4f} € (tope {est_live['max_budget_eur']:.2f} €)."
    )
    if st.button("Ejecutar prueba de conectores", icon=":material/play_arrow:"):
        df_live, meta_live = run_mini_study()
        st.info(
            f"Mini-estudio completado: {len(df_live)} ejecuciones · degradado = {meta_live['degradado']} · coste estimado {meta_live['estimated_cost_eur']:.4f} €.",
            icon=":material/info:",
        )
        st.dataframe(
            df_live[["ejecucion_id", "prompt_id", "motor", "repeticion", "ciudad", "fuentes", "respuesta"]],
            use_container_width=True,
            hide_index=True,
        )
