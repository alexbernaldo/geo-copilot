"""Página 5: plan estratégico GEO, cronograma, presupuesto, capacidad semanal y simulador (punto de control 3)."""

from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import (
    cat_colors,
    checkpoint_summary,
    get_active_run,
    kpi_strip,
    page_header,
    panel,
    section,
    show_fig,
    tokens,
)
from geo.budget import (
    compute_weekly_client_hours,
    effort_impact_matrix,
    get_template_hours_map,
    validate_and_adjust_plan,
)
from geo.config import CLIENT_WEEKLY_HOURS_CAPACITY
from geo.schemas import Accion
from geo.simulate import (
    DISCLAIMER_SIMULADOR,
    apply_simulation_to_plan_objectives,
    get_brand_baseline_params,
    simulate,
)

run = get_active_run()
if not (run.run_dir / "plan.json").exists():
    from app.ui_shared import render_empty
    render_empty("Análisis incompleto", "Este análisis no tiene plan todavía.")
    st.stop()

ficha = run.load_ficha()
hallazgos = run.load_hallazgos()
plan = run.load_plan()
t = tokens()

page_header(
    "Plan de acción",
    "Hoja de ruta a 12 meses con trazabilidad a los hallazgos, control de presupuesto y respeto de la capacidad semanal del equipo del cliente.",
    checkpoint=3,
    step=5,
)

# 1. Presupuesto y objetivos
min_b = ficha.presupuesto_min_eur or 18000.0
max_b = ficha.presupuesto_max_eur or 27000.0
coste = plan.coste_total_eur
in_range = min_b <= coste <= max_b
ratio = min(1.0, max(0.0, coste / max_b)) if max_b > 0 else 0.0

kpi_strip(
    [
        {
            "label": "Coste total estimado",
            "value": f"{coste:,.0f}".replace(",", "."),
            "unit": "€",
            "note": f"{ratio * 100:.1f} % del tope presupuestario",
            "source": "Plan a 12 meses · suma de iniciativas",
            "highlight": True,
        },
        {
            "label": "Horquilla del brief",
            "value": f"{min_b:,.0f} a {max_b:,.0f}".replace(",", "."),
            "unit": "€",
            "chip": "Dentro" if in_range else ("Por encima" if coste > max_b else "Por debajo"),
            "chip_kind": "good dot" if in_range else "err dot",
            "source": "Ficha de la marca",
        },
        {
            "label": "Iniciativas",
            "value": str(len(plan.acciones)),
            "note": f"Capacidad del cliente: hasta {CLIENT_WEEKLY_HOURS_CAPACITY:.0f} h por semana",
            "source": "Plan · acciones activas",
        },
    ]
)
if coste > max_b:
    st.error(f"El coste ({coste:,.0f} €) supera el límite máximo ({max_b:,.0f} €).", icon=":material/error:")
elif coste < min_b:
    st.warning(f"El coste ({coste:,.0f} €) está por debajo del rango mínimo ({min_b:,.0f} €).", icon=":material/warning:")

section("Objetivos estratégicos", "Horizonte de 12 meses")
df_obj = pd.DataFrame(
    [
        {
            "KPI": obj.kpi,
            "Actual": str(obj.valor_actual),
            "Objetivo": f"{obj.valor_objetivo_min} a {obj.valor_objetivo_max}",
            "Plazo (meses)": obj.plazo_meses,
            "Hallazgos": ", ".join(obj.hallazgos) if obj.hallazgos else "-",
        }
        for obj in plan.objetivos
    ]
)
st.dataframe(df_obj, use_container_width=True, hide_index=True)

# 2. Matriz y cronograma
section("Priorización y calendario")
col_mat, col_gantt = st.columns(2, gap="medium")

