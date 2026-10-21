"""Sistema de diseño y componentes compartidos de GEO Copilot.

Estación de trabajo de auditoría: neutros fríos, un único acento (el color de la marca
analizada), tipografía Geist servida en local y tokens claro/oscuro. Los componentes
combinan widgets nativos de Streamlit con HTML mínimo y accesible.
"""
from __future__ import annotations

from contextlib import contextmanager
from html import escape
from pathlib import Path
import re
import sys
from typing import Any, Iterator, Sequence

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.config import BRIEF_MD, RUNS_DIR
from geo.loader import load_ejecuciones, load_marcas
from geo.orchestrator import Run

APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "assets" / "logo.svg"

# ---------------------------------------------------------------------------
# Tokens (claro / oscuro). Un acento: el color de la marca analizada.
# ---------------------------------------------------------------------------
LIGHT: dict[str, str] = {
    "bg": "#F6F7F9", "surface": "#FFFFFF", "sunken": "#EEF0F3", "side": "#F0F2F5",
    "line-1": "#E4E7EC", "line-2": "#D5D9E0", "line-3": "#98A0AE",
    "ink": "#0E1116", "ink-2": "#4A5160", "ink-3": "#667085", "ink-4": "#A3AAB7", "on-ink": "#FFFFFF",
    "accent": "#E8590C", "accent-fg": "#B8460A", "accent-bg": "#FFF1E8",
    "lead": "#0E1116", "rest": "#B4BAC6",
    "spont": "#0B6B75", "spont-bg": "#E3F4F5",
    "assist": "#5B46A0", "assist-bg": "#EEEBFA",
    "good": "#17703A", "good-bg": "#E4F4EA",
    "bad": "#A3173B", "bad-bg": "#FCE9ED",
    "warn": "#8A5A00", "warn-bg": "#FFF4D9", "warn-fill": "#D69300",
    "err": "#B42318", "err-bg": "#FDECEA",
    "human": "#1E4FA3", "human-bg": "#E6EEFB",
    "ai": "#8A5524", "ai-bg": "#FAF0E4",
    "code": "#3A3F47", "code-bg": "#ECEDEF",
    "shadow": "0 1px 2px rgba(14,17,22,.05), 0 1px 1px rgba(14,17,22,.03)",
    "shadow-hover": "0 4px 14px rgba(14,17,22,.08)",
}
DARK: dict[str, str] = {
    "bg": "#0C0E12", "surface": "#14171C", "sunken": "#1B1F26", "side": "#101318",
    "line-1": "#232831", "line-2": "#2E343F", "line-3": "#5A6272",
    "ink": "#ECEEF2", "ink-2": "#B4BAC6", "ink-3": "#8E96A5", "ink-4": "#5A6272", "on-ink": "#0E1116",
    "accent": "#F26B1D", "accent-fg": "#FF9966", "accent-bg": "#3A1D10",
    "lead": "#ECEEF2", "rest": "#4A5160",
    "spont": "#5CCBD6", "spont-bg": "#0F2E32",
    "assist": "#B3A3F2", "assist-bg": "#231E3F",
    "good": "#5FD38A", "good-bg": "#10301D",
    "bad": "#FF8FA8", "bad-bg": "#3A1420",
    "warn": "#F2C25A", "warn-bg": "#33270A", "warn-fill": "#F2C25A",
    "err": "#FF8A80", "err-bg": "#3A1512",
    "human": "#8AB4FF", "human-bg": "#14233F",
    "ai": "#E0A869", "ai-bg": "#33200E",
    "code": "#B4BAC6", "code-bg": "#1B1F26",
    "shadow": "0 1px 2px rgba(0,0,0,.4)",
    "shadow-hover": "0 4px 14px rgba(0,0,0,.45)",
}

# Categorías neutras para gráficos con muchas series (distinguibles en ambos temas)
CAT_LIGHT = ["#2F6FEB", "#0B6B75", "#8A5524", "#5B46A0", "#7A8497", "#B8860B"]
CAT_DARK = ["#6C9CFF", "#5CCBD6", "#E0A869", "#B3A3F2", "#8E96A5", "#E5C15D"]

