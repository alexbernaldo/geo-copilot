"""Punto de entrada de GEO Copilot: navegación y marco común de la interfaz."""

from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import LOGO_PATH, shell

st.set_page_config(
    page_title="GEO Copilot",
    page_icon=str(LOGO_PATH),
    layout="wide",
)

pages = {
    "": [st.Page("pages/0_Inicio.py", title="Inicio", icon=":material/home:", default=True)],
    "Análisis": [
        st.Page("pages/1_Brief.py", title="Ficha", icon=":material/assignment:", url_path="ficha"),
        st.Page("pages/2_Competidores.py", title="Competencia", icon=":material/groups:", url_path="competencia"),
        st.Page("pages/3_Diagnostico.py", title="Diagnóstico", icon=":material/monitoring:", url_path="diagnostico"),
        st.Page("pages/4_Hallazgos.py", title="Hallazgos", icon=":material/lightbulb:", url_path="hallazgos"),
    ],
    "Estrategia": [
        st.Page("pages/5_Plan.py", title="Plan", icon=":material/route:", url_path="plan"),
        st.Page("pages/6_Propuesta.py", title="Propuesta", icon=":material/description:", url_path="propuesta"),
    ],
    "Control": [
        st.Page("pages/7_Calidad_y_trazas.py", title="Calidad y trazas", icon=":material/verified:", url_path="calidad"),
    ],
}

page = st.navigation(pages, position="sidebar")
shell()
page.run()
