"""Configuración global, rutas, constantes de la metodología y settings de entorno."""

import csv
import os
from pathlib import Path
from dotenv import load_dotenv

from geo.schemas import Intencion, Motor, TipoFuente

load_dotenv()

# ---------- Rutas ----------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
KIT_DIR: Path = ROOT_DIR / "kit" / "Kit Participantes Hackaton"
REFERENCE_DATA_DIR: Path = Path(__file__).resolve().parent / "reference_data"
DATA_DIR: Path = REFERENCE_DATA_DIR  # solo datos del kit (modo de referencia)
BRIEF_DIR: Path = REFERENCE_DATA_DIR
BRIEF_MD: Path = BRIEF_DIR / "Brief_de_ejemplo_Clinica_Alborada.md"
BRIEF_DOCX: Path = BRIEF_DIR / "Brief_de_ejemplo_Clinica_Alborada.docx"
DOCS_DIR: Path = KIT_DIR / "03_Documentacion"
PROMPTS_DIR: Path = Path(__file__).resolve().parent / "prompts"
CACHE_DIR: Path = ROOT_DIR / "cache"
RUNS_DIR: Path = ROOT_DIR / "runs"

# Archivos CSV del kit
MARCAS_CSV: Path = DATA_DIR / "marcas.csv"
BANCO_PROMPTS_CSV: Path = DATA_DIR / "banco_prompts.csv"
EJECUCIONES_CSV: Path = DATA_DIR / "ejecuciones.csv"
FUENTES_CATALOGO_CSV: Path = DATA_DIR / "fuentes_catalogo.csv"
MUESTRA_EVALUADA_CSV: Path = DATA_DIR / "muestra_evaluada.csv"

# ---------- Constantes de la metodología ----------
MOTORES: list[Motor] = ["ChatGPT", "Gemini", "Perplexity", "Claude"]

# Orden del embudo de decisión
INTENCIONES: list[Intencion] = [
    "Descubrimiento",
    "Comparación",
    "Validación",
    "Decisión",
]

INSTANCIACIONES_ESPONTANEAS: set[str] = {"generico", "ciudad"}
INSTANCIACIONES_ASISTIDAS: set[str] = {"marca", "par"}

CIUDADES_CONOCIDAS: list[str] = [
    "Madrid",
    "Barcelona",
    "Valencia",
    "Sevilla",
    "Bilbao",
    "Zaragoza",
    "Málaga",
]

# Pesos máximos de los componentes del Score de Citación (0-100)
SCORE_WEIGHTS: dict[str, int] = {
    "aparicion": 30,
    "posicion": 20,
    "fuerza": 30,
    "fuente": 20,
}

# Pesos por posición: {1: 3, 2: 2, 3: 2, >=4: 1, ausente: 0}
POSITION_WEIGHTS: dict[int, int] = {
    0: 0,
    1: 3,
    2: 2,
    3: 2,
}
DEFAULT_POSITION_WEIGHT_GE_4: int = 1


def peso_por_posicion(posicion: int | None) -> int:
    """Devuelve el peso de posición según la metodología GEO (1->3, 2-3->2, >=4->1, None/0->0)."""
    if posicion is None or posicion <= 0:
        return 0
    return POSITION_WEIGHTS.get(posicion, DEFAULT_POSITION_WEIGHT_GE_4)


# Calidad por tipo de fuente (0.0 a 1.0)
SOURCE_QUALITY_BY_TYPE: dict[TipoFuente, float] = {
    "Ranking / institución": 1.0,
    "Medio": 0.9,
    "Web propia": 0.7,
    "Directorio / comparador": 0.6,
    "Plataforma de reseñas": 0.6,
    "Red social / foro": 0.4,
    "Sin fuente": 0.2,
}

# ---------- Léxico del juez por reglas (F3, texto normalizado sin tildes) ----------
FUERZA_3: list[str] = [
    "es la que mas recomendaria",
    "la opcion mas recomendable",
    "seria mi recomendacion principal",
    "si tuviera que inclinarme por una",
    "es la opcion mas recomendada",
    "mi recomendacion principal",
    "tambien la recomendaria con confianza",
    "me inclinaria por",
]

FUERZA_2: list[str] = [
    "alternativa muy bien valorada",
    "opcion solida y bien valorada",
    "tambien la recomendaria",
    "encaja bien",
]

NEGATIVO: list[str] = [
    "eso si,",
    "quejas",
    "advierten",
    "listas de espera",
    "coste notablemente superior",
    "pocas opiniones verificadas",
    "desiguales",
    "mas antiguas",
    "varia bastante",
    "echan en falta",
    "muy cargada",
]

DESCONOCIMIENTO: list[str] = [
    "no dispongo de informacion",
    "no tengo informacion",
    "no cuento con datos",
]