# Alias estáticos (tema claro) para compatibilidad
COLOR_BRIEF: str = LIGHT["accent"]
COLOR_LIDER: str = LIGHT["lead"]
COLOR_OTRAS: str = LIGHT["rest"]


def theme_name() -> str:
    """Tema activo de Streamlit ('light' u 'dark')."""
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def tokens() -> dict[str, str]:
    return DARK if theme_name() == "dark" else LIGHT


def cat_colors() -> list[str]:
    return CAT_DARK if theme_name() == "dark" else CAT_LIGHT


def brand_color_map(
    marcas_nombres: Sequence[str],
    marca_brief: str = "Clínica Alborada Visión",
    lider: str = "Grupo Hospitalario Valdecruz",
) -> dict[str, str]:
    t = tokens()
    return {
        m: t["accent"] if m == marca_brief else (t["lead"] if m == lider else t["rest"])
        for m in marcas_nombres
    }


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_CSS = """
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --r-s: 6px; --r-m: 8px; --r-l: 12px;
}
html { -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }
.stApp { background: var(--bg); color: var(--ink); font-variant-numeric: tabular-nums; }
::selection { background: var(--accent-bg); color: var(--ink); }
input, textarea { caret-color: var(--accent); }
:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; border-radius: var(--r-s); }
a { text-underline-offset: 3px; }

/* Lienzo */
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1240px; padding: 1.25rem 2.5rem 4rem; }
@media (max-width: 760px) { [data-testid="stMainBlockContainer"] { padding: 3.5rem 1rem 3rem; } }

/* Barra lateral: segunda capa neutra */
[data-testid="stSidebar"] { background: var(--side); border-right: 1px solid var(--line-1); }
[data-testid="stSidebarHeader"] { padding: 1.1rem 1rem .4rem; align-items: center; }
[data-testid="stSidebarHeader"] > :first-child { display: flex; align-items: center; gap: 10px; }
[data-testid="stSidebarHeader"] > :first-child::after { content: "GEO Copilot"; font-weight: 600; font-size: 15px; letter-spacing: -.01em; color: var(--ink); }
[data-testid="stSidebarHeader"] img { height: 28px; width: 28px; }
[data-testid="stSidebarNavLink"] {
  border-radius: var(--r-m); padding: .3rem .65rem; color: var(--ink-2); font-size: 14px; font-weight: 500;
  transition: background-color 120ms var(--ease-out), color 120ms var(--ease-out);
}
[data-testid="stSidebarNavLink"][aria-current="page"] { background: var(--surface); color: var(--ink); font-weight: 600; box-shadow: var(--shadow), inset 0 0 0 1px var(--line-1); }
@media (hover: hover) and (pointer: fine) { [data-testid="stSidebarNavLink"]:hover { background: var(--sunken); color: var(--ink); } }
[data-testid="stNavSectionHeader"] { color: var(--ink-3); font-size: 12px; font-weight: 500; }

/* Tarjeta de análisis activo */
.geo-run { margin: .5rem 0 .5rem; padding: 14px; background: var(--surface); border: 1px solid var(--line-1); border-radius: var(--r-l); }
.geo-run .name { font-weight: 600; font-size: 14px; line-height: 1.3; color: var(--ink); }
.geo-run .meta { margin-top: 2px; font-size: 12px; color: var(--ink-3); font-family: var(--font-mono, 'Geist Mono', monospace); }
.geo-run .cps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; margin-top: 12px; }
.geo-run .cps i { height: 4px; border-radius: 2px; background: var(--line-2); display: block; }
.geo-run .cps i.on { background: var(--human); }
.geo-run .cpl { margin-top: 6px; font-size: 12px; color: var(--ink-2); }

/* Aviso de datos sintéticos */
.geo-notice { display: flex; gap: 8px; align-items: baseline; padding: 6px 12px; margin-bottom: 18px; border-radius: var(--r-m);
  background: var(--warn-bg); color: var(--warn); font-size: 12.5px; line-height: 1.45; }
.geo-notice b { font-weight: 600; }

/* Cabecera de página */
.geo-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; margin: 4px 0 24px; flex-wrap: wrap; }
.geo-head h1 { font-size: 30px; line-height: 1.15; font-weight: 650; letter-spacing: -.025em; margin: 0; padding: 0; color: var(--ink); }
.geo-head p { margin: 8px 0 0; max-width: 68ch; font-size: 15px; line-height: 1.55; color: var(--ink-2); }
.geo-head .side { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; padding-top: 6px; }

/* Chips y estados */
.geo-chip { display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 500; line-height: 1.4;
  background: var(--sunken); color: var(--ink-2); border: 1px solid var(--line-1); white-space: nowrap; }
.geo-chip.dot::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.geo-chip.human { background: var(--human-bg); color: var(--human); border-color: transparent; }
.geo-chip.warn { background: var(--warn-bg); color: var(--warn); border-color: transparent; }
.geo-chip.good { background: var(--good-bg); color: var(--good); border-color: transparent; }
.geo-chip.bad { background: var(--bad-bg); color: var(--bad); border-color: transparent; }
.geo-chip.err { background: var(--err-bg); color: var(--err); border-color: transparent; }
.geo-chip.spont { background: var(--spont-bg); color: var(--spont); border-color: transparent; }
.geo-chip.assist { background: var(--assist-bg); color: var(--assist); border-color: transparent; }
.geo-chip.accent { background: var(--accent-bg); color: var(--accent-fg); border-color: transparent; }
.geo-origin { display: inline-flex; align-items: center; padding: 1px 7px; border-radius: var(--r-s); font-size: 11px; font-weight: 500; }
.geo-origin.code { background: var(--code-bg); color: var(--code); border: 1px solid var(--line-2); }
.geo-origin.ai { background: var(--ai-bg); color: var(--ai); border: 1px dashed var(--ai); }
.geo-origin.human { background: var(--human-bg); color: var(--human); border: 1px solid var(--human); }

/* Secciones */
.geo-sec { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin: 32px 0 12px; }
.geo-sec h2 { font-size: 18px; line-height: 1.3; font-weight: 600; letter-spacing: -.015em; margin: 0; padding: 0; }
.geo-sec .src { font-family: var(--font-mono, 'Geist Mono', monospace); font-size: 12px; color: var(--ink-3); text-align: right; }
.geo-desc { margin: -6px 0 14px; max-width: 70ch; font-size: 14px; color: var(--ink-2); line-height: 1.55; }
.geo-sec { margin-bottom: 14px; }

/* Recorrido: filas con filete, sin huecos verticales */
.st-key-journey { gap: 0 !important; padding: 4px 16px; }
[class*="st-key-jrow_"] { padding: 10px 0; border-bottom: 1px solid var(--line-1); }
[class*="st-key-jrow_"]:last-child { border-bottom: 0; }
[class*="st-key-jrow_"] [data-testid="stCaptionContainer"] { font-size: 13.5px; }

/* Clave de color de gráficos */
.geo-key { display: flex; gap: 14px; flex-wrap: wrap; margin: 0 0 6px; font-size: 12px; color: var(--ink-2); }
.geo-key span { display: inline-flex; align-items: center; gap: 6px; }
.geo-key i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }

/* Lista de filas con filetes */
.geo-list { margin: 0; padding: 0; list-style: none; }
.geo-list li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 9px 2px; font-size: 14px; border-bottom: 1px solid var(--line-1); }
.geo-list li:last-child { border-bottom: 0; }

/* Paneles (contenedores con borde) */
[class*="st-key-panel_"], [class*="st-key-finding_"], .st-key-journey {
  background: var(--surface); border: 1px solid var(--line-1) !important; border-radius: var(--r-l) !important; box-shadow: var(--shadow);
}
[class*="st-key-panel_"] > div, [class*="st-key-finding_"] > div { padding: 4px 4px; }
.geo-panel-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 4px; }
.geo-panel-head .t { font-weight: 600; font-size: 14.5px; letter-spacing: -.01em; }
.geo-panel-head .src { font-family: var(--font-mono, 'Geist Mono', monospace); font-size: 11.5px; color: var(--ink-3); }

/* Tira de indicadores: un solo bloque con celdas separadas por filetes */
.geo-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); background: var(--surface);
  border: 1px solid var(--line-1); border-radius: var(--r-l); box-shadow: var(--shadow); overflow: hidden; }
.geo-kpis .k { padding: 18px 20px 16px; display: flex; flex-direction: column; gap: 3px; border-left: 1px solid var(--line-1); min-width: 0; }
.geo-kpis .k:first-child { border-left: 0; }
.geo-kpis .l { font-size: 13px; font-weight: 500; color: var(--ink-2); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.geo-kpis .v { font-size: 30px; line-height: 1.1; font-weight: 600; letter-spacing: -.03em; color: var(--ink); margin-top: 4px; }
.geo-kpis .v .u { font-size: 14px; font-weight: 500; letter-spacing: 0; color: var(--ink-3); margin-left: 4px; }
.geo-kpis .n { font-size: 12.5px; color: var(--ink-2); line-height: 1.4; }
.geo-kpis .s { margin-top: auto; padding-top: 8px; font-family: var(--font-mono, 'Geist Mono', monospace); font-size: 11px; color: var(--ink-3); }
.geo-kpis .k.hl .v { color: var(--accent-fg); }
@media (max-width: 760px) { .geo-kpis .k { border-left: 0; border-top: 1px solid var(--line-1); } .geo-kpis .k:first-child { border-top: 0; } }

/* Hallazgos */
.geo-find { display: grid; grid-template-columns: 148px 1fr; gap: 20px; padding: 12px 14px 4px; }
.geo-find .fig { background: var(--sunken); border-radius: var(--r-m); padding: 14px 12px; text-align: left; align-self: start; }
.geo-find .fig .num { font-size: 26px; font-weight: 600; letter-spacing: -.03em; line-height: 1.1; }
.geo-find .fig .org { margin-top: 6px; font-family: var(--font-mono, 'Geist Mono', monospace); font-size: 11px; color: var(--ink-3); line-height: 1.4; }
.geo-find .top { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.geo-find .fid { font-family: var(--font-mono, 'Geist Mono', monospace); font-size: 12px; color: var(--ink-3); }
.geo-find h3 { font-size: 17px; font-weight: 600; letter-spacing: -.015em; line-height: 1.3; margin: 8px 0 6px; padding: 0; }
.geo-find p { margin: 0; font-size: 14px; line-height: 1.55; color: var(--ink-2); max-width: 70ch; }
.geo-find dl { display: flex; gap: 6px 22px; flex-wrap: wrap; margin: 12px 0 0; font-size: 12.5px; }
.geo-find dt { color: var(--ink-3); display: inline; }
.geo-find dd { display: inline; margin: 0 0 0 5px; color: var(--ink); font-weight: 500; }
@media (max-width: 760px) { .geo-find { grid-template-columns: 1fr; } }

/* Sello del revisor */
.geo-seal { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; padding: 18px 22px; background: var(--surface);
  border: 1px solid var(--line-1); border-radius: var(--r-l); box-shadow: var(--shadow); margin-bottom: 20px; }
.geo-seal .c { font-size: 22px; font-weight: 600; letter-spacing: -.02em; }
.geo-seal .d { margin-top: 4px; font-size: 13px; color: var(--ink-2); }

/* Estado vacío */
.geo-empty { text-align: center; padding: 48px 24px; color: var(--ink-3); border: 1px dashed var(--line-2); border-radius: var(--r-l); }
.geo-empty .t { font-size: 16px; font-weight: 600; color: var(--ink); }
.geo-empty .d { margin: 6px auto 0; max-width: 48ch; font-size: 14px; line-height: 1.5; color: var(--ink-2); }

/* Punto de control */
.geo-cp { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.geo-cp .n { font-weight: 600; font-size: 15px; letter-spacing: -.01em; }
.geo-cp .s { font-size: 13px; color: var(--ink-2); margin-top: 2px; }

/* Widgets nativos */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: var(--r-m); font-weight: 500; min-height: 2.5rem; border: 1px solid var(--line-2); background: var(--surface); color: var(--ink);
  box-shadow: var(--shadow);
  transition: background-color 140ms var(--ease-out), border-color 140ms var(--ease-out), transform 160ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .stButton > button:hover, .stDownloadButton > button:hover { background: var(--sunken); border-color: var(--line-3); color: var(--ink); }
}
.stButton > button:active, .stDownloadButton > button:active, [data-testid="stFormSubmitButton"] > button:active { transform: scale(.97); }
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--ink); color: var(--on-ink); border-color: var(--ink); font-weight: 600;
}
@media (hover: hover) and (pointer: fine) {
  button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--ink-2); border-color: var(--ink-2); color: var(--on-ink); }
}
button:disabled { opacity: .5; }

[data-testid="stExpander"] details { border: 1px solid var(--line-1); border-radius: var(--r-m); background: var(--surface); }
[data-testid="stExpander"] summary { font-weight: 500; font-size: 14px; }
[data-testid="stAlert"] { border-radius: var(--r-m); border: 0; font-size: 14px; }
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) { background: var(--warn-bg); color: var(--warn); }
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) { background: var(--human-bg); color: var(--human); }
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) { background: var(--good-bg); color: var(--good); }
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) { background: var(--err-bg); color: var(--err); }
[data-testid="stAlert"] p, [data-testid="stAlert"] code { color: inherit; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border: 1px solid var(--line-1); border-radius: var(--r-m); overflow: hidden; }
[data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--line-1); }
button[data-baseweb="tab"] { font-weight: 500; color: var(--ink-2); padding: 10px 14px; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--ink); font-weight: 600; }
[data-baseweb="tab-highlight"] { background: var(--ink) !important; height: 2px !important; }
[data-testid="stCaptionContainer"] { color: var(--ink-3); }
hr { border-color: var(--line-1); margin: 1.75rem 0; }
code { font-size: .88em; padding: .1em .35em; border-radius: 4px; background: var(--code-bg); color: var(--code); }
label p { font-weight: 500; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: var(--line-2); border-radius: 6px; border: 2px solid var(--bg); }
::-webkit-scrollbar-thumb:hover { background: var(--line-3); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
}
"""


