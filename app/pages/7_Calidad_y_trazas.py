"""Página 7 · Calidad del Juez (accuracy, kappa de Cohen, matrices de confusión), discrepancias y trazas de agentes (F13)."""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, render_header_banner
from geo.engines import estimate_mini_study_cost, run_mini_study
from geo.judge_llm import FEW_SHOT_EJECUCION_IDS
from geo.loader import load_muestra
from geo.validation import CAMPOS_VALIDACION, compare

st.set_page_config(page_title="7 · Calidad y Trazas | GEO Copilot", page_icon="🔬", layout="wide")
render_header_banner()

run = get_active_run()
if not (run.run_dir / "evaluaciones.parquet").exists():
    run.run_all(auto_approve=True, force=False)

df_eval = pd.read_parquet(run.run_dir / "evaluaciones.parquet")
df_muestra = load_muestra()
traces = run.read_traces()

st.title("7 · Calidad del Juez, Discrepancias y Trazas de Ejecución")
st.caption(
    "Auditoría metodológica frente a `muestra_evaluada.csv` (133 filas de 15 ejecuciones), revisión de discrepancias Reglas vs LLM y registro de trazas (`trace.jsonl`)."
)

# 1. Validación frente a muestra_evaluada.csv
st.subheader("🎯 Validación del Juez frente a `muestra_evaluada.csv`")

rep_present = compare(df_eval, df_muestra, only_present=True)
rep_global = compare(df_eval, df_muestra, only_present=False)
rep_heldout = compare(
    df_eval,
    df_muestra,
    only_present=True,
    exclude_ejecucion_ids=set(FEW_SHOT_EJECUCION_IDS),
)

val_rows = []
for campo in CAMPOS_VALIDACION:
    rp = rep_present[campo]
    rg = rep_global[campo]
    rh = rep_heldout[campo]
    val_rows.append(
        {
            "Campo evaluado": campo,
            "Accuracy (apariciones n=67)": f"{rp['accuracy'] * 100:.1f} % ({rp['aciertos']}/{rp['n']})",
            "Kappa de Cohen (n=67)": round(rp["kappa"], 3),
            "Accuracy Held-out (12 ejec., n=53)": f"{rh['accuracy'] * 100:.1f} % ({rh['aciertos']}/{rh['n']})",
            "Kappa Held-out": round(rh["kappa"], 3),
            "Accuracy Global (n=133)": f"{rg['accuracy'] * 100:.1f} % ({rg['aciertos']}/{rg['n']})",
            "Kappa Global (n=133)": round(rg["kappa"], 3),
        }
    )

st.dataframe(pd.DataFrame(val_rows), use_container_width=True, hide_index=True)
st.caption(
    "Nota metodológica: En `tipo_mencion`, `fuerza` y `sentimiento` el juez determinista alcanza **100 % de exactitud (kappa = 1,000)**. En `tipo_fuente`, las fuentes se informan a nivel de ejecución y no vinculadas a cada marca, lo que explica el techo determinista del 56,7 % en apariciones (78,2 % global)."
)

with st.expander("🔢 Ver matrices de confusión por campo (apariciones n=67)"):
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
            st.markdown(f"**Matriz de confusión · `{campo}`**")
            st.dataframe(cm_df, use_container_width=True)

st.divider()

# 2. Discrepancias Reglas vs LLM para revisión humana
st.subheader("⚖️ Revisión de discrepancias (Reglas vs LLM)")
df_disc = df_eval[df_eval["discrepancia"] == True].copy()  # noqa: E712
c_d1, c_d2, c_d3 = st.columns(3)
c_d1.metric("Total pares evaluados", f"{len(df_eval):,}")
c_d2.metric("Apariciones detectadas (`aparece=1`)", f"{int((df_eval['aparece'] == 1).sum()):,}")
c_d3.metric("Filas con `discrepancia == True`", f"{len(df_disc):,}")

if df_disc.empty:
    st.success(
        "No existen discrepancias entre el juez de reglas y el juez LLM en el run activo (`0` filas con `discrepancia == True`)."
    )
else:
    st.dataframe(
        df_disc[
            [
                "ejecucion_id",
                "marca",
                "posicion",
                "tipo_mencion",
                "fuerza",
                "sentimiento",
                "tipo_fuente",
                "metodo_evaluacion",
                "fragmento",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with st.expander("🔍 Ver casos de ambigüedad en `tipo_fuente` frente a `muestra_evaluada.csv`"):
    disc_fuente = pd.DataFrame(rep_present["tipo_fuente"]["discrepancias"])
    st.dataframe(disc_fuente, use_container_width=True, hide_index=True)

st.divider()

# 3. Trazas de ejecución de agentes (trace.jsonl) y aprobaciones humanas
col_tr, col_ap = st.columns([1.5, 1.0])

with col_tr:
    st.subheader("📜 Trazas de ejecución de agentes (`trace.jsonl`)")
    if traces:
        df_traces = pd.DataFrame(traces)
        cols_tr = [
            c
            for c in [
                "step",
                "started_at",
                "duration_s",
                "prompt_version",
                "model",
                "input_hash",
                "llm_calls",
                "cache_hits",
                "estimated_cost_eur",
                "degradado",
                "output_path",
            ]
            if c in df_traces.columns
        ]
        st.dataframe(
            df_traces[cols_tr],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hay trazas registradas todavía en este run.")

with col_ap:
    st.subheader("👤 Registro de Checkpoints Humanos (`state.json`)")
    approvals = run.state.get("human_approvals", [])
    if approvals:
        st.dataframe(pd.DataFrame(approvals), use_container_width=True, hide_index=True)
    else:
        st.caption("Aún no se han registrado aprobaciones manuales en este run.")

st.divider()

# 4. Conectores de motores con búsqueda web (F15 · Nivel 3)
with st.expander("🌐 Conectores en vivo y Mini-Estudio Demostrativo (F15 · 6 prompts × 2 motores × 2 repeticiones = 24 llamadas)"):
    est_live = estimate_mini_study_cost(n_prompts=6, n_motors=2, repeticiones=2)
    st.caption(
        f"**Aislamiento garantizado:** Este conector consulta marcas públicas reales para demostrar la integración con `web_search` / `grounding` / `Sonar` y **nunca se mezcla con los datos sintéticos del kit**. "
        f"Coste estimado para 24 llamadas: **`{est_live['estimated_cost_eur']:.4f} €`** (tope `MAX_BUDGET_EUR = {est_live['max_budget_eur']:.2f} €`)."
    )
    if st.button("🚀 Ejecutar prueba de conectores (24 llamadas con caché / fallback seguro)"):
        df_live, meta_live = run_mini_study()
        st.info(
            f"Mini-estudio completado: `{len(df_live)}` ejecuciones generadas · `degradado={meta_live['degradado']}` · `coste_estimado={meta_live['estimated_cost_eur']:.4f} €`."
        )
        st.dataframe(
            df_live[["ejecucion_id", "prompt_id", "motor", "repeticion", "ciudad", "fuentes", "respuesta"]],
            use_container_width=True,
            hide_index=True,
        )