# Umbral de longitud mínima del fragmento (sin el nombre de la marca) para no ser Pasiva en pos 1-3
PASIVA_MAX_CHARS: int = 35

# ---------- Umbrales del motor de hallazgos (F6) ----------
FINDINGS_THRESHOLDS: dict[str, float] = {
    "r1_geo_diff_pp": 25.0,               # Diferencia >= 25 pp entre ciudades
    "r1_geo_growth_city_max": 0.15,       # O aparición < 15 % en ciudad de crecimiento
    "r2_weak_motor_ratio": 0.50,          # Aparición en un motor < 50 % de la media en los demás
    "r3_funnel_drop_pp": 20.0,            # Caída >= 20 pp respecto a fase anterior
    "r3_funnel_leader_gap_pp": 30.0,      # Brecha con el líder >= 30 pp en una fase
    "r5_authority_sources_gap_pp": 20.0,  # Brecha >= 20 pp en Ranking/institución + Medio vs líder
    "r5_sin_fuente_min": 0.15,            # O % Sin fuente >= 15 %
    "r7_undeclared_competitor_min": 0.30, # Competidor no declarado con >= 30 % aparición espontánea
    "r8_azar_min": 0.50,                  # % de series en zona de azar (1-2/3) > 50 %
    "r9_profile_low_max": 0.40,           # Aparición en familia DP < 40 %
    "r10_desconocimiento_min": 0.05,      # % de desconocimiento en asistida >= 5 %
}
MAX_FINDINGS: int = 7

# Capacidad semanal máxima del equipo del cliente dedicada al plan GEO (1 resp. marketing + 0.5 comunicación -> ~18 h/sem dedicables)
CLIENT_WEEKLY_HOURS_CAPACITY: float = 18.0


def get_catalog_domains_by_type(path: Path | None = None) -> dict[str, list[str]]:
    """Lee un fuentes_catalogo.csv y devuelve los dominios agrupados por Tipo_de_fuente."""
    if path is None:
        path = FUENTES_CATALOGO_CSV
    by_type: dict[str, list[str]] = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                dom = str(row["Dominio"]).strip().lower()
                t_fuente = str(row["Tipo_de_fuente"]).strip()
                by_type.setdefault(t_fuente, []).append(dom)
    return by_type


