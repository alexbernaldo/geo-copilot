"""Configuración global, rutas, constantes de la metodología y settings de entorno."""

import os
from pathlib import Path
from dotenv import load_dotenv

from geo.schemas import Intencion, Motor, TipoFuente

load_dotenv()

# ---------- Rutas ----------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
KIT_DIR: Path = ROOT_DIR / "kit" / "Kit Participantes Hackaton"
DATA_DIR: Path = KIT_DIR / "02_Datos" / "caso_oftalmologia"
BRIEF_DIR: Path = KIT_DIR / "01_Briefings"
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

# ---------- Settings leídos de .env ----------
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
LLM_MODEL: str = os.getenv("LLM_MODEL", "").strip()
LLM_MODEL_WRITER: str = os.getenv("LLM_MODEL_WRITER", "").strip()
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
MAX_LLM_CALLS: int = int(os.getenv("MAX_LLM_CALLS", "1500").strip() or "1500")