def inject_design_system() -> None:
    """Inyecta tokens y CSS del sistema de diseño."""
    t = tokens()
    root = ";".join(f"--{k}:{v}" for k, v in t.items())
    st.markdown(f"<style>:root{{{root}}}{_CSS}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Recorrido
# ---------------------------------------------------------------------------
STEPS = [
    (1, "Ficha", "CP0"),
    (2, "Competencia", "CP1"),
    (3, "Diagnóstico", ""),
    (4, "Hallazgos", "CP2"),
    (5, "Plan", "CP3"),
    (6, "Propuesta", ""),
    (7, "Calidad y trazas", ""),
]
_CP_KEYS = ["checkpoint_0_brief", "checkpoint_1_competidores", "checkpoint_2_hallazgos", "checkpoint_3_plan"]


# ---------------------------------------------------------------------------
# Ejecución activa
# ---------------------------------------------------------------------------
def ensure_demo_run_ready() -> Run:
    demo_run = Run(run_id="demo", modo="cliente", brief_path=BRIEF_MD, provider="mock")
    if not (demo_run.run_dir / "propuesta.json").exists():
        demo_run.run_all(auto_approve=True, force=False)
    return demo_run


def get_active_run() -> Run:
    run_id = st.session_state.get("active_run_id", "demo")
    run_dir = RUNS_DIR / str(run_id)
    if not run_dir.exists() or not (run_dir / "ficha.json").exists():
        return ensure_demo_run_ready()
    return Run(run_id=str(run_id))


@st.cache_data(show_spinner=False)
def cached_ejecuciones_df() -> pd.DataFrame:
    return load_ejecuciones()


@st.cache_data(show_spinner=False)
def cached_marcas_aliases() -> dict[str, list[str]]:
    return {m.nombre: [m.nombre, *m.alias] for m in load_marcas()}


def shell() -> None:
    """Marco común: CSS, logotipo, aviso de datos sintéticos y tarjeta del análisis activo."""
    inject_design_system()
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), size="large")
    st.markdown(
        '<div class="geo-notice"><span><b>Datos sintéticos del kit UFV-EPS × reload.</b> '
        "No representan el comportamiento real de ningún modelo de lenguaje.</span></div>",
        unsafe_allow_html=True,
    )
    # guardia de run activo
    try:
        from app import ui_jobs
        ui_jobs.guard_active_run()
    except Exception:
        pass
    run = get_active_run()
    ficha = run.load_ficha()
    cps = run.state.get("checkpoints", {})
    done = sum(1 for k in _CP_KEYS if cps.get(k))
    segs = "".join(f'<i class="{"on" if cps.get(k) else ""}"></i>' for k in _CP_KEYS)
    degradados = run.state.get("degradados", {}) or {}
    with st.sidebar:
        st.markdown(
            f'<div class="geo-run"><div class="name">{escape(ficha.marca)}</div>'
            f'<div class="meta">{escape(run.run_id)} · {escape(run.modo)} · {escape(run.provider)}</div>'
            f'<div class="cps" role="img" aria-label="{done} de 4 puntos de control aprobados">{segs}</div>'
            f'<div class="cpl">Puntos de control: {done} de 4</div></div>',
            unsafe_allow_html=True,
        )
        # coste del run si hay progress.json
        try:
            import json
            from pathlib import Path
            from geo.config import RUNS_DIR
            prog = RUNS_DIR / run.run_id / "progress.json"
            if prog.exists():
                pd_ = json.loads(prog.read_text(encoding="utf-8"))
                if pd_.get("cost_eur") is not None:
                    st.caption(f"Coste: {pd_.get('cost_eur')} €")
        except Exception:
            pass
        if degradados:
            st.warning("Pasos en modo simulado: " + ", ".join(degradados.keys()))
        # indicador de conexión
        from geo import settings
        if not settings.has_openrouter_key():
            st.markdown(chip("OpenRouter sin configurar", ""), unsafe_allow_html=True)
            st.page_link("pages/8_Ajustes.py", label="Ir a Ajustes")
        elif settings.get("LLM_PROVIDER") == "openrouter":
            st.markdown(chip(f"OpenRouter · {settings.get('LLM_MODEL')}", "good"), unsafe_allow_html=True)
        else:
            st.markdown(chip("Modo simulado", ""), unsafe_allow_html=True)
        if st.button("Nuevo análisis", type="primary", use_container_width=True):
            st.switch_page("pages/00_Nuevo_analisis.py")
        if st.button("Cargar demo", icon=":material/restart_alt:", use_container_width=True, help="Abre el análisis de demostración (runs/demo/)."):
            ensure_demo_run_ready()
            st.session_state["active_run_id"] = "demo"
            st.rerun()


