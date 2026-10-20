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
        st.markdown(f"**{idx}.** {obj}")

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
