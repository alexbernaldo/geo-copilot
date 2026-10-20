"""Componentes compartidos de interfaz, banner sintético, paleta de colores y visor de evidencias (F13)."""

from pathlib import Path
import re
import sys
from typing import Sequence
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.config import BRIEF_MD, RUNS_DIR
from geo.loader import load_ejecuciones, load_marcas
from geo.orchestrator import Run

# Paleta consistente en toda la aplicación
COLOR_BRIEF: str = "#0B5FFF"   # Azul destacado para la marca del brief
COLOR_LIDER: str = "#2C3E50"   # Gris oscuro para el líder real del mercado
COLOR_OTRAS: str = "#A0AEC0"   # Gris neutro para el resto de competidores


def brand_color_map(
    marcas_nombres: Sequence[str],
    marca_brief: str = "Clínica Alborada Visión",
    lider: str = "Grupo Hospitalario Valdecruz",
) -> dict[str, str]:
    """Devuelve un diccionario `marca -> color hex` manteniendo siempre el mismo color para la marca del brief y el líder."""
    cmap: dict[str, str] = {}
    for m in marcas_nombres:
        if m == marca_brief:
            cmap[m] = COLOR_BRIEF
        elif m == lider:
            cmap[m] = COLOR_LIDER
        else:
            cmap[m] = COLOR_OTRAS
    return cmap


def render_header_banner() -> None:
    """Muestra el banner fijo superior de datos sintéticos y el estado del run activo en la barra lateral."""
    st.info(
        "📌 **Datos sintéticos del kit UFV-EPS × reload.** · No representan el comportamiento real en producción de ningún LLM ni clínica sanitaria."
    )
    with st.sidebar:
        st.markdown("### 🧭 GEO Copilot")
        run_id = st.session_state.get("active_run_id", "demo")
        st.caption(f"**Run activo:** `{run_id}`")
        if st.button("⚡ Cargar Modo Demo (`runs/demo/`)", use_container_width=True):
            ensure_demo_run_ready()
            st.session_state["active_run_id"] = "demo"
            st.rerun()


def ensure_demo_run_ready() -> Run:
    """Asegura que `runs/demo/` exista y tenga todos los pasos ejecutados en modo mock."""
    demo_run = Run(run_id="demo", modo="cliente", brief_path=BRIEF_MD, provider="mock")
    if not (demo_run.run_dir / "propuesta.json").exists():
        demo_run.run_all(auto_approve=True, force=False)
    return demo_run


def get_active_run() -> Run:
    """Devuelve el objeto `Run` actualmente seleccionado en `st.session_state` (por defecto `demo`)."""
    run_id = st.session_state.get("active_run_id", "demo")
    run_dir = RUNS_DIR / str(run_id)
    if not run_dir.exists() or not (run_dir / "ficha.json").exists():
        return ensure_demo_run_ready()
    return Run(run_id=str(run_id))


@st.cache_data(show_spinner=False)
def cached_ejecuciones_df() -> pd.DataFrame:
    """Carga en caché el DataFrame de las 624 ejecuciones para el visor de evidencias."""
    return load_ejecuciones()


@st.cache_data(show_spinner=False)
def cached_marcas_aliases() -> dict[str, list[str]]:
    """Devuelve `nombre_marca -> [nombre, *alias]` para resaltar menciones en el texto."""
    return {m.nombre: [m.nombre, *m.alias] for m in load_marcas()}


def highlight_brand_in_text(text: str, marca_nombre: str) -> str:
    """Resalta en negrita/color las apariciones de `marca_nombre` y sus alias dentro del texto de una respuesta."""
    aliases_map = cached_marcas_aliases()
    terms = sorted(aliases_map.get(marca_nombre, [marca_nombre]), key=len, reverse=True)
    out = text
    for term in terms:
        pat = re.compile(rf"(\b{re.escape(term)}\b)", flags=re.IGNORECASE)
        out = pat.sub(r":blue-background[**\1**]", out)
    return out


def evidence_view(
    ejecucion_ids: Sequence[str],
    marca_resaltada: str = "Clínica Alborada Visión",
    *,
    title: str = "🔎 Ver evidencia en respuestas originales",
    max_items: int = 5,
) -> None:
    """Componente reutilizable que muestra las ejecuciones originales con prompt, motor, fuentes y marca resaltada."""
    ids_list = [str(x) for x in ejecucion_ids if str(x)][:max_items]
    if not ids_list:
        st.caption("Sin ejecuciones asociadas.")
        return

    df_ej = cached_ejecuciones_df()
    sub = df_ej[df_ej["ejecucion_id"].isin(ids_list)]

    with st.expander(f"{title} ({len(ids_list)} ejecuciones: {', '.join(ids_list[:3])}{'…' if len(ids_list) > 3 else ''})"):
        for _, row in sub.iterrows():
            fuentes_str = ", ".join(row["fuentes"]) if row["fuentes"] else "Sin fuentes citadas (sin búsqueda web)"
            ambito_tag = "Espontánea" if row["espontanea"] else "Asistida"
            st.markdown(
                f"**`{row['ejecucion_id']}`** · **Motor:** `{row['motor']}` (Rep. {row['repeticion']}) · "
                f"**Intención:** `{row['intencion']}` (`{row['familia']}`) · **Ámbito:** `{ambito_tag}`"
            )
            st.caption(f"**Prompt ejecutado:** {row['prompt_ejecutado']}  \n**Fuentes citadas:** `{fuentes_str}`")
            st.markdown(highlight_brand_in_text(str(row["respuesta"]), marca_resaltada))
            st.divider()
