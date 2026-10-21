"""Página 3: diagnóstico de visibilidad espontánea y asistida, con gráficos y evidencias."""

from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import (
    brand_color_map,
    brand_key,
    scope_style,
    cat_colors,
    evidence_view,
    get_active_run,
    kpi_strip,
    page_header,
    panel,
    section,
    show_fig,
    tokens,
)

run = get_active_run()
ficha = run.load_ficha()
tablas = run.load_tablas()
marca_brief = ficha.marca
t = tokens()

t1_esp = tablas["T1_espontanea"]
t1_asis = tablas["T1_asistida"]
t2 = tablas["T2"]
t4 = tablas["T4"]
t6 = tablas["T6"]
t9 = tablas["T9"]
t10 = tablas["T10"]
t11 = tablas["T11"]

lider_nombre = str(t1_esp.iloc[0]["marca"]) if not t1_esp.empty else "Grupo Hospitalario Valdecruz"
row_esp_b = t1_esp[t1_esp["marca"] == marca_brief].iloc[0]
row_asis_b = t1_asis[t1_asis["marca"] == marca_brief].iloc[0]

page_header(
    "Diagnóstico",
    "Cómo aparece la marca cuando nadie la nombra (espontánea) y qué dicen de ella cuando sí (asistida). Los dos ámbitos nunca se mezclan.",
    step=3,
)

ambito = st.segmented_control(
    "Ámbito de las preguntas",
    options=["Espontánea", "Asistida"],
    default="Espontánea",
    format_func=lambda a: "Espontánea · prompts sin marca" if a == "Espontánea" else "Asistida · prompts con marca",
    selection_mode="single",
    key="ambito_diagnostico",
)
es_espontanea = ambito != "Asistida"
scope_style("Espontánea" if es_espontanea else "Asistida")
st.write("")

if es_espontanea:
    kpi_strip(
        [
            {
                "label": "Score de citación",
                "value": f"{row_esp_b['score']:.2f}",
                "unit": "/ 100",
                "note": f"{row_esp_b['score'] - t1_esp.iloc[0]['score']:.2f} frente al líder ({lider_nombre})",
                "source": "T1 espontánea · n = 240",
                "chip": "Espontánea",
                "chip_kind": "spont",
                "highlight": True,
            },
            {
                "label": "Puesto en el ranking",
                "value": f"{int(row_esp_b['puesto'])}º",
                "unit": f"de {len(t1_esp)}",
                "note": "7º por score (27,97) y 8º por aparición (38,8 %), tras Vistalia (41,2 %).",
                "source": "T1 espontánea · n = 240",
            },
            {
                "label": "Aparición espontánea",
                "value": f"{row_esp_b['tasa_aparicion'] * 100:.1f}",
                "unit": "%",
                "note": "Madrid 54,2 % · Barcelona 4,2 %",
                "source": "T1 y T4 · n = 240 y 24 por ciudad",
            },
            {
                "label": "Recomendación activa",
                "value": f"{row_esp_b['%recomendacion_activa'] * 100:.1f}",
                "unit": "%",
                "note": "Consultas donde el motor la recomienda como primera opción (fuerza 3).",
                "source": "T1 espontánea · n = 240",
            },
        ]
    )
else:
    kpi_strip(
        [
            {
                "label": "Score asistido",
                "value": f"{row_asis_b['score']:.2f}",
                "unit": "/ 100",
                "source": "T1 asistida · n = 108",
                "chip": "Asistida",
                "chip_kind": "assist",
                "highlight": True,
            },
            {
                "label": "Aparición asistida",
                "value": f"{row_asis_b['tasa_aparicion'] * 100:.1f}",
                "unit": "%",
                "note": "Si el prompt nombra la marca, casi siempre aparece. Lo que importa es qué dicen de ella.",
                "source": "T1 asistida · n = 108",
            },
            {
                "label": "Fuerza media en apariciones",
                "value": f"{row_asis_b['fuerza_media_apariciones']:.2f}",
                "unit": "/ 3",
                "source": "T9 y T1 asistida · n = 108",
            },
            {
                "label": "Menciones con advertencias",
                "value": f"{row_asis_b['%negativo'] * 100:.1f}",
                "unit": "%",
                "note": "Fortaleza frente a competidores low cost (34,3 %).",
                "source": "T9 · n = 108",
            },
        ]
    )

