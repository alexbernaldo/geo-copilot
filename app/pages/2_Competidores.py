"""Página 2: contraste de mercado y competidores (punto de control 1)."""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import checkpoint_summary, get_active_run, page_header, panel, section
from geo.schemas import MarcaMercado

run = get_active_run()
market = run.load_market()
ficha = run.load_ficha()

page_header(
    "Competencia",
    "Contraste entre los competidores que declara el cliente y los actores que de verdad aparecen en las 240 consultas espontáneas.",
    checkpoint=1,
    step=2,
)

section("Discrepancias entre el brief y los datos", "T1 espontánea · n = 240")
if market.discrepancias_brief:
    for disc in market.discrepancias_brief:
        st.warning(disc, icon=":material/difference:")
else:
    st.success("El brief y los datos coinciden: no hay discrepancias.", icon=":material/check_circle:")

section(
    "Mapa de marcas del sector",
    "Editable por la persona revisora",
    "Ajusta el rol de cada marca. La aparición espontánea la calcula el código y no se puede editar.",
)
df_m = pd.DataFrame([m.model_dump() for m in market.marcas])
df_m["aparicion_espontanea_%"] = (df_m["tasa_aparicion_espontanea"] * 100.0).round(1)

edited_df = st.data_editor(
    df_m[["nombre", "rol", "declarada_en_brief", "detectada_en_datos", "aparicion_espontanea_%", "nota"]],
    column_config={
        "nombre": st.column_config.TextColumn("Marca", disabled=True),
        "rol": st.column_config.SelectboxColumn(
            "Rol en el estudio",
            options=["marca_brief", "lider", "competidor_directo", "referencia", "contexto"],
            required=True,
        ),
        "declarada_en_brief": st.column_config.CheckboxColumn("Declarada en brief"),
        "detectada_en_datos": st.column_config.CheckboxColumn("Detectada en datos", disabled=True),
        "aparicion_espontanea_%": st.column_config.ProgressColumn(
            "Aparición espontánea",
            format="%.1f %%",
            min_value=0,
            max_value=100,
            help="n = 240",
        ),
        "nota": st.column_config.TextColumn("Nota diagnóstica", width="large"),
    },
    use_container_width=True,
    hide_index=True,
)

st.write("")
with panel():
    checkpoint_summary(
        "Punto de control 1: mapa de competidores",
        "Al aprobar, el mapa y las discrepancias se guardan en `market.json`.",
        bool(market.aprobado_por_humano),
    )
    if st.button("Aprobar mapa de competidores", type="primary", icon=":material/task_alt:", use_container_width=True):
        updated_marcas: list[MarcaMercado] = []
        for idx, row in edited_df.iterrows():
            orig_tasa = float(df_m.loc[idx, "tasa_aparicion_espontanea"])
            updated_marcas.append(
                MarcaMercado(
                    nombre=str(row["nombre"]),
                    rol=str(row["rol"]),  # type: ignore[arg-type]
                    declarada_en_brief=bool(row["declarada_en_brief"]),
                    detectada_en_datos=bool(row["detectada_en_datos"]),
                    tasa_aparicion_espontanea=orig_tasa,
                    nota=str(row["nota"]),
                )
            )
        market.marcas = updated_marcas
        market.aprobado_por_humano = True
        run.save_market(market)
        run.approve_checkpoint(
            "checkpoint_1_competidores",
            note="Mapa de competidores y discrepancias aprobado en Página 2.",
        )
        st.toast("Punto de control 1 aprobado.", icon=":material/check_circle:")
        st.rerun()
