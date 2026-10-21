"""Página 1: revisión y confirmación de la ficha del brief (punto de control 0)."""

from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, page_header, panel, section
from geo.intake import ficha_resumen, find_missing_fields

run = get_active_run()
ficha = run.load_ficha()
faltantes = find_missing_fields(ficha)

page_header(
    "Ficha de la marca",
    "Revisa lo que el código extrajo del brief, corrige lo que haga falta y confirma antes de analizar la competencia.",
    checkpoint=0,
    step=1,
)

if faltantes:
    st.warning(
        f"Faltan campos por completar: {', '.join(f'`{f}`' for f in faltantes)}.",
        icon=":material/warning:",
    )
else:
    st.success("Todos los campos clave del brief se han extraído y validado por código.", icon=":material/check_circle:")

col_form, col_summary = st.columns([3, 2], gap="large")

with col_form:
    with st.form("ficha_edit_form", border=False):
        section("Identidad")
        marca = st.text_input("Marca", value=ficha.marca)
        web = st.text_input("Web oficial", value=ficha.web or "")
        c1, c2 = st.columns(2)
        sector = c1.text_input("Sector", value=ficha.sector)
        subsector = c2.text_input("Subsector", value=ficha.subsector or "")

        section("Alcance geográfico y servicios")
        c3, c4, c5 = st.columns(3)
        ciudades_str = c3.text_input("Ciudades", value=", ".join(ficha.ciudades), help="Separadas por coma.")
        ciudad_princ = c4.text_input("Ciudad principal", value=ficha.ciudad_principal or "")
        ciudad_crec = c5.text_input("Ciudad de crecimiento", value=ficha.ciudad_crecimiento or "")
        prio_str = st.text_input(
            "Servicios prioritarios",
            value=", ".join(ficha.servicios_prioritarios),
            help="Separados por coma.",
        )
        dif_str = st.text_area("Diferenciales", value="\n".join(ficha.diferenciales), height=96, help="Uno por línea.")
        comp_str = st.text_input(
            "Competidores declarados en el brief",
            value=", ".join(ficha.competidores_declarados),
            help="Separados por coma.",
        )

        section("Objetivo y presupuesto")
        obj_princ = st.text_area("Objetivo principal", value=ficha.objetivo_principal, height=80)
        b1, b2, b3 = st.columns(3)
        pres_min = b1.number_input("Presupuesto mínimo (€)", value=float(ficha.presupuesto_min_eur or 18000.0), step=1000.0)
        pres_max = b2.number_input("Presupuesto máximo (€)", value=float(ficha.presupuesto_max_eur or 27000.0), step=1000.0)
        horizonte = b3.number_input("Horizonte (meses)", value=int(ficha.horizonte_meses), min_value=3, max_value=24)

        section("Equipo y comunicación")
        equipo = st.text_input("Equipo disponible", value=ficha.equipo)
        audiencia = st.text_input("Audiencia de la propuesta", value=ficha.audiencia)
        tono = st.text_input("Tono", value=ficha.tono)

        submitted = st.form_submit_button(
            "Confirmar ficha y aprobar punto de control 0",
            type="primary",
            icon=":material/task_alt:",
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
            ficha.servicios_prioritarios = [x.strip() for x in prio_str.split(",") if x.strip()]
            ficha.diferenciales = [x.strip() for x in dif_str.splitlines() if x.strip()]
            ficha.competidores_declarados = [x.strip() for x in comp_str.split(",") if x.strip()]
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
            st.success("Punto de control 0 aprobado. Ficha guardada en `ficha.json`.", icon=":material/check_circle:")

with col_summary:
    section("Resumen estructurado")
    with panel():
        st.markdown(ficha_resumen(ficha))
    if ficha.hipotesis_cliente:
        section("Hipótesis del cliente", desc="Lo que el cliente cree antes de ver los datos. Cada una se contrasta en el diagnóstico.")
        for h_cli in ficha.hipotesis_cliente:
            st.info(f"«{h_cli}»", icon=":material/format_quote:")
    if ficha.restricciones_normativas:
        section("Restricciones normativas")
        for r_norm in ficha.restricciones_normativas:
            st.markdown(f"- {r_norm}")