if es_espontanea:
    section("Posición frente al mercado")
    c_left, c_right = st.columns(2, gap="medium")

    with c_left:
        with panel("Ranking por score de citación", "T1 · n = 240"):
            brand_key(marca_brief, lider_nombre)
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
                text=df_plot_t1.apply(lambda r: f"{r['score']:.1f}", axis=1),
                labels={"score": "Score de citación (0 a 100)", "marca": ""},
                custom_data=["ap_pct"],
            )
            fig_t1.update_traces(
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Score %{x:.1f}<br>Aparición %{customdata[0]} %<extra></extra>",
            )
            fig_t1.update_xaxes(range=[0, 100])
            show_fig(fig_t1, 400, legend=False)

    with c_right:
        with panel("Aparición por marca y motor", "T2 · % espontáneo · n = 60 por motor"):
            piv_t2 = t2.pivot(index="marca", columns="motor", values="tasa_aparicion") * 100.0
            piv_t2 = piv_t2.loc[t1_esp["marca"].tolist()]
            fig_hm = px.imshow(
                piv_t2.round(1),
                text_auto=".1f",
                aspect="auto",
                color_continuous_scale=[[0, t["sunken"]], [1, t["spont"]]],
                labels=dict(x="", y="", color="% aparición"),
            )
            fig_hm.update_layout(coloraxis_showscale=False)
            fig_hm.update_xaxes(side="top", showgrid=False)
            fig_hm.update_yaxes(showgrid=False)
            show_fig(fig_hm, 400, legend=False)

    section("Embudo y geografía")
    c_emb, c_geo = st.columns(2, gap="medium")

    with c_emb:
        with panel("Embudo de decisión: marca, líder y media", "T11 · % aparición"):
            df_emb = pd.concat(
                [
                    pd.DataFrame({"Fase": t11["intencion"], "Serie": marca_brief, "Aparición (%)": t11["tasa_aparicion_marca"] * 100.0}),
                    pd.DataFrame({"Fase": t11["intencion"], "Serie": "Líder", "Aparición (%)": t11["tasa_aparicion_lider"] * 100.0}),
                    pd.DataFrame({"Fase": t11["intencion"], "Serie": "Media de competidores", "Aparición (%)": t11["tasa_aparicion_media_competidores"] * 100.0}),
                ]
            )
            fig_emb = px.line(
                df_emb,
                x="Fase",
                y="Aparición (%)",
                color="Serie",
                markers=True,
                color_discrete_map={
                    marca_brief: t["accent"],
                    "Líder": t["lead"],
                    "Media de competidores": t["rest"],
                },
            )
            fig_emb.update_traces(line=dict(width=2.5), marker=dict(size=7))
            show_fig(fig_emb, 360)

    with c_geo:
        with panel("Brecha geográfica: Madrid y Barcelona", "T4 · n = 24 por ciudad"):
            t4_focus = t4[
                t4["marca"].isin(
                    [marca_brief, lider_nombre, "Instituto Oftálmico Tramuntana", "Láser Nítida", "Vistalia Oftalmología"]
                )
            ].copy()
            t4_focus["Aparición (%)"] = (t4_focus["tasa_aparicion"] * 100.0).round(1)
            fig_geo = px.bar(
                t4_focus,
                x="Aparición (%)",
                y="marca",
                color="ciudad",
                barmode="group",
                text_auto=".1f",
                orientation="h",
                color_discrete_map={"Madrid": t["line-3"], "Barcelona": t["spont"]},
                labels={"marca": ""},
            )
            fig_geo.update_traces(textposition="outside", cliponaxis=False)
            fig_geo.update_xaxes(range=[0, 115])
            show_fig(fig_geo, 360)

            row_bcn = t4[(t4["marca"] == marca_brief) & (t4["ciudad"] == "Barcelona")]
            if not row_bcn.empty:
                evidence_view(
                    row_bcn.iloc[0]["evidencia_ids"],
                    marca_resaltada=marca_brief,
                    title=f"Ver respuestas de {marca_brief} en Barcelona (4,2 %, n = 24)",
                )

    section("Fuentes y consistencia")
    c_src, c_cons = st.columns(2, gap="medium")
    with c_src:
        with panel("Perfil de fuentes por marca", "T6 · sobre apariciones"):
            t6_plot = t6.copy()
            t6_plot["% apariciones"] = (t6_plot["pct_apariciones"] * 100.0).round(1)
            fig_src = px.bar(
                t6_plot,
                x="% apariciones",
                y="marca",
                color="tipo_fuente",
                orientation="h",
                barmode="stack",
                color_discrete_sequence=cat_colors(),
                labels={"marca": ""},
            )
            show_fig(fig_src, 380)

    with c_cons:
        with panel("Consistencia entre repeticiones", "T10 · 3 repeticiones por prompt"):
            t10_melt = t10.melt(
                id_vars=["marca"],
                value_vars=["%consolidada", "%azar", "%ausente"],
                var_name="Estado",
                value_name="Proporción",
            )
            t10_melt["Porcentaje (%)"] = (t10_melt["Proporción"] * 100.0).round(1)
            t10_melt["Estado"] = t10_melt["Estado"].map(
                {"%consolidada": "Consolidada", "%azar": "Por azar", "%ausente": "Ausente"}
            )
            fig_cons = px.bar(
                t10_melt,
                x="Porcentaje (%)",
                y="marca",
                color="Estado",
                orientation="h",
                barmode="stack",
                color_discrete_map={"Consolidada": t["spont"], "Por azar": t["warn-fill"], "Ausente": t["line-2"]},
                labels={"marca": ""},
            )
            show_fig(fig_cons, 380)

else:
    st.info(
        "En las consultas asistidas el propio prompt nombra a la clínica, así que la aparición ronda el 100 %. "
        "Lo relevante es la fuerza de la recomendación, el sentimiento y las objeciones recurrentes.",
        icon=":material/info:",
    )
    section("Calidad de la mención y objeciones recurrentes", "T9")
    t9_disp = t9[
        ["marca", "n", "tasa_aparicion", "fuerza_media", "%recomendacion_activa", "%negativo", "objeciones_recurrentes"]
    ].copy()
    for c in ("tasa_aparicion", "%recomendacion_activa", "%negativo"):
        t9_disp[c] = (t9_disp[c] * 100).round(1)
    st.dataframe(
        t9_disp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "marca": "Marca",
            "n": st.column_config.NumberColumn("n"),
            "tasa_aparicion": st.column_config.NumberColumn("Aparición", format="%.1f %%"),
            "fuerza_media": st.column_config.NumberColumn("Fuerza media", format="%.2f"),
            "%recomendacion_activa": st.column_config.NumberColumn("Recomendación activa", format="%.1f %%"),
            "%negativo": st.column_config.NumberColumn("Con advertencias", format="%.1f %%"),
            "objeciones_recurrentes": st.column_config.TextColumn("Objeciones recurrentes", width="large"),
        },
    )

    section("Duelos directos uno a uno", "T8 · por par y motor")
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
            title=f"Ver respuestas asistidas de {marca_brief} (T9, n = {int(row_t9_b.iloc[0]['n'])})",
        )
