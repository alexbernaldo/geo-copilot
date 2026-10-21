"""WC4 · Clasificación de fuentes citadas (B2.4)."""

from __future__ import annotations

import json
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from pydantic import BaseModel, Field

from geo import llm as _llm
from geo import reference as _reference
from geo import settings as _settings
from geo.config import SOURCE_QUALITY_BY_TYPE
from geo.study.brands import read_marcas_csv
from geo.study.common import (
    FUENTES_COLUMNS,
    TIPOS_FUENTE_CLASIFICABLES,
    active_provider,
    extract_domain,
    prompt_text,
    read_csv_flex,
    split_domains,
    write_csv,
)

PROMPT_VERSION = "sources_v1"
BATCH_SIZE = 30
DEFAULT_TYPE = "Directorio / comparador"  # la opción más conservadora (calidad 0,6) cuando no hay criterio

_cache_lock = threading.Lock()


class ClasifDominio(BaseModel):
    dominio: str
    tipo: str


class ClasificacionDominios(BaseModel):
    dominios: list[ClasifDominio] = Field(default_factory=list)


@dataclass
class SourcesResult:
    catalogo_csv: Path
    total_dominios: int = 0
    nuevos: int = 0
    web_propia: int = 0
    desde_cache: int = 0
    clasificados_llm: int = 0
    heuristicos: int = 0
    dominios_nuevos: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- heurística por código (respaldo y modo mock)

_SOCIAL = ("facebook.", "instagram.", "twitter.", "x.com", "reddit.", "youtube.", "tiktok.", "linkedin.", "forocoches", "foro", "quora.", "pinterest.", "telegram.")
_RESENAS = ("trustpilot", "opiniones", "resenas", "reseñas", "tripadvisor", "yelp", "google.com/maps", "reviews", "valoraciones", "ciao.", "mejoropinion", "opinion")
_INSTITUCION = (".gov", ".gob.", ".edu", ".ac.", "wikipedia.", "who.int", "europa.eu", "colegio", "sociedad", "asociacion", "fundacion", "universidad", "ranking", "ministerio", "ine.es", "isciii", "oms.")
_MEDIO = (
    "elpais.", "elmundo.", "abc.es", "lavanguardia.", "20minutos.", "rtve.", "europapress.", "elconfidencial.", "expansion.",
    "cincodias.", "eldiario.", "lavozdegalicia.", "larazon.", "marca.com", "as.com", "cnn.", "bbc.", "forbes.", "huffingtonpost.",
    "xataka.", "genbeta.", "magazine", "diario", "noticias", "periodico", "revista", "news", "prensa",
)
_DIRECTORIO = ("doctoralia", "topdoctors", "paginasamarillas", "directorio", "comparador", "compara", "buscador", "guia", "listado", "habitissimo", "milanuncios", "idealista", "tuprofesional")


def heuristic_type(domain: str) -> str:
    """Tipo de fuente deducido del dominio con reglas simples; sin criterio devuelve el tipo conservador."""
    d = domain.lower()
    for kw, tipo in (
        (_SOCIAL, "Red social / foro"),
        (_RESENAS, "Plataforma de reseñas"),
        (_INSTITUCION, "Ranking / institución"),
        (_DIRECTORIO, "Directorio / comparador"),
        (_MEDIO, "Medio"),
    ):
        if any(k in d for k in kw):
            return tipo
    return DEFAULT_TYPE


def quality(tipo: str) -> float:
    return SOURCE_QUALITY_BY_TYPE[tipo]  # type: ignore[index]


# ---------------------------------------------------------------- caché global por dominio


def global_cache_path() -> Path:
    """`<GEO_DATA_DIR>/cache/dominios.json`; sin GEO_DATA_DIR usa `data/cache/dominios.json` de la raíz."""
    raw = _settings.get("GEO_DATA_DIR").strip()
    if raw:
        base = Path(raw)
        if not base.is_absolute():
            base = _settings.ROOT_DIR / base
        return base / "cache" / "dominios.json"
    return _settings.ROOT_DIR / "data" / "cache" / "dominios.json"


def _load_cache(path: Path) -> dict[str, str]:
    with _cache_lock:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {k: v for k, v in data.items() if v in TIPOS_FUENTE_CLASIFICABLES}
        except Exception:
            return {}


def _save_cache(path: Path, new: dict[str, str]) -> None:
    with _cache_lock:
        cur: dict[str, str] = {}
        if path.exists():
            try:
                cur = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                cur = {}
        cur.update(new)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(dict(sorted(cur.items())), ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)


# ---------------------------------------------------------------- clasificación


def is_own_domain(domain: str, own: set[str]) -> bool:
    return any(domain == o or domain.endswith("." + o) for o in own if o)


def cited_domains(ejecuciones_csv: Path) -> list[str]:
    df = read_csv_flex(Path(ejecuciones_csv))
    col = next((c for c in df.columns if c.replace("﻿", "").strip() == "Fuentes citadas"), None)
    out: dict[str, None] = {}
    if col is not None:
        for v in df[col]:
            for d in split_domains(v):
                dom = extract_domain(d)
                if dom:
                    out[dom] = None
    return list(out)


