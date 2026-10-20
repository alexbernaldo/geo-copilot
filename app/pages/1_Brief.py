"""Página 1: Revisión y confirmación del Brief (Checkpoint 0) (F13)."""

from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, render_header_banner
from geo.intake import ficha_resumen, find_missing_fields

st.set_page_config(page_title="1 · Brief · GEO Copilot", page_icon="📄", layout="wide")
render_header_banner()

run = get_active_run()
ficha = run.load_ficha()
faltantes = find_missing_fields(ficha)

st.title("1 · Intake del Brief y Ficha de Marca (Checkpoint 0)")
if faltantes:
    st.warning(
        f"⚠️ **Campos pendientes de completar por el consultor:** `{', '.join(faltantes)}`"
    )
else:
    st.success("✅ Todos los campos clave del brief han sido extraídos y validados por código.")

col_form, col_summary = st.columns([3, 2], gap="large")

with col_form:
    with st.form("ficha_edit_form"):
        st.subheader("✏️ Formulario editable de FichaMarca")
        marca = st.text_input("Marca", value=ficha.marca)
        web = st.text_input("Web oficial", value=ficha.web or "")
        c1, c2 = st.columns(2)
        sector = c1.text_input("Sector", value=ficha.sector)
        subsector = c2.text_input("Subsector", value=ficha.subsector or "")

        c3, c4, c5 = st.columns(3)
        ciudades_str = c3.text_input(
            "Ciudades (separadas por coma)", value=", ".join(ficha.ciudades)
        )
        ciudad_princ = c4.text_input(
            "Ciudad principal", value=ficha.ciudad_principal or ""
        )
        ciudad_crec = c5.text_input(
            "Ciudad de crecimiento", value=ficha.ciudad_crecimiento or ""
        )

        prio_str = st.text_input(
            "Servicios prioritarios (separados por coma)",
            value=", ".join(ficha.servicios_prioritarios),
        )
        dif_str = st.text_area(
            "Diferenciales (uno por línea)",
            value="\n".join(ficha.diferenciales),
            height=90,
        )
        comp_str = st.text_input(
            "Competidores declarados en el brief (separados por coma)",
            value=", ".join(ficha.competidores_declarados),
        )
        obj_princ = st.text_area(
            "Objetivo principal", value=ficha.objetivo_principal, height=70
        )

        b1, b2, b3 = st.columns(3)
        pres_min = b1.number_input(
            "Presupuesto mínimo (€)",
            value=float(ficha.presupuesto_min_eur or 18000.0),
            step=1000.0,
        )
        pres_max = b2.number_input(
            "Presupuesto máximo (€)",
            value=float(ficha.presupuesto_max_eur or 27000.0),
            step=1000.0,
        )
        horizonte = b3.number_input(
            "Horizonte (meses)", value=int(ficha.horizonte_meses), min_value=3, max_value=24
        )

        equipo = st.text_input("Equipo disponible", value=ficha.equipo)
        audiencia = st.text_input("Audiencia de la propuesta", value=ficha.audiencia)
        tono = st.text_input("Tono", value=ficha.tono)

        submitted = st.form_submit_button(
            "💾 Confirmar FichaMarca (Aprobar Checkpoint 0)",
            type="primary",
            use_container_width=True,
        )
        if submitted:
            ficha.marca = marca.strip()
            ficha.web = web.strip() or None
            ficha.sector = sector.strip()
            ficha.subsector = subsector.strip() or None
            ficha.ciudades = [x.strip() for x in ciudades_str.split(",") if x.strip()]
            ficha.ciudad_principal = ciudad_princ.strip() or None
            ficha.ciudad_crecimiento = ciudad_crec.strip() or None
            ficha.servicios_prioritarios = [
                x.strip() for x in prio_str.split(",") if x.strip()
            ]
            ficha.diferenciales = [
                x.strip() for x in dif_str.splitlines() if x.strip()
            ]
            ficha.competidores_declarados = [
                x.strip() for x in comp_str.split(",") if x.strip()
            ]
            ficha.objetivo_principal = obj_princ.strip()
            ficha.presupuesto_min_eur = float(pres_min)
            ficha.presupuesto_max_eur = float(pres_max)
            ficha.horizonte_meses = int(horizonte)
            ficha.equipo = equipo.strip()
            ficha.audiencia = audiencia.strip()
            ficha.tono = tono.strip()

            run.save_ficha(ficha)
            run.approve_checkpoint(
                "checkpoint_0_brief",
                note="FichaMarca revisada y confirmada en Página 1.",
            )
            st.success("✅ Checkpoint 0 aprobado y guardado en `ficha.json`.")

with col_summary:
    st.subheader("📌 Resumen estructurado")
    st.markdown(ficha_resumen(ficha))
    st.markdown("#### Hipótesis del cliente extraídas")
    for h_cli in ficha.hipotesis_cliente:
        st.info(f"💬 «{h_cli}»")
    st.markdown("#### Restricciones normativas")
    for r_norm in ficha.restricciones_normativas:
        st.caption(f"⚖️ {r_norm}")