# ---------------------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------------------
def chip(text: str, kind: str = "", dot: bool = False) -> str:
    cls = " ".join(x for x in ("geo-chip", kind, "dot" if dot else "") if x)
    return f'<span class="{cls}">{escape(text)}</span>'


def render_origin_chip(kind: str, text: str | None = None) -> str:
    """Marca de origen de una cifra: código, IA o persona."""
    mapping = {
        "code": (text or "Calculado", "code"),
        "ai": (text or "Redactado por IA", "ai"),
        "human": (text or "Aprobado", "human"),
        "edited": (text or "Editado", "human"),
    }
    label, cls = mapping.get(kind, (kind, "code"))
    return f'<span class="geo-origin {cls}">{escape(label)}</span>'


def page_header(title: str, lede: str = "", *, checkpoint: int | None = None, step: int | None = None) -> None:
    """Cabecera de página: título, entradilla y estado del punto de control."""
    side = ""
    if step:
        side += chip(f"Paso {step} de 7")
    if checkpoint is not None:
        approved = bool(get_active_run().state.get("checkpoints", {}).get(_CP_KEYS[checkpoint]))
        side += chip(
            f"Punto de control {checkpoint}: " + ("aprobado" if approved else "pendiente"),
            "human dot" if approved else "warn dot",
        )
    lede_html = f"<p>{escape(lede)}</p>" if lede else ""
    st.markdown(
        f'<div class="geo-head"><div><h1>{escape(title)}</h1>{lede_html}</div><div class="side">{side}</div></div>',
        unsafe_allow_html=True,
    )