# ---------- Catálogo de plantillas de acción (F9: 22 plantillas) ----------
# Aquí solo vive la parte numérica y estructural. Los textos (título, descripción, KPI y
# entregables) salen del perfil de sector (`geo/sector_profiles/*.yaml`) con los datos del proyecto.
ACTION_SKELETON: list[dict[str, object]] = [
    {
        'template_id': 'TPL-01',
        'palanca': 'entidad_datos_estructurados',
        'tipos_hallazgo': ['fuentes', 'motor', 'embudo'],
        'fase_embudo': ['Descubrimiento', 'Validación'],
        'esfuerzo': 'M',
        'impacto': 'L',
        'responsable': 'agencia',
        'coste_rango_eur': (1500.0, 2500.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 3,
        'fase_plan': 0,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-02',
        'palanca': 'tecnico',
        'tipos_hallazgo': ['motor', 'consistencia'],
        'fase_embudo': ['Descubrimiento'],
        'esfuerzo': 'S',
        'impacto': 'L',
        'responsable': 'agencia',
        'coste_rango_eur': (500.0, 1000.0),
        'horas_cliente_semana': 1.5,
        'plazo_semanas': 2,
        'fase_plan': 0,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-03',
        'palanca': 'entidad_datos_estructurados',
        'tipos_hallazgo': ['fuentes', 'geografia', 'brief_vs_datos'],
        'fase_embudo': ['Descubrimiento', 'Comparación'],
        'esfuerzo': 'S',
        'impacto': 'M',
        'responsable': 'cliente_marketing',
        'coste_rango_eur': (800.0, 1500.0),
        'horas_cliente_semana': 3.0,
        'plazo_semanas': 3,
        'fase_plan': 0,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-04',
        'palanca': 'entidad_datos_estructurados',
        'tipos_hallazgo': ['motor', 'fuentes'],
        'fase_embudo': ['Descubrimiento', 'Validación'],
        'esfuerzo': 'S',
        'impacto': 'M',
        'responsable': 'agencia',
        'coste_rango_eur': (300.0, 800.0),
        'horas_cliente_semana': 1.0,
        'plazo_semanas': 2,
        'fase_plan': 0,
        'dependencias_tpl': ['TPL-01'],
    },
    {
        'template_id': 'TPL-05',
        'palanca': 'contenido',
        'tipos_hallazgo': ['geografia'],
        'fase_embudo': ['Descubrimiento', 'Decisión'],
        'esfuerzo': 'M',
        'impacto': 'L',
        'responsable': 'agencia',
        'coste_rango_eur': (2000.0, 3500.0),
        'horas_cliente_semana': 3.5,
        'plazo_semanas': 4,
        'fase_plan': 1,
        'dependencias_tpl': ['TPL-01'],
    },
    {
        'template_id': 'TPL-06',
        'palanca': 'reputacion_resenas',
        'tipos_hallazgo': ['geografia', 'reputacion'],
        'fase_embudo': ['Validación', 'Decisión'],
        'esfuerzo': 'S',
        'impacto': 'L',
        'responsable': 'cliente_comunicacion',
        'coste_rango_eur': (600.0, 1200.0),
        'horas_cliente_semana': 2.5,
        'plazo_semanas': 5,
        'fase_plan': 1,
        'dependencias_tpl': ['TPL-03'],
    },
    {
        'template_id': 'TPL-07',
        'palanca': 'contenido',
        'tipos_hallazgo': ['embudo', 'perfil', 'motor'],
        'fase_embudo': ['Descubrimiento', 'Comparación', 'Decisión'],
        'esfuerzo': 'M',
        'impacto': 'L',
        'responsable': 'agencia',
        'coste_rango_eur': (1500.0, 2500.0),
        'horas_cliente_semana': 3.0,
        'plazo_semanas': 4,
        'fase_plan': 1,
        'dependencias_tpl': ['TPL-01'],
    },
    {
        'template_id': 'TPL-08',
        'palanca': 'contenido',
        'tipos_hallazgo': ['embudo', 'competencia'],
        'fase_embudo': ['Comparación', 'Decisión'],
        'esfuerzo': 'S',
        'impacto': 'L',
        'responsable': 'cliente_marketing',
        'coste_rango_eur': (800.0, 1200.0),
        'horas_cliente_semana': 3.0,
        'plazo_semanas': 3,
        'fase_plan': 1,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-09',
        'palanca': 'contenido',
        'tipos_hallazgo': ['reputacion', 'embudo'],
        'fase_embudo': ['Validación', 'Decisión'],
        'esfuerzo': 'S',
        'impacto': 'L',
        'responsable': 'cliente_medico',
        'coste_rango_eur': (1000.0, 1500.0),
        'horas_cliente_semana': 2.5,
        'plazo_semanas': 3,
        'fase_plan': 1,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-10',
        'palanca': 'contenido',
        'tipos_hallazgo': ['perfil', 'embudo'],
        'fase_embudo': ['Descubrimiento', 'Comparación'],
        'esfuerzo': 'M',
        'impacto': 'M',
        'responsable': 'agencia',
        'coste_rango_eur': (2000.0, 3000.0),
        'horas_cliente_semana': 2.5,
        'plazo_semanas': 5,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-07'],
    },
    {
        'template_id': 'TPL-11',
        'palanca': 'autoridad_terceros',
        'tipos_hallazgo': ['fuentes', 'competencia', 'brief_vs_datos', 'reputacion'],
        'fase_embudo': ['Descubrimiento', 'Validación'],
        'esfuerzo': 'L',
        'impacto': 'L',
        'responsable': 'agencia',
        'coste_rango_eur': (4000.0, 7000.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 12,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-05', 'TPL-09'],
    },
    {
        'template_id': 'TPL-12',
        'palanca': 'autoridad_terceros',
        'tipos_hallazgo': ['fuentes', 'competencia'],
        'fase_embudo': ['Descubrimiento', 'Comparación', 'Validación'],
        'esfuerzo': 'M',
        'impacto': 'L',
        'responsable': 'cliente_comunicacion',
        'coste_rango_eur': (1000.0, 3000.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 8,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-03'],
    },
    {
        'template_id': 'TPL-13',
        'palanca': 'comunidades',
        'tipos_hallazgo': ['fuentes', 'reputacion'],
        'fase_embudo': ['Comparación', 'Validación'],
        'esfuerzo': 'M',
        'impacto': 'M',
        'responsable': 'cliente_comunicacion',
        'coste_rango_eur': (1500.0, 3000.0),
        'horas_cliente_semana': 2.5,
        'plazo_semanas': 8,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-09'],
    },
    {
        'template_id': 'TPL-14',
        'palanca': 'contenido',
        'tipos_hallazgo': ['embudo', 'competencia'],
        'fase_embudo': ['Comparación'],
        'esfuerzo': 'M',
        'impacto': 'M',
        'responsable': 'cliente_medico',
        'coste_rango_eur': (1200.0, 2000.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 4,
        'fase_plan': 1,
        'dependencias_tpl': ['TPL-01'],
    },
    {
        'template_id': 'TPL-15',
        'palanca': 'entidad_datos_estructurados',
        'tipos_hallazgo': ['fuentes', 'motor'],
        'fase_embudo': ['Validación', 'Decisión'],
        'esfuerzo': 'S',
        'impacto': 'M',
        'responsable': 'cliente_marketing',
        'coste_rango_eur': (900.0, 1500.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 3,
        'fase_plan': 0,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-16',
        'palanca': 'reputacion_resenas',
        'tipos_hallazgo': ['reputacion'],
        'fase_embudo': ['Validación', 'Decisión'],
        'esfuerzo': 'S',
        'impacto': 'M',
        'responsable': 'cliente_marketing',
        'coste_rango_eur': (500.0, 900.0),
        'horas_cliente_semana': 1.5,
        'plazo_semanas': 3,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-06'],
    },
    {
        'template_id': 'TPL-17',
        'palanca': 'entidad_datos_estructurados',
        'tipos_hallazgo': ['brief_vs_datos', 'consistencia', 'motor'],
        'fase_embudo': ['Descubrimiento', 'Validación'],
        'esfuerzo': 'S',
        'impacto': 'L',
        'responsable': 'cliente_comunicacion',
        'coste_rango_eur': (700.0, 1200.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 2,
        'fase_plan': 0,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-18',
        'palanca': 'comunidades',
        'tipos_hallazgo': ['fuentes', 'consistencia'],
        'fase_embudo': ['Descubrimiento', 'Validación'],
        'esfuerzo': 'M',
        'impacto': 'S',
        'responsable': 'agencia',
        'coste_rango_eur': (1000.0, 1800.0),
        'horas_cliente_semana': 1.5,
        'plazo_semanas': 6,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-07'],
    },
    {
        'template_id': 'TPL-19',
        'palanca': 'contenido',
        'tipos_hallazgo': ['embudo', 'consistencia', 'motor'],
        'fase_embudo': ['Comparación', 'Decisión'],
        'esfuerzo': 'M',
        'impacto': 'M',
        'responsable': 'agencia',
        'coste_rango_eur': (1500.0, 2400.0),
        'horas_cliente_semana': 2.0,
        'plazo_semanas': 6,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-07'],
    },
    {
        'template_id': 'TPL-20',
        'palanca': 'medicion',
        'tipos_hallazgo': ['brief_vs_datos', 'competencia'],
        'fase_embudo': ['Descubrimiento', 'Comparación'],
        'esfuerzo': 'S',
        'impacto': 'M',
        'responsable': 'agencia',
        'coste_rango_eur': (600.0, 1000.0),
        'horas_cliente_semana': 1.0,
        'plazo_semanas': 4,
        'fase_plan': 3,
        'dependencias_tpl': [],
    },
    {
        'template_id': 'TPL-21',
        'palanca': 'autoridad_terceros',
        'tipos_hallazgo': ['geografia', 'perfil'],
        'fase_embudo': ['Descubrimiento'],
        'esfuerzo': 'M',
        'impacto': 'M',
        'responsable': 'cliente_comunicacion',
        'coste_rango_eur': (1200.0, 2200.0),
        'horas_cliente_semana': 2.5,
        'plazo_semanas': 8,
        'fase_plan': 2,
        'dependencias_tpl': ['TPL-05'],
    },
    {
        'template_id': 'TPL-22',
        'palanca': 'medicion',
        'tipos_hallazgo': ['geografia', 'motor', 'embudo', 'competencia', 'fuentes', 'reputacion', 'brief_vs_datos', 'consistencia', 'perfil'],
        'fase_embudo': ['Descubrimiento', 'Comparación', 'Validación', 'Decisión'],
        'esfuerzo': 'S',
        'impacto': 'L',
        'responsable': 'agencia',
        'coste_rango_eur': (3000.0, 6000.0),
        'horas_cliente_semana': 1.0,
        'plazo_semanas': 36,
        'fase_plan': 3,
        'dependencias_tpl': ['TPL-01', 'TPL-05'],
    },
]


def __getattr__(name: str):
    """`ACTION_LIBRARY`: esqueleto + textos genéricos sin rellenar (para inspección y tests)."""
    if name == "ACTION_LIBRARY":
        from geo.sectors import raw_action_library

        return raw_action_library()
    raise AttributeError(name)

# ---------- Settings leídos de .env ----------
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
LLM_MODEL: str = os.getenv("LLM_MODEL", "").strip()
LLM_MODEL_WRITER: str = os.getenv("LLM_MODEL_WRITER", "").strip()
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
MAX_LLM_CALLS: int = int(os.getenv("MAX_LLM_CALLS", "1500").strip() or "1500")
MAX_BUDGET_EUR: float = float(os.getenv("MAX_BUDGET_EUR", "5.0").strip() or "5.0")
