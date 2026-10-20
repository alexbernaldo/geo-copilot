"""Página 3: Diagnóstico de visibilidad espontánea y asistida con gráficos y evidencias (F13)."""

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
    COLOR_BRIEF,
    COLOR_LIDER,
    COLOR_OTRAS,
    brand_color_map,
    evidence_view,
    get_active_run,
    render_header_banner,
)

st.set_page_config(page_title="3 · Diagnóstico · GEO Copilot", page_icon="📈", layout="wide")
render_header_banner()

run = get_active_run()
ficha = run.load_ficha()
tablas = run.load_tablas()
marca_brief = ficha.marca

t1_esp = tablas["T1_espontanea"]
t1_asis = tablas["T1_asistida"]
t2 = tablas["T2"]
t3_esp = tablas["T3"]
t3_asis = tablas["T3_asistida"]
t4 = tablas["T4"]
t6 = tablas["T6"]
t9 = tablas["T9"]
t10 = tablas["T10"]
t11 = tablas["T11"]

lider_nombre = str(t1_esp.iloc[0]["marca"]) if not t1_esp.empty else "Grupo Hospitalario Valdecruz"
row_esp_b = t1_esp[t1_esp["marca"] == marca_brief].iloc[0]
row_asis_b = t1_asis[t1_asis["marca"] == marca_brief].iloc[0]

st.title(f"3 · Diagnóstico de Visibilidad GEO — {marca_brief}")

# Conmutador principal Espontánea / Asistida
ambito_vista = st.radio(
    "🔎 Selecciona el ámbito de análisis (nunca se mezclan entre sí):",
    options=["Espontánea (prompts sin marca: generico + ciudad)", "Asistida (prompts con marca: marca + par)"],
    horizontal=True,
)
es_espontanea = ambito_vista.startswith("Espontánea")

# KPI Cards con tooltips de origen y n
k1, k2, k3, k4 = st.columns(4)
if es_espontanea:
    k1.metric(
        "Score de Citación Espontáneo",
        f"{row_esp_b['score']:.2f} / 100",
        delta=f"{row_esp_b['score'] - t1_esp.iloc[0]['score']:.2f} vs líder ({lider_nombre})",
        help="Origen: Tabla T1_espontanea · n=240 ejecuciones sin marca.",
    )
    k2.metric(
        "Puesto en Ranking (Score / Aparición)",
        f"{int(row_esp_b['puesto'])}º / 8º de {len(t1_esp)}",
        help="7º por Score (27,97) y 8º por tasa de aparición (38,8 %, por detrás de Vistalia 41,2 %). Origen: T1_espontanea, n=240.",
    )
    k3.metric(
        "% Aparición Espontánea",
        f"{row_esp_b['tasa_aparicion'] * 100:.1f} %",
        delta=f"Barcelona: 4,2 % · Madrid: 54,2 %",
        help="Origen: T1_espontanea (n=240) y T4 (n=24 por ciudad).",
    )
    k4.metric(
        "% Recomendación Activa (Fuerza 3)",
        f"{row_esp_b['%recomendacion_activa'] * 100:.1f} %",
        help="Proporción de consultas espontáneas donde el motor la recomienda como primera opción. Origen: T1_espontanea, n=240.",
    )
else:
    k1.metric(
        "Score Asistido (con marca)",
        f"{row_asis_b['score']:.2f} / 100",
        help="Origen: Tabla T1_asistida · n=108 evaluaciones con marca en el prompt.",
    )
    k2.metric(
        "% Aparición Asistida",
        f"{row_asis_b['tasa_aparicion'] * 100:.1f} %",
        help="Cuando el prompt nombra la marca, aparece casi siempre. Mide qué dicen de ella, no si la descubren. Origen: T1_asistida, n=108.",
    )
    k3.metric(
        "Fuerza Media en Apariciones",
        f"{row_asis_b['fuerza_media_apariciones']:.2f} / 3",
        help="Origen: T9 / T1_asistida · n=108.",
    )
    k4.metric(
        "% Menciones con Advertencias",
        f"{row_asis_b['%negativo'] * 100:.1f} %",
        delta="Fortaleza frente a competidores low cost (34,3 %)",
        help="Origen: Tabla T9 · n=108.",
    )

st.divider()