def section(title: str, source: str = "", desc: str = "") -> None:
    src = f'<span class="src">{escape(source)}</span>' if source else ""
    d = f'<div class="geo-desc">{escape(desc)}</div>' if desc else ""
    st.markdown(f'<div class="geo-sec"><h2>{escape(title)}</h2>{src}</div>{d}', unsafe_allow_html=True)


@contextmanager
def panel(title: str = "", source: str = "") -> Iterator[None]:
    """Panel con borde y cabecera opcional (título + origen de la cifra)."""
    n = st.session_state.get("_panel_n", 0)
    st.session_state["_panel_n"] = n + 1
    with st.container(border=True, key=f"panel_{n}"):
        if title:
            src = f'<span class="src">{escape(source)}</span>' if source else ""
            st.markdown(f'<div class="geo-panel-head"><span class="t">{escape(title)}</span>{src}</div>', unsafe_allow_html=True)
        yield


def kpi_strip(items: Sequence[dict[str, Any]], scope: str | None = None) -> None:
    """Tira de indicadores. Cada item: label, value, unit, note, source, highlight, chip."""
    cells = []
    for it in items:
        unit = f'<span class="u">{escape(str(it["unit"]))}</span>' if it.get("unit") else ""
        chip_html = chip(it["chip"], it.get("chip_kind", "")) if it.get("chip") else ""
        note = f'<div class="n">{escape(str(it["note"]))}</div>' if it.get("note") else ""
        src = f'<div class="s">{escape(str(it["source"]))}</div>' if it.get("source") else ""
        hl = " hl" if it.get("highlight") else ""
        cells.append(
            f'<div class="k{hl}"><div class="l">{escape(str(it["label"]))}{chip_html}</div>'
            f'<div class="v">{escape(str(it["value"]))}{unit}</div>{note}{src}</div>'
        )
    st.markdown(f'<div class="geo-kpis">{"".join(cells)}</div>', unsafe_allow_html=True)


