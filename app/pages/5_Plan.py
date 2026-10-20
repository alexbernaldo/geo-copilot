"""Página 5 · Plan estratégico GEO, Gantt, presupuesto, capacidad semanal y Checkpoint 3 (F13)."""

from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import COLOR_BRIEF, COLOR_LIDER, get_active_run, render_header_banner
from geo.budget import (
    compute_weekly_client_hours,
    effort_impact_matrix,
    get_template_hours_map,
    validate_and_adjust_plan,
)
from geo.config import CLIENT_WEEKLY_HOURS_CAPACITY
from geo.schemas import Accion, Plan
from geo.simulate import (
    DISCLAIMER_SIMULADOR,
    apply_simulation_to_plan_objectives,
    get_brand_baseline_params,
    simulate,
)

st.set_page_config(page_title="5 · Plan GEO | GEO Copilot", page_icon="🗺️", layout="wide")
render_header_banner()

run = get_active_run()
if not (run.run_dir / "plan.json").exists():
    run.run_all(auto_approve=True, force=False)

ficha = run.load_ficha()
hallazgos = run.load_hallazgos()
plan = run.load_plan()

st.title("5 · Plan Estratégico GEO y Checkpoint 3")
st.caption(
    "Hoja de ruta a 12 meses con trazabilidad a hallazgos, matriz Esfuerzo vs Impacto, cronograma por fases, control presupuestario y capacidad semanal del equipo del cliente."
)

# 1. Objetivos estratégicos y resumen presupuestario
col_obj, col_bud = st.columns([1.6, 1.0])
with col_obj:
    st.subheader("🎯 Objetivos estratégicos (horizonte 12 meses)")
    for idx, obj in enumerate(plan.objetivos, start=1):
        h_str = ", ".join(obj.hallazgos) if obj.hallazgos else "-"
        st.markdown(
            f"**{idx}. {obj.kpi}** · Actual: `{obj.valor_actual}` → Objetivo ({obj.plazo_meses}m): "
            f"`{obj.valor_objetivo_min} – {obj.valor_objetivo_max}` *(Hallazgos: {h_str})*"
        )

with col_bud:
    st.subheader("💶 Control presupuestario")
    min_b = ficha.presupuesto_min_eur or 18000.0
    max_b = ficha.presupuesto_max_eur or 27000.0
    coste = plan.coste_total_eur
    in_range = min_b <= coste <= max_b
    st.metric(
        "Coste total estimado (12 meses)",
        f"{coste:,.0f} €",
        f"Rango objetivo: {min_b:,.0f} € – {max_b:,.0f} €",
    )
    ratio = min(1.0, max(0.0, coste / max_b)) if max_b > 0 else 0.0
    st.progress(ratio, text=f"{ratio * 100:.1f}% del tope presupuestario ({max_b:,.0f} €)")
    if in_range:
        st.success(f"Presupuesto dentro de la horquilla orientativa ({min_b:,.0f} € – {max_b:,.0f} €).")
    elif coste > max_b:
        st.error(f"El coste ({coste:,.0f} €) supera el límite máximo ({max_b:,.0f} €).")
    else:
        st.warning(f"El coste ({coste:,.0f} €) está por debajo del rango mínimo ({min_b:,.0f} €).")

st.divider()

# 2. Matriz Esfuerzo vs Impacto + Cronograma Gantt por fases
col_mat, col_gantt = st.columns(2)