if es_espontanea:
    c_left, c_right = st.columns(2, gap="large")

    with c_left:
        st.subheader("🏆 Ranking de Marcas por Score Espontáneo (T1, n=240)")
        df_plot_t1 = t1_esp.sort_values("score", ascending=True).copy()
        df_plot_t1["ap_pct"] = (df_plot_t1["tasa_aparicion"] * 100).round(1)
        cmap = brand_color_map(df_plot_t1["marca"].tolist(), marca_brief, lider_nombre)
        fig_t1 = px.bar(
            df_plot_t1,
            x="score",
            y="marca",
            orientation="h",
            color="marca",
            color_discrete_map=cmap,
            text=df_plot_t1.apply(lambda r: f"{r['score']:.1f} pts ({r['ap_pct']:.1f}%)", axis=1),
            labels={"score": "Score de Citación (0-100)", "marca": "Marca"},
        )
        fig_t1.update_layout(showlegend=False, height=400, margin=dict(l=10, r=20, t=20, b=20))
        st.plotly_chart(fig_t1, use_container_width=True)

    with c_right:
        st.subheader("🔥 Heatmap Marca × Motor (% Aparición Espontánea, T2, n=60/motor)")
        piv_t2 = t2.pivot(index="marca", columns="motor", values="tasa_aparicion") * 100.0
        piv_t2 = piv_t2.loc[t1_esp["marca"].tolist()]
        fig_hm = px.imshow(
            piv_t2.round(1),
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="Blues",
            labels=dict(x="Motor", y="Marca", color="% Aparición"),
        )
        fig_hm.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_hm, use_container_width=True)

    c_emb, c_geo = st.columns(2, gap="large")

    with c_emb:
        st.subheader("📉 Embudo de Decisión: Marca vs. Líder y Media (T11)")
        df_emb = pd.DataFrame(
            [
                {
                    "Fase": r["intencion"],
                    "Serie": marca_brief,
                    "Aparición (%)": r["tasa_aparicion_marca"] * 100.0,
                }
                for _, r in t11.iterrows()
            ]
            + [
                {
                    "Fase": r["intencion"],
                    "Serie": f"Líder ({lider_nombre})",
                    "Aparición (%)": r["tasa_aparicion_lider"] * 100.0,
                }
                for _, r in t11.iterrows()
            ]
            + [
                {
                    "Fase": r["intencion"],
                    "Serie": "Media competidores",
                    "Aparición (%)": r["tasa_aparicion_media_competidores"] * 100.0,
                }
                for _, r in t11.iterrows()
            ]
        )
        fig_emb = px.line(
            df_emb,
            x="Fase",
            y="Aparición (%)",
            color="Serie",
            markers=True,
            color_discrete_map={
                marca_brief: COLOR_BRIEF,
                f"Líder ({lider_nombre})": COLOR_LIDER,
                "Media competidores": COLOR_OTRAS,
            },
        )
        fig_emb.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_emb, use_container_width=True)

    with c_geo:
        st.subheader("📍 Brecha Geográfica: Madrid vs. Barcelona (T4, n=24/ciudad)")
        t4_focus = t4[
            t4["marca"].isin(
                [marca_brief, lider_nombre, "Instituto Oftálmico Tramuntana", "Láser Nítida", "Vistalia Oftalmología"]
            )
        ].copy()
        t4_focus["Aparición (%)"] = (t4_focus["tasa_aparicion"] * 100.0).round(1)
        fig_geo = px.bar(
            t4_focus,
            x="marca",
            y="Aparición (%)",
            color="ciudad",
            barmode="group",
            text_auto=".1f",
            color_discrete_map={"Madrid": COLOR_BRIEF, "Barcelona": "#E53E3E"},
        )
        fig_geo.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_geo, use_container_width=True)

        row_bcn = t4[(t4["marca"] == marca_brief) & (t4["ciudad"] == "Barcelona")]
        if not row_bcn.empty:
            evidence_view(
                row_bcn.iloc[0]["evidencia_ids"],
                marca_resaltada=marca_brief,
                title=f"🔎 Ver evidencia de {marca_brief} en Barcelona (4,2 %, n=24)",
            )

    c_src, c_cons = st.columns(2, gap="large")
    with c_src:
        st.subheader("🔗 Perfil de Fuentes por Marca (T6, sobre apariciones)")
        t6_plot = t6.copy()
        t6_plot["% Apariciones"] = (t6_plot["pct_apariciones"] * 100.0).round(1)
        fig_src = px.bar(
            t6_plot,
            x="% Apariciones",
            y="marca",
            color="tipo_fuente",
            orientation="h",
            barmode="stack",
        )
        fig_src.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_src, use_container_width=True)

    with c_cons:
        st.subheader("🎯 Consistencia entre Repeticiones (T10, 3 rep./prompt)")
        t10_melt = t10.melt(
            id_vars=["marca"],
            value_vars=["%consolidada", "%azar", "%ausente"],
            var_name="Estado",
            value_name="Proporción",
        )
        t10_melt["Porcentaje (%)"] = (t10_melt["Proporción"] * 100.0).round(1)
        fig_cons = px.bar(
            t10_melt,
            x="Porcentaje (%)",
            y="marca",
            color="Estado",
            orientation="h",
            barmode="stack",
            color_discrete_map={
                "%consolidada": COLOR_BRIEF,
                "%azar": "#ECC94B",
                "%ausente": "#E2E8F0",
            },
        )
        fig_cons.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_cons, use_container_width=True)

else:
    st.info(
        "💡 **Nota metodológica:** En las consultas **asistidas** (`marca` y `par`), el propio prompt nombra a la clínica. "
        "Por eso la tasa de aparición es cercana al 100 % y lo relevante es **la fuerza de recomendación, el sentimiento y las objeciones recurrentes**."
    )
    st.subheader("💬 Calidad de la Mención Asistida y Objeciones Recurrentes (T9)")
    t9_disp = t9[
        [
            "marca",
            "n",
            "tasa_aparicion",
            "fuerza_media",
            "%recomendacion_activa",
            "%negativo",
            "objeciones_recurrentes",
        ]
    ].copy()
    t9_disp["tasa_aparicion"] = (t9_disp["tasa_aparicion"] * 100).round(1)
    t9_disp["%recomendacion_activa"] = (t9_disp["%recomendacion_activa"] * 100).round(1)
    t9_disp["%negativo"] = (t9_disp["%negativo"] * 100).round(1)
    st.dataframe(t9_disp, use_container_width=True, hide_index=True)

    st.subheader("🥊 Duelos Directos 1 a 1 por Par y Motor (T8)")
    st.dataframe(
        tablas["T8"].drop(columns=["evidencia_ids"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
    )

    row_t9_b = t9[t9["marca"] == marca_brief]
    if not row_t9_b.empty:
        evidence_view(
            row_t9_b.iloc[0]["evidencia_ids"],
            marca_resaltada=marca_brief,
            title=f"🔎 Ver evidencias asistidas de {marca_brief} (T9, n={int(row_t9_b.iloc[0]['n'])})",
        )