def _classify_batch(dominios: list[str], provider: str, model: str | None) -> dict[str, str]:
    payload = "<datos>" + json.dumps({"dominios": dominios}, ensure_ascii=False) + "</datos>"
    res = _llm.complete_json(
        prompt_text(PROMPT_VERSION),
        payload,
        ClasificacionDominios,
        model=model,
        prompt_version=PROMPT_VERSION,
        mock_builder=lambda: ClasificacionDominios(
            dominios=[ClasifDominio(dominio=d, tipo=heuristic_type(d)) for d in dominios]
        ),
        provider=provider,
    )
    out: dict[str, str] = {}
    for item in res.dominios:
        d = extract_domain(item.dominio)
        if d in dominios and item.tipo in TIPOS_FUENTE_CLASIFICABLES:
            out[d] = item.tipo
    return out


def classify_sources(
    study_dir: Path,
    marcas: list[Any] | None = None,
    *,
    reference: bool | None = None,
    brief_text: str | None = None,
    ficha_marca: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    cache_path: Path | None = None,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> SourcesResult:
    """Clasifica los dominios citados en `study/ejecuciones.csv` que no están en el catálogo y escribe `study/fuentes_catalogo.csv`.

    Orden: dominio propio de una marca → `Web propia` (código); caché global por dominio; LLM por lotes de 30;
    respaldo por reglas del dominio. La calidad sale de `SOURCE_QUALITY_BY_TYPE` (código, no LLM).
    Modo de referencia: copia el catálogo del kit.
    """
    study_dir = Path(study_dir)
    dst = study_dir / "fuentes_catalogo.csv"
    if reference is None:
        reference, _ = _reference.detect_reference(
            brief_text=brief_text, csv_paths=None, prospect_brand=ficha_marca, prospect_domain=None
        )
    if reference:
        study_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_reference.REFERENCE_DIR / "fuentes_catalogo.csv", dst)
        n = len(pd.read_csv(dst, encoding="utf-8-sig", dtype=str))
        return SourcesResult(catalogo_csv=dst, total_dominios=n)

    citados = cited_domains(study_dir / "ejecuciones.csv")
    if marcas is None:
        mp = study_dir / "marcas.csv"
        marcas = read_marcas_csv(mp) if mp.exists() else []
    propios = {extract_domain(m.dominio) for m in marcas if getattr(m, "dominio", "")}

    # catálogo ya existente en el proyecto (subido o de una ejecución anterior)
    existentes: dict[str, tuple[str, str]] = {}
    if dst.exists():
        old = read_csv_flex(dst)
        for _, r in old.iterrows():
            dom = extract_domain(str(r.get("Dominio", "")))
            if dom:
                existentes[dom] = (str(r["Tipo_de_fuente"]).strip(), str(r["Calidad_de_fuente_0_1"]).strip())

    faltan = [d for d in citados if d not in existentes]
    nuevos: dict[str, str] = {}
    res = SourcesResult(catalogo_csv=dst, total_dominios=len(citados), nuevos=len(faltan), dominios_nuevos=list(faltan))

    pendientes: list[str] = []
    cpath = cache_path or global_cache_path()
    cache = _load_cache(cpath)
    for d in faltan:
        if is_own_domain(d, propios):
            nuevos[d] = "Web propia"
            res.web_propia += 1
        elif d in cache:
            nuevos[d] = cache[d]
            res.desde_cache += 1
        else:
            pendientes.append(d)

    prov = active_provider(provider)
    lotes = [pendientes[i : i + BATCH_SIZE] for i in range(0, len(pendientes), BATCH_SIZE)]
    por_guardar: dict[str, str] = {}
    for n, lote in enumerate(lotes, start=1):
        if on_progress:
            on_progress("fuentes", n - 1, len(lotes))
        clasif = _classify_batch(lote, prov, model)
        for d in lote:
            if d in clasif:
                nuevos[d] = clasif[d]
                if prov != "mock":
                    res.clasificados_llm += 1
                    por_guardar[d] = clasif[d]
                else:
                    res.heuristicos += 1
            else:
                nuevos[d] = heuristic_type(d)
                res.heuristicos += 1
    if on_progress and lotes:
        on_progress("fuentes", len(lotes), len(lotes))
    if por_guardar:
        _save_cache(cpath, por_guardar)

    rows = [{"Dominio": d, "Tipo_de_fuente": t, "Calidad_de_fuente_0_1": q} for d, (t, q) in existentes.items()]
    for d in sorted(nuevos):
        rows.append({"Dominio": d, "Tipo_de_fuente": nuevos[d], "Calidad_de_fuente_0_1": str(quality(nuevos[d]))})
    write_csv(pd.DataFrame(rows, columns=FUENTES_COLUMNS), dst)
    return res