with col_mat:
    st.subheader("📊 Matriz Esfuerzo vs Impacto")
    df_mat = effort_impact_matrix(plan)
    if not df_mat.empty:
        # Añadir pequeño desplazamiento visual determinista por índice para evitar solapamiento exacto
        df_mat["esfuerzo_plot"] = df_mat["esfuerzo_num"] + (df_mat.index % 3 - 1) * 0.08
        df_mat["impacto_plot"] = df_mat["impacto_num"] + ((df_mat.index // 3) % 3 - 1) * 0.08
        fig_mat = px.scatter(
            df_mat,
            x="esfuerzo_plot",
            y="impacto_plot",
            size="coste_estimado_eur",
            color="palanca",
            hover_name="titulo",
            hover_data={
                "id": True,
                "esfuerzo": True,
                "impacto": True,
                "coste_estimado_eur": ":,.0f",
                "hallazgos": True,
                "esfuerzo_plot": False,
                "impacto_plot": False,
            },
            text="id",
            labels={
                "esfuerzo_plot": "Esfuerzo (1=S, 2=M, 3=L)",
                "impacto_plot": "Impacto esperado (1=S, 2=M, 3=L)",
                "palanca": "Palanca GEO",
            },
        )
        fig_mat.update_traces(textposition="top center")
        fig_mat.update_layout(
            xaxis=dict(tickmode="array", tickvals=[1, 2, 3], ticktext=["S (Bajo)", "M (Medio)", "L (Alto)"], range=[0.5, 3.5]),
            yaxis=dict(tickmode="array", tickvals=[1, 2, 3], ticktext=["S (Bajo)", "M (Medio)", "L (Alto)"], range=[0.5, 3.5]),
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_mat, use_container_width=True)

with col_gantt:
    st.subheader("🗓️ Cronograma por semanas (S1–S52)")
    gantt_rows = []
    for a in plan.acciones:
        gantt_rows.append(
            {
                "Acción": f"{a.id} · {a.titulo[:38]}",
                "Fase": f"Fase {a.fase_plan}",
                "Semana Inicio": int(a.semana_inicio),
                "Duración (sem)": int(a.plazo_semanas),
                "Semana Fin": int(a.semana_inicio + a.plazo_semanas - 1),
                "Responsable": a.responsable,
            }
        )
    df_gantt = pd.DataFrame(gantt_rows)
    if not df_gantt.empty:
        fig_gantt = go.Figure()
        phase_colors = {"Fase 0": "#1E40AF", "Fase 1": "#0B5FFF", "Fase 2": "#3B82F6", "Fase 3": "#64748B"}
        for fase_label, grp in df_gantt.groupby("Fase", sort=False):
            fig_gantt.add_trace(
                go.Bar(
                    y=grp["Acción"],
                    x=grp["Duración (sem)"],
                    base=grp["Semana Inicio"] - 1,
                    orientation="h",
                    name=str(fase_label),
                    marker_color=phase_colors.get(str(fase_label), COLOR_BRIEF),
                    hovertemplate="<b>%{y}</b><br>Semanas: S%{base} a S%{x}<extra></extra>",
                )
            )
        fig_gantt.update_layout(
            barmode="stack",
            xaxis_title="Semana del plan (1 a 52)",
            yaxis=dict(autorange="reversed"),
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

# 3. Capacidad semanal del equipo del cliente
st.subheader("👥 Carga semanal estimada del equipo del cliente (máx. 8 h/semana)")
tpl_hours = get_template_hours_map()
hours_by_id = {a.id: tpl_hours.get(a.titulo, 2.0) for a in plan.acciones}
weekly_hours = compute_weekly_client_hours(plan.acciones, hours_by_action_id=hours_by_id)
df_hours = pd.DataFrame(
    [{"Semana": w, "Horas equipo cliente": h, "Capacidad máxima": CLIENT_WEEKLY_HOURS_CAPACITY} for w, h in weekly_hours.items()]
)
fig_hrs = go.Figure()
fig_hrs.add_trace(
    go.Bar(
        x=df_hours["Semana"],
        y=df_hours["Horas equipo cliente"],
        name="Horas semanales requeridas",
        marker_color=COLOR_BRIEF,
    )
)
fig_hrs.add_trace(
    go.Scatter(
        x=df_hours["Semana"],
        y=df_hours["Capacidad máxima"],
        mode="lines",
        name=f"Capacidad máx. ({CLIENT_WEEKLY_HOURS_CAPACITY:.0f} h/sem)",
        line=dict(color="#DC2626", dash="dash", width=2),
    )
)
fig_hrs.update_layout(
    xaxis_title="Semana (1 a 52)",
    yaxis_title="Horas / semana",
    height=260,
    margin=dict(l=10, r=10, t=20, b=10),
)
st.plotly_chart(fig_hrs, use_container_width=True)

st.divider()

# 4. Tabla editable de acciones (Checkpoint 3)
st.subheader("✏️ Tabla editable de acciones del Plan (Checkpoint 3)")
st.caption(
    "Puedes ajustar costes, semanas de inicio, plazos, tallas de esfuerzo/impacto o activar/desactivar acciones antes de generar la propuesta final."
)

df_acc_edit = pd.DataFrame(
    [
        {
            "Incluir": True,
            "id": a.id,
            "fase_plan": a.fase_plan,
            "palanca": a.palanca,
            "titulo": a.titulo,
            "hallazgos": ", ".join(a.hallazgos_relacionados),
            "impacto": a.impacto,
            "esfuerzo": a.esfuerzo,
            "semana_inicio": a.semana_inicio,
            "plazo_semanas": a.plazo_semanas,
            "coste_estimado_eur": a.coste_estimado_eur,
            "responsable": a.responsable,
            "kpi": a.kpi,
        }
        for a in plan.acciones
    ]
)

edited_acc_df = st.data_editor(
    df_acc_edit,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Incluir": st.column_config.CheckboxColumn("Activa", default=True),
        "id": st.column_config.TextColumn("ID", disabled=True),
        "fase_plan": st.column_config.SelectboxColumn("Fase", options=[0, 1, 2, 3]),
        "palanca": st.column_config.SelectboxColumn(
            "Palanca",
            options=["contenido", "autoridad", "tecnico", "reputacion", "entidad", "medicion"],
        ),
        "titulo": st.column_config.TextColumn("Título de la acción"),
        "hallazgos": st.column_config.TextColumn("Hallazgos", disabled=True),
        "impacto": st.column_config.SelectboxColumn("Impacto", options=["S", "M", "L"]),
        "esfuerzo": st.column_config.SelectboxColumn("Esfuerzo", options=["S", "M", "L"]),
        "semana_inicio": st.column_config.NumberColumn("Semana inicio", min_value=1, max_value=52, step=1),
        "plazo_semanas": st.column_config.NumberColumn("Duración (sem)", min_value=1, max_value=48, step=1),
        "coste_estimado_eur": st.column_config.NumberColumn("Coste (€)", min_value=0.0, max_value=25000.0, step=100.0),
        "responsable": st.column_config.SelectboxColumn(
            "Responsable",
            options=["cliente_marketing", "cliente_it", "cliente_comunicacion", "agencia_geo", "externo_pr"],
        ),
        "kpi": st.column_config.TextColumn("KPI"),
    },
    key="editor_acciones_plan",
)

with st.expander("📋 Ver detalles de Medición, Riesgos y Supuestos del Plan"):
    col_m, col_r, col_s = st.columns(3)
    with col_m:
        st.markdown("**Protocolo de medición**")
        for m in plan.medicion:
            st.markdown(f"- {m}")
    with col_r:
        st.markdown("**Riesgos identificados**")
        for r in plan.riesgos:
            st.markdown(f"- {r}")
    with col_s:
        st.markdown("**Supuestos operativos**")
        for s in plan.supuestos:
            st.markdown(f"- {s}")

comentario_cp3 = st.text_input(
    "Comentario de validación del plan (opcional):",
    value="Plan validado dentro del rango 18.000–27.000 € y capacidad <= 8 h/semana.",
)

if st.button("✅ Aprobar Plan Estratégico (Checkpoint 3) y revalidar restricciones", type="primary"):
    orig_by_id = {a.id: a for a in plan.acciones}
    updated_acciones: list[Accion] = []
    for _, row in edited_acc_df.iterrows():
        if not bool(row["Incluir"]):
            continue
        aid = str(row["id"])
        orig = orig_by_id[aid]
        updated_acciones.append(
            orig.model_copy(
                update={
                    "fase_plan": int(row["fase_plan"]),  # type: ignore[arg-type]
                    "palanca": str(row["palanca"]),  # type: ignore[arg-type]
                    "titulo": str(row["titulo"]),
                    "impacto": str(row["impacto"]),  # type: ignore[arg-type]
                    "esfuerzo": str(row["esfuerzo"]),  # type: ignore[arg-type]
                    "semana_inicio": int(row["semana_inicio"]),
                    "plazo_semanas": int(row["plazo_semanas"]),
                    "coste_estimado_eur": float(row["coste_estimado_eur"]),
                    "responsable": str(row["responsable"]),  # type: ignore[arg-type]
                    "kpi": str(row["kpi"]),
                }
            )
        )

    candidate_plan = plan.model_copy(
        update={
            "acciones": updated_acciones,
            "coste_total_eur": round(sum(a.coste_estimado_eur for a in updated_acciones), 2),
        }
    )
    validated_plan = validate_and_adjust_plan(
        candidate_plan,
        ficha,
        hallazgos,
        hours_by_action_id={a.id: tpl_hours.get(a.titulo, 2.0) for a in updated_acciones},
    )
    run.save_plan(validated_plan)
    run.approve_checkpoint("checkpoint_3_plan", note=comentario_cp3)
    st.success(
        f"Checkpoint 3 aprobado. Plan guardado con {len(validated_plan.acciones)} acciones y coste total de {validated_plan.coste_total_eur:,.0f} €."
    )
    st.rerun()

st.divider()

# 5. Simulador What-if del Score de Citación (F14)
st.subheader("🧪 Simulador What-If de Impacto en el Score de Citación (F14)")
st.warning(f"⚠️ **{DISCLAIMER_SIMULADOR}** Recalcula el Score espontáneo aplicando la fórmula de `geo/metrics.py` sobre los parámetros objetivo seleccionados.")

df_eval_sim = pd.read_parquet(run.run_dir / "evaluaciones.parquet")
base_params = get_brand_baseline_params(df_eval_sim, ficha.marca)

ap_madrid_base = round(base_params["aparicion_por_ciudad"].get("Madrid", 0.5417) * 100.0, 1)
ap_bcn_base = round(base_params["aparicion_por_ciudad"].get("Barcelona", 0.0417) * 100.0, 1)
ap_chatgpt_base = round(base_params["aparicion_por_motor"].get("ChatGPT", 0.1833) * 100.0, 1)
ap_claude_base = round(base_params["aparicion_por_motor"].get("Claude", 0.15) * 100.0, 1)
ap_gemini_base = round(base_params["aparicion_por_motor"].get("Gemini", 0.5667) * 100.0, 1)
ap_perp_base = round(base_params["aparicion_por_motor"].get("Perplexity", 0.65) * 100.0, 1)
fuerza_base = round(float(base_params["fuerza_presentes"]), 2)
pct_qual_base = round(float(base_params["pct_fuentes_calidad"]) * 100.0, 1)

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown("**1. Aparición espontánea por ciudad (%)**")
    sl_madrid = st.slider(
        "Madrid (% aparición espontánea)",
        min_value=0.0,
        max_value=100.0,
        value=ap_madrid_base,
        step=0.5,
        key="sim_madrid",
    )
    sl_bcn = st.slider(
        "Barcelona (% aparición espontánea)",
        min_value=0.0,
        max_value=100.0,
        value=ap_bcn_base,
        step=0.5,
        key="sim_bcn",
    )

with col_s2:
    st.markdown("**2. Aparición espontánea por motor (%)**")
    sl_chatgpt = st.slider(
        "ChatGPT (% aparición)",
        min_value=0.0,
        max_value=100.0,
        value=ap_chatgpt_base,
        step=0.5,
        key="sim_chatgpt",
    )
    sl_claude = st.slider(
        "Claude (% aparición)",
        min_value=0.0,
        max_value=100.0,
        value=ap_claude_base,
        step=0.5,
        key="sim_claude",
    )
    sl_gemini = st.slider(
        "Gemini (% aparición)",
        min_value=0.0,
        max_value=100.0,
        value=ap_gemini_base,
        step=0.5,
        key="sim_gemini",
    )
    sl_perp = st.slider(
        "Perplexity (% aparición)",
        min_value=0.0,
        max_value=100.0,
        value=ap_perp_base,
        step=0.5,
        key="sim_perp",
    )

with col_s3:
    st.markdown("**3. Fuerza de recomendación y Calidad de fuente**")
    sl_fuerza = st.slider(
        "Fuerza media objetivo en apariciones (0 a 3)",
        min_value=0.0,
        max_value=3.0,
        value=fuerza_base,
        step=0.05,
        key="sim_fuerza",
    )
    sl_qual = st.slider(
        "% de fuentes de alta calidad (Institucional / Medio >= 0.9)",
        min_value=0.0,
        max_value=100.0,
        value=pct_qual_base,
        step=0.5,
        key="sim_qual",
    )

cambios_ui = {
    "aparicion_por_ciudad": {
        "Madrid": sl_madrid / 100.0,
        "Barcelona": sl_bcn / 100.0,
    },
    "aparicion_por_motor": {
        "ChatGPT": sl_chatgpt / 100.0,
        "Claude": sl_claude / 100.0,
        "Gemini": sl_gemini / 100.0,
        "Perplexity": sl_perp / 100.0,
    },
    "fuerza_media_objetivo": sl_fuerza,
    "pct_fuentes_calidad": sl_qual / 100.0,
}

sim_res = simulate(df_eval_sim, ficha.marca, cambios=cambios_ui)

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Score espontáneo actual",
    f"{sim_res['score_actual']:.2f} / 100",
    f"Puesto actual: {sim_res['puesto_actual']}º de 10",
)
k2.metric(
    "Score espontáneo simulado",
    f"{sim_res['score_simulado']:.2f} / 100",
    f"{sim_res['delta_score']:+.2f} pts ({DISCLAIMER_SIMULADOR})",
)
k3.metric(
    "Puesto en el ranking simulado",
    f"{sim_res['puesto_simulado']}º de 10",
    f"{sim_res['delta_puesto']:+d} posiciones" if sim_res["delta_puesto"] != 0 else "Mismo puesto",
)
k4.metric(
    "Aparición espontánea global",
    f"{sim_res['tasa_aparicion_simulada'] * 100:.1f} %",
    f"Actual: {sim_res['tasa_aparicion_actual'] * 100:.1f} %",
)

col_sim_chart, col_sim_rank = st.columns([1.1, 1.0])
with col_sim_chart:
    comp_act = sim_res["componentes"]["actual"]
    comp_sim = sim_res["componentes"]["simulado"]
    df_comp_plot = pd.DataFrame(
        [
            {"Componente": "Aparición (30)", "Escenario": "Actual", "Puntos": comp_act["aparicion"]},
            {"Componente": "Aparición (30)", "Escenario": "Simulado", "Puntos": comp_sim["aparicion"]},
            {"Componente": "Posición (20)", "Escenario": "Actual", "Puntos": comp_act["posicion"]},
            {"Componente": "Posición (20)", "Escenario": "Simulado", "Puntos": comp_sim["posicion"]},
            {"Componente": "Fuerza (30)", "Escenario": "Actual", "Puntos": comp_act["fuerza"]},
            {"Componente": "Fuerza (30)", "Escenario": "Simulado", "Puntos": comp_sim["fuerza"]},
            {"Componente": "Fuente (20)", "Escenario": "Actual", "Puntos": comp_act["fuente"]},
            {"Componente": "Fuente (20)", "Escenario": "Simulado", "Puntos": comp_sim["fuente"]},
        ]
    )
    fig_sim = px.bar(
        df_comp_plot,
        x="Componente",
        y="Puntos",
        color="Escenario",
        barmode="group",
        text_auto=".2f",
        color_discrete_map={"Actual": COLOR_LIDER, "Simulado": COLOR_BRIEF},
        title=f"Desglose del Score: Actual ({sim_res['score_actual']:.2f}) vs Simulado ({sim_res['score_simulado']:.2f}) — {DISCLAIMER_SIMULADOR}",
    )
    fig_sim.update_layout(height=340, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_sim, use_container_width=True)

with col_sim_rank:
    st.markdown("**Ranking espontáneo simulado (`n=240`)**")
    st.dataframe(sim_res["ranking_simulado"], use_container_width=True, hide_index=True)

if st.button("🎯 Usar como objetivo en el Plan", use_container_width=False):
    updated_plan_obj = apply_simulation_to_plan_objectives(plan, sim_res)
    run.save_plan(updated_plan_obj)
    st.success(
        f"Objetivo what-if volcado a `plan.objetivos` (Score {sim_res['score_actual']:.2f} → {sim_res['score_simulado']:.2f}, puesto {sim_res['puesto_actual']}º → {sim_res['puesto_simulado']}º)."
    )
    st.rerun()
