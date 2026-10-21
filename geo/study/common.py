"""Utilidades compartidas del estudio: lectura/escritura de CSV del kit y normalización de texto."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from geo import settings as _settings

MOTORES: tuple[str, ...] = ("ChatGPT", "Gemini", "Perplexity", "Claude")

KINDS: tuple[str, ...] = (
    "ejecuciones",
    "marcas",
    "banco_prompts",
    "fuentes_catalogo",
    "muestra_evaluada",
)

# Nombre del archivo canónico dentro de study/
KIND_FILENAMES: dict[str, str] = {k: f"{k}.csv" for k in KINDS}

TIPOS_FUENTE_CLASIFICABLES: tuple[str, ...] = (
    "Ranking / institución",
    "Medio",
    "Web propia",
    "Directorio / comparador",
    "Plataforma de reseñas",
    "Red social / foro",
)

EJECUCIONES_COLUMNS: list[str] = [
    "Ejecucion_ID",
    "Sector",
    "Prompt_ID",
    "Familia",
    "Intención",
    "Prompt ejecutado",
    "Motor",
    "Repetición",
    "Marcas a evaluar",
    "Respuesta completa",
    "Fuentes citadas",
    "Fecha/hora",
]
MARCAS_COLUMNS: list[str] = ["Marca", "Nivel", "Rol", "Dominio_propio", "Alias"]
BANCO_COLUMNS: list[str] = [
    "Prompt_ID",
    "Sector",
    "Familia",
    "Intención",
    "Prioridad",
    "Uso",
    "Instanciación",
    "Prompt (plantilla)",
    "Notas de instanciación",
]
FUENTES_COLUMNS: list[str] = ["Dominio", "Tipo_de_fuente", "Calidad_de_fuente_0_1"]
MUESTRA_COLUMNS: list[str] = [
    "Sector",
    "Marca",
    "Prompt_ID",
    "Intención",
    "Prompt ejecutado",
    "Motor",
    "Repetición",
    "Aparece (1/0)",
    "Posición",
    "Peso posición",
    "Tipo de mención",
    "Fuente citada",
    "Respuesta completa",
    "Fecha/hora",
    "Notas",
    "Fuerza recomendación (-1 a 3)",
    "Sentimiento",
    "Tipo de fuente",
    "Fuera de territorio",
    "Ejecucion_ID",
]
KIND_COLUMNS: dict[str, list[str]] = {
    "ejecuciones": EJECUCIONES_COLUMNS,
    "marcas": MARCAS_COLUMNS,
    "banco_prompts": BANCO_COLUMNS,
    "fuentes_catalogo": FUENTES_COLUMNS,
    "muestra_evaluada": MUESTRA_COLUMNS,
}


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def header_key(text: str) -> str:
    """Clave tolerante de cabecera: sin BOM, tildes, mayúsculas ni signos."""
    t = strip_accents(str(text).replace("﻿", "")).lower()
    return re.sub(r"[^a-z0-9]+", "", t)


def norm_name(text: str) -> str:
    """Nombre normalizado para comparar marcas: sin tildes, minúsculas y espacios simples."""
    t = strip_accents(str(text or "")).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def read_csv_flex(path: Path) -> pd.DataFrame:
    """Lee un CSV como texto (sin NaN), tolerante a BOM, codificación y separador."""
    last: Exception | None = None
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(
                path,
                encoding=enc,
                dtype=str,
                keep_default_na=False,
                sep=None,
                engine="python",
            )
        except UnicodeDecodeError as exc:
            last = exc
            continue
    raise ValueError(f"No se pudo leer el archivo {path.name}: {last}")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def write_json(path: Path, obj: Any) -> Path:
    """Guarda un objeto (modelo de Pydantic o dict) como JSON legible en UTF-8."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def split_pipe(val: Any) -> list[str]:
    if val is None:
        return []
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return []
    return [p.strip() for p in s.split("|") if p.strip()]


def split_domains(val: Any) -> list[str]:
    if val is None:
        return []
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return []
    return [p.strip().lower() for p in re.split(r"[,;]", s) if p.strip()]


def setting_int(key: str, default: int) -> int:
    """Ajuste entero opcional: si la clave no existe o está vacía devuelve el valor por defecto."""
    try:
        raw = _settings.get(key).strip()
        return int(raw) if raw else default
    except Exception:
        return default


def setting_float(key: str, default: float) -> float:
    try:
        raw = _settings.get(key).strip()
        return float(raw) if raw else default
    except Exception:
        return default


def proposer_model() -> str:
    """Modelo de propuesta: LLM_MODEL_PROPOSER, o el modelo general si no está definido."""
    try:
        m = _settings.get("LLM_MODEL_PROPOSER").strip()
        if m:
            return m
        return _settings.get("LLM_MODEL").strip() or "mock"
    except Exception:
        return "mock"


def active_provider(provider: str | None = None) -> str:
    return (provider or _settings.get("LLM_PROVIDER") or "mock").strip().lower()


def track_usage(model: str, tokens_in: int, tokens_out: int, cost_usd: float | None, prompt_version: str) -> float:
    """Suma una llamada directa a `openrouter.chat` a los contadores de `geo.llm` (para el coste del proyecto).

    Devuelve el coste de la llamada en euros (real si OpenRouter lo informa; estimado si no).
    """
    from geo import llm as _llm

    rate = _settings.get_float("USD_EUR")
    if cost_usd is not None:
        eur = cost_usd * rate
    else:
        try:
            eur = _llm.estimate_cost_for_model(model, tokens_in, tokens_out)
        except Exception:
            eur = _llm.estimate_cost(1, tokens_in, tokens_out) * rate
    tr = _llm._TRACKER
    with tr.lock:
        tr.calls += 1
        tr.tokens_in += tokens_in
        tr.tokens_out += tokens_out
        tr.cost_eur += eur
        if cost_usd is not None:
            tr.cost_is_real = True
        tr.records.append(
            {
                "provider": "openrouter",
                "model": model,
                "prompt_version": prompt_version,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cache_file": "",
            }
        )
    return eur


def extract_domain(url: str) -> str:
    from geo.engines.openai_engine import extract_domain as _ed

    return _ed(url)


def prompt_text(name: str) -> str:
    """Carga un prompt versionado de geo/prompts/<name>.md o, si no está, de geo/study/prompts/<name>.md."""
    from geo.config import PROMPTS_DIR

    for base in (PROMPTS_DIR, Path(__file__).resolve().parent / "prompts"):
        p = base / f"{name}.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Falta el prompt {name}.md")
