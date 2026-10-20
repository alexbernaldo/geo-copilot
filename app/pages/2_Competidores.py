"""Página 2: Contraste de mercado y competidores (Checkpoint 1) (F13)."""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, render_header_banner
from geo.schemas import MarcaMercado

st.set_page_config(page_title="2 · Competidores · GEO Copilot", page_icon="🏢", layout="wide")
render_header_banner()

run = get_active_run()
market = run.load_market()
ficha = run.load_ficha()

st.title("2 · Mapa del Mercado y Contraste Brief vs. Datos (Checkpoint 1)")
st.markdown(
    "Contraste automático entre los competidores declarados por el cliente en el brief y los actores que "
    "realmente aparecen en las **240 consultas espontáneas** (`T1_espontanea`, `n=240`)."
)

st.subheader("🚨 Discrepancias detectadas entre el Brief y los Datos")
for disc in market.discrepancias_brief:
    st.warning(f"🔍 {disc}")

st.subheader("📊 Tabla de marcas del sector (editable para revisión humana)")
df_m = pd.DataFrame([m.model_dump() for m in market.marcas])
df_m["aparicion_espontanea_%"] = (df_m["tasa_aparicion_espontanea"] * 100.0).round(1)

edited_df = st.data_editor(
    df_m[
        [
            "nombre",
            "rol",
            "declarada_en_brief",
            "detectada_en_datos",
            "aparicion_espontanea_%",
            "nota",
        ]
    ],
    column_config={
        "nombre": st.column_config.TextColumn("Marca", disabled=True),
        "rol": st.column_config.SelectboxColumn(
            "Rol en el estudio",
            options=["marca_brief", "lider", "competidor_directo", "referencia", "contexto"],
            required=True,
        ),
        "declarada_en_brief": st.column_config.CheckboxColumn("Declarada en Brief"),
        "detectada_en_datos": st.column_config.CheckboxColumn("Detectada en Datos", disabled=True),
        "aparicion_espontanea_%": st.column_config.NumberColumn(
            "% Aparición espontánea (n=240)",
            format="%.1f %%",
            disabled=True,
        ),
        "nota": st.column_config.TextColumn("Nota diagnóstica"),
    },
    use_container_width=True,
    hide_index=True,
)

if st.button(
    "✅ Aprobar Mapa de Competidores (Checkpoint 1)",
    type="primary",
    use_container_width=True,
):
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
    st.success("✅ Checkpoint 1 aprobado y persistido en `market.json`.")