def finding_header(
    fid: str, tipo: str, categoria: str, titulo: str, cifra: str, origin: str, n: int,
    fase: str, motores: str, impacto: str, confianza: str, descripcion: str,
) -> None:
    kind = "good" if tipo.lower().startswith("fort") else "bad"
    st.markdown(
        f'''<div class="geo-find">
          <div class="fig"><div class="num">{escape(cifra)}</div><div class="org">{escape(origin)}</div></div>
          <div>
            <div class="top"><span class="fid">{escape(fid)}</span>{chip(tipo, kind)}{chip(categoria)}</div>
            <h3>{escape(titulo)}</h3>
            <p>{escape(descripcion)}</p>
            <dl>
              <div><dt>Muestra</dt><dd>n = {n}</dd></div>
              <div><dt>Fase</dt><dd>{escape(fase)}</dd></div>
              <div><dt>Motores</dt><dd>{escape(motores)}</dd></div>
              <div><dt>Impacto</dt><dd>{escape(impacto)}</dd></div>
              <div><dt>Confianza</dt><dd>{escape(confianza)}</dd></div>
            </dl>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_seal(counts: str, status: str = "Lista para enviar", ok: bool = True) -> None:
    """Sello del agente revisor (verificación determinista)."""
    st.markdown(
        f'''<div class="geo-seal">
          <div><div class="c">{escape(counts)}</div>
          <div class="d">Verificación determinista de cifras y cumplimiento normativo sanitario</div></div>
          {chip(status, "good dot" if ok else "err dot")}
        </div>''',
        unsafe_allow_html=True,
    )


def render_empty(title: str, desc: str) -> None:
    st.markdown(f'<div class="geo-empty"><div class="t">{escape(title)}</div><div class="d">{escape(desc)}</div></div>', unsafe_allow_html=True)


def checkpoint_summary(name: str, summary: str, approved: bool) -> None:
    """Resumen de punto de control (los botones de acción los pone la página)."""
    st.markdown(
        f'<div class="geo-cp"><div><div class="n">{escape(name)}</div><div class="s">{escape(summary)}</div></div>'
        f'{chip("Aprobado" if approved else "Pendiente de aprobación", "human dot" if approved else "warn dot")}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def style_fig(fig: go.Figure, height: int = 360, legend: bool = True) -> go.Figure:
    """Aplica el estilo común a una figura de Plotly (claro/oscuro, Geist, filetes finos)."""
    t = tokens()
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Geist, system-ui, sans-serif", size=12, color=t["ink-2"]),
        margin=dict(l=4, r=8, t=8, b=4),
        colorway=cat_colors(),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text="", font=dict(size=12)),
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["line-2"], font=dict(family="Geist, system-ui, sans-serif", size=12, color=t["ink"])),
        bargap=0.28,
    )
    fig.update_xaxes(gridcolor=t["line-1"], zeroline=False, linecolor=t["line-2"], tickfont=dict(color=t["ink-3"]), title_font=dict(size=12, color=t["ink-3"]))
    fig.update_yaxes(gridcolor=t["line-1"], zeroline=False, linecolor=t["line-2"], tickfont=dict(color=t["ink-2"]), title_font=dict(size=12, color=t["ink-3"]))
    return fig


def brand_key(marca: str, lider: str) -> None:
    """Clave de color marca / líder / resto, común a los gráficos de ranking."""
    t = tokens()
    st.markdown(
        f'<div class="geo-key"><span><i style="background:{t["accent"]}"></i>{escape(marca)}</span>'
        f'<span><i style="background:{t["lead"]}"></i>Líder ({escape(lider)})</span>'
        f'<span><i style="background:{t["rest"]}"></i>Resto de marcas</span></div>',
        unsafe_allow_html=True,
    )


def scope_style(scope: str) -> None:
    """Colorea el control segmentado activo con el color del ámbito (espontánea/asistida)."""
    color = "var(--assist)" if scope == "Asistida" else "var(--spont)"
    st.markdown(
        f'<style>[data-testid="stButtonGroup"] button[aria-checked="true"]{{background:{color} !important;border-color:{color} !important}}'
        f'[data-testid="stButtonGroup"] button[aria-checked="true"] *{{color:#fff !important}}</style>',
        unsafe_allow_html=True,
    )


def show_fig(fig: go.Figure, height: int = 360, legend: bool = True) -> None:
    st.plotly_chart(style_fig(fig, height, legend), use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Visor de evidencias
# ---------------------------------------------------------------------------
def highlight_brand_in_text(text: str, marca_nombre: str) -> str:
    aliases_map = cached_marcas_aliases()
    terms = sorted(aliases_map.get(marca_nombre, [marca_nombre]), key=len, reverse=True)
    out = text
    for term in terms:
        pat = re.compile(rf"(\b{re.escape(term)}\b)", flags=re.IGNORECASE)
        out = pat.sub(r":orange-background[**\1**]", out)
    return out


def evidence_view(
    ejecucion_ids: Sequence[str],
    marca_resaltada: str = "Clínica Alborada Visión",
    *,
    title: str = "Ver respuestas originales",
    max_items: int = 5,
) -> None:
    ids_list = [str(x) for x in ejecucion_ids if str(x)][:max_items]
    if not ids_list:
        st.caption("Sin ejecuciones asociadas.")
        return
    df_ej = cached_ejecuciones_df()
    sub = df_ej[df_ej["ejecucion_id"].isin(ids_list)]
    with st.expander(f"{title} ({len(ids_list)})", icon=":material/manage_search:"):
        for i, (_, row) in enumerate(sub.iterrows()):
            fuentes_str = ", ".join(row["fuentes"]) if row["fuentes"] else "Sin fuentes citadas (sin búsqueda web)"
            ambito = "Espontánea" if row["espontanea"] else "Asistida"
            st.markdown(
                f'<code>{escape(str(row["ejecucion_id"]))}</code> '
                f'{chip(ambito, "spont" if row["espontanea"] else "assist")} '
                f'{chip(str(row["motor"]) + " · rep. " + str(row["repeticion"]))} '
                f'{chip(str(row["intencion"]))}',
                unsafe_allow_html=True,
            )
            st.caption(f"Prompt: {row['prompt_ejecutado']}  \nFuentes: {fuentes_str}")
            st.markdown(highlight_brand_in_text(str(row["respuesta"]), marca_resaltada))
            if i < len(sub) - 1:
                st.divider()