with col_mat:
    with panel("Matriz esfuerzo e impacto", "Tamaño = coste estimado"):
        df_mat = effort_impact_matrix(plan)
        if not df_mat.empty:
            df_mat["palanca"] = df_mat["palanca"].str.replace("_", " ").str.capitalize()
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
                    "id": True, "esfuerzo": True, "impacto": True, "coste_estimado_eur": ":,.0f",
                    "hallazgos": True, "esfuerzo_plot": False, "impacto_plot": False,
                },
                text="id",
                color_discrete_sequence=cat_colors(),
                labels={"esfuerzo_plot": "Esfuerzo", "impacto_plot": "Impacto esperado", "palanca": "Palanca GEO"},
            )
            fig_mat.update_traces(textposition="top center", marker=dict(line=dict(width=1, color=t["surface"])))
            fig_mat.update_layout(
                xaxis=dict(tickmode="array", tickvals=[1, 2, 3], ticktext=["Bajo", "Medio", "Alto"], range=[0.5, 3.5]),
                yaxis=dict(tickmode="array", tickvals=[1, 2, 3], ticktext=["Bajo", "Medio", "Alto"], range=[0.5, 3.5]),
            )
            show_fig(fig_mat, 420)

with col_gantt:
    with panel("Cronograma por semanas", "S1 a S52"):
        gantt_rows = [
            {
                "Acción": f"{a.id} · {a.titulo[:38]}",
                "Fase": f"Fase {a.fase_plan}",
                "Semana Inicio": int(a.semana_inicio),
                "Duración (sem)": int(a.plazo_semanas),
            }
            for a in plan.acciones
        ]
        df_gantt = pd.DataFrame(gantt_rows)
        if not df_gantt.empty:
            fig_gantt = go.Figure()
            cc = cat_colors()
            phase_colors = {"Fase 0": t["lead"], "Fase 1": cc[0], "Fase 2": cc[1], "Fase 3": t["line-3"]}
            for fase_label, grp in df_gantt.groupby("Fase", sort=False):
                fig_gantt.add_trace(
                    go.Bar(
                        y=grp["Acción"],
                        x=grp["Duración (sem)"],
                        base=grp["Semana Inicio"] - 1,
                        orientation="h",
                        name=str(fase_label),
                        marker_color=phase_colors.get(str(fase_label), t["accent"]),
                        hovertemplate="<b>%{y}</b><br>Duración: %{x} semanas<extra></extra>",
                    )
                )
            fig_gantt.update_layout(barmode="stack", xaxis_title="Semana del plan", yaxis=dict(autorange="reversed", tickfont=dict(size=11)))
            show_fig(fig_gantt, 420)

# 3. Capacidad semanal
tpl_hours = get_template_hours_map()
hours_by_id = {a.id: tpl_hours.get(a.titulo, 2.0) for a in plan.acciones}
weekly_hours = compute_weekly_client_hours(plan.acciones, hours_by_action_id=hours_by_id)
df_hours = pd.DataFrame(
    [{"Semana": w, "Horas": h, "Capacidad": CLIENT_WEEKLY_HOURS_CAPACITY} for w, h in weekly_hours.items()]
)
section("Carga del equipo del cliente")
with panel("Horas por semana frente a la capacidad", f"Máximo {CLIENT_WEEKLY_HOURS_CAPACITY:.0f} h por semana"):
    fig_hrs = go.Figure()
    fig_hrs.add_trace(go.Bar(x=df_hours["Semana"], y=df_hours["Horas"], name="Horas requeridas", marker_color=cat_colors()[0]))
    fig_hrs.add_trace(
        go.Scatter(
            x=df_hours["Semana"], y=df_hours["Capacidad"], mode="lines",
            name=f"Capacidad ({CLIENT_WEEKLY_HOURS_CAPACITY:.0f} h)", line=dict(color=t["err"], dash="dash", width=2),
        )
    )
    fig_hrs.update_layout(xaxis_title="Semana (1 a 52)", yaxis_title="Horas por semana")
    show_fig(fig_hrs, 260)

# 4. Tabla editable de acciones
section(
    "Acciones del plan",
    "Punto de control 3",
    "Ajusta costes, semanas, plazos y tallas, o desactiva acciones antes de generar la propuesta.",
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
            options=sorted({"contenido", "autoridad", "tecnico", "reputacion", "entidad", "medicion", *df_acc_edit["palanca"].dropna().astype(str)}),
        ),
        "titulo": st.column_config.TextColumn("Título de la acción", width="large"),
        "hallazgos": st.column_config.TextColumn("Hallazgos", disabled=True),
        "impacto": st.column_config.SelectboxColumn("Impacto", options=["S", "M", "L"]),
        "esfuerzo": st.column_config.SelectboxColumn("Esfuerzo", options=["S", "M", "L"]),
        "semana_inicio": st.column_config.NumberColumn("Semana inicio", min_value=1, max_value=52, step=1),
        "plazo_semanas": st.column_config.NumberColumn("Duración (sem)", min_value=1, max_value=48, step=1),
        "coste_estimado_eur": st.column_config.NumberColumn("Coste (€)", min_value=0.0, max_value=25000.0, step=100.0, format="%.0f"),
        "responsable": st.column_config.SelectboxColumn(
            "Responsable",
            options=["cliente_marketing", "cliente_it", "cliente_comunicacion", "agencia_geo", "externo_pr"],
        ),
        "kpi": st.column_config.TextColumn("KPI"),
    },
    key="editor_acciones_plan",
)

with st.expander("Medición, riesgos y supuestos del plan", icon=":material/fact_check:"):
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

st.write("")
with panel():
    checkpoint_summary(
        "Punto de control 3: plan estratégico",
        "Al aprobar se revalidan presupuesto y capacidad semanal.",
        bool(run.state.get("checkpoints", {}).get("checkpoint_3_plan")),
    )
    comentario_cp3 = st.text_input(
        "Comentario de validación (opcional)",
        value=f"Plan validado dentro del rango {min_b:,.0f} a {max_b:,.0f} € y capacidad <= {CLIENT_WEEKLY_HOURS_CAPACITY:.0f} h/semana.".replace(",", "."),
    )
    aprobar = st.button("Aprobar plan y revalidar restricciones", type="primary", icon=":material/task_alt:", use_container_width=True)

if aprobar:
    orig_by_id = {a.id: a for a in plan.acciones}
    updated_acciones: list[Accion] = []
    for _, row in edited_acc_df.iterrows():
        if not bool(row["Incluir"]):
            continue
        orig = orig_by_id[str(row["id"])]
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
    st.toast(
        f"Punto de control 3 aprobado: {len(validated_plan.acciones)} acciones, {validated_plan.coste_total_eur:,.0f} €.",
        icon=":material/check_circle:",
    )
    st.rerun()

# 5. Simulador what-if
section("Simulador de impacto en el score", "geo/metrics.py")
st.warning(
    f"{DISCLAIMER_SIMULADOR} Recalcula el score espontáneo con la fórmula de `geo/metrics.py` sobre los parámetros que elijas.",
    icon=":material/science:",
)

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

col_s1, col_s2, col_s3 = st.columns(3, gap="large")
with col_s1:
    st.markdown("**Aparición por ciudad**")
    sl_madrid = st.slider("Madrid (%)", 0.0, 100.0, ap_madrid_base, 0.5, key="sim_madrid")
    sl_bcn = st.slider("Barcelona (%)", 0.0, 100.0, ap_bcn_base, 0.5, key="sim_bcn")
with col_s2:
    st.markdown("**Aparición por motor**")
    sl_chatgpt = st.slider("ChatGPT (%)", 0.0, 100.0, ap_chatgpt_base, 0.5, key="sim_chatgpt")
    sl_claude = st.slider("Claude (%)", 0.0, 100.0, ap_claude_base, 0.5, key="sim_claude")
    sl_gemini = st.slider("Gemini (%)", 0.0, 100.0, ap_gemini_base, 0.5, key="sim_gemini")
    sl_perp = st.slider("Perplexity (%)", 0.0, 100.0, ap_perp_base, 0.5, key="sim_perp")
with col_s3:
    st.markdown("**Fuerza y calidad de fuente**")
    sl_fuerza = st.slider("Fuerza media objetivo (0 a 3)", 0.0, 3.0, fuerza_base, 0.05, key="sim_fuerza")
    sl_qual = st.slider("Fuentes de alta calidad (%)", 0.0, 100.0, pct_qual_base, 0.5, key="sim_qual",
                        help="Institucional o medio con calidad >= 0,9.")

cambios_ui = {
    "aparicion_por_ciudad": {"Madrid": sl_madrid / 100.0, "Barcelona": sl_bcn / 100.0},
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

st.write("")
kpi_strip(
    [
        {
            "label": "Score actual",
            "value": f"{sim_res['score_actual']:.2f}",
            "unit": "/ 100",
            "note": f"Puesto actual: {sim_res['puesto_actual']}º de 10",
        },
        {
            "label": "Score simulado",
            "value": f"{sim_res['score_simulado']:.2f}",
            "unit": "/ 100",
            "note": f"{sim_res['delta_score']:+.2f} puntos",
            "chip": "Simulación",
            "chip_kind": "warn",
            "highlight": True,
        },
        {
            "label": "Puesto simulado",
            "value": f"{sim_res['puesto_simulado']}º",
            "unit": "de 10",
            "note": f"{sim_res['delta_puesto']:+d} posiciones" if sim_res["delta_puesto"] != 0 else "Mismo puesto",
        },
        {
            "label": "Aparición espontánea global",
            "value": f"{sim_res['tasa_aparicion_simulada'] * 100:.1f}",
            "unit": "%",
            "note": f"Actual: {sim_res['tasa_aparicion_actual'] * 100:.1f} %",
        },
    ]
)

st.write("")
col_sim_chart, col_sim_rank = st.columns([1.1, 1.0], gap="medium")
with col_sim_chart:
    with panel("Desglose del score", "Actual frente a simulado"):
        comp_act = sim_res["componentes"]["actual"]
        comp_sim = sim_res["componentes"]["simulado"]
        df_comp_plot = pd.DataFrame(
            [
                {"Componente": f"{lab} ({peso})", "Escenario": esc, "Puntos": comp[key]}
                for lab, peso, key in (("Aparición", 30, "aparicion"), ("Posición", 20, "posicion"), ("Fuerza", 30, "fuerza"), ("Fuente", 20, "fuente"))
                for esc, comp in (("Actual", comp_act), ("Simulado", comp_sim))
            ]
        )
        fig_sim = px.bar(
            df_comp_plot,
            x="Componente",
            y="Puntos",
            color="Escenario",
            barmode="group",
            text_auto=".2f",
            color_discrete_map={"Actual": t["lead"], "Simulado": t["accent"]},
            labels={"Componente": ""},
        )
        fig_sim.update_traces(textposition="outside", cliponaxis=False)
        show_fig(fig_sim, 340)

with col_sim_rank:
    with panel("Ranking espontáneo simulado", "n = 240"):
        st.dataframe(sim_res["ranking_simulado"], use_container_width=True, hide_index=True)

if st.button("Usar como objetivo en el plan", icon=":material/flag:"):
    updated_plan_obj = apply_simulation_to_plan_objectives(plan, sim_res)
    run.save_plan(updated_plan_obj)
    st.toast(
        f"Objetivo volcado al plan: score {sim_res['score_actual']:.2f} a {sim_res['score_simulado']:.2f}, "
        f"puesto {sim_res['puesto_actual']}º a {sim_res['puesto_simulado']}º.",
        icon=":material/check_circle:",
    )
    st.rerun()
