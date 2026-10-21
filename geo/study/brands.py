"""WC2 · Propuesta de marcas del estudio (B2.1)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from geo import llm as _llm
from geo import openrouter as _openrouter
from geo import reference as _reference
from geo.schemas import FichaMarca
from geo.study.common import (
    MARCAS_COLUMNS,
    active_provider,
    extract_domain,
    norm_name,
    proposer_model,
    prompt_text,
    read_csv_flex,
    setting_int,
    split_pipe,
    track_usage,
    write_csv,
    write_json,
)

PROMPT_VERSION = "brands_v1"
DEFAULT_MAX_FOCO = 4
DEFAULT_MAX_TOTAL = 12
MAX_ALIAS = 4

ROL_MARCA = "MARCA DEL BRIEF"
ROL_DECLARADO = "competidor declarado"
ROL_DETECTADO = "competidor detectado"
ROL_LIDER = "líder de mercado"
ROL_CONTEXTO = "contexto"


class MarcaPropuesta(BaseModel):
    nombre: str
    nivel: Literal["foco", "contexto"]
    rol: str  # "MARCA DEL BRIEF", "competidor declarado", "competidor detectado", "líder de mercado", "contexto"
    dominio: str = ""  # dominio propio sin www
    alias: list[str] = Field(default_factory=list)  # 0-4 alias reales
    motivo: str = ""  # por qué se incluye (≤ 200 caracteres)
    fuente_url: str | None = None  # URL que lo respalda


class PropuestaMarcas(BaseModel):
    marcas: list[MarcaPropuesta]


class ProposalError(RuntimeError):
    """La propuesta del modelo no se pudo validar ni corregir."""


# ---------------------------------------------------------------- CSV de marcas


def marcas_to_df(marcas: list[MarcaPropuesta]) -> pd.DataFrame:
    rows = [
        {
            "Marca": m.nombre,
            "Nivel": m.nivel,
            "Rol": m.rol,
            "Dominio_propio": m.dominio,
            "Alias": " | ".join(m.alias),
        }
        for m in marcas
    ]
    return pd.DataFrame(rows, columns=MARCAS_COLUMNS)


def write_marcas_csv(study_dir: Path, marcas: list[MarcaPropuesta]) -> Path:
    """Escribe `study/marcas.csv` con las columnas del kit."""
    path = Path(study_dir) / "marcas.csv"
    write_csv(marcas_to_df(marcas), path)
    return path


def read_marcas_csv(path: Path) -> list[MarcaPropuesta]:
    df = read_csv_flex(Path(path))
    cols = {c.replace("﻿", "").strip(): c for c in df.columns}
    out: list[MarcaPropuesta] = []
    for _, r in df.iterrows():
        nivel = str(r[cols["Nivel"]]).strip().lower()
        rol = str(r[cols["Rol"]]).strip()
        out.append(
            MarcaPropuesta(
                nombre=str(r[cols["Marca"]]).strip(),
                nivel="foco" if nivel == "foco" else "contexto",
                rol=rol,
                dominio=str(r[cols["Dominio_propio"]]).strip().lower(),
                alias=split_pipe(r[cols["Alias"]]) if "Alias" in cols else [],
                motivo=rol[:200],
            )
        )
    return out


def limits() -> tuple[int, int]:
    """(máximo de marcas foco, máximo total), configurables con STUDY_MAX_FOCO y STUDY_MAX_MARCAS."""
    return setting_int("STUDY_MAX_FOCO", DEFAULT_MAX_FOCO), setting_int("STUDY_MAX_MARCAS", DEFAULT_MAX_TOTAL)


# ---------------------------------------------------------------- validación por código


def _same_brand(a: str, b: str, alias_a: list[str] | None = None) -> bool:
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if alias_a and any(norm_name(x) == nb for x in alias_a):
        return True
    # «Nítida» frente a «Láser Nítida»: una contiene a la otra como palabras completas
    return f" {na} " in f" {nb} " or f" {nb} " in f" {na} "


def _clean(m: MarcaPropuesta) -> MarcaPropuesta:
    dom = extract_domain(m.dominio) if m.dominio else ""
    alias: list[str] = []
    for a in m.alias:
        a = a.strip()
        if a and norm_name(a) != norm_name(m.nombre) and all(norm_name(a) != norm_name(x) for x in alias):
            alias.append(a)
    url = (m.fuente_url or "").strip() or None
    return MarcaPropuesta(
        nombre=m.nombre.strip(),
        nivel=m.nivel,
        rol=(m.rol or ROL_CONTEXTO).strip(),
        dominio=dom,
        alias=alias[:MAX_ALIAS],
        motivo=(m.motivo or "").strip()[:200],
        fuente_url=url,
    )


def validate_brands(
    prop: PropuestaMarcas,
    ficha: FichaMarca,
    *,
    max_foco: int | None = None,
    max_total: int | None = None,
) -> PropuestaMarcas:
    """Aplica las reglas de B2.1: marca del brief siempre presente y foco, competidores declarados presentes,
    máximo de foco y de total, dominios normalizados y sin duplicados por nombre ni por dominio."""
    cfg_foco, cfg_total = limits()
    max_foco = max_foco or cfg_foco
    max_total = max_total or cfg_total

    # 1. limpiar y deduplicar por nombre normalizado y por dominio (conserva la primera aparición)
    limpias: list[MarcaPropuesta] = []
    nombres: set[str] = set()
    dominios: set[str] = set()
    for raw in prop.marcas:
        if not raw.nombre.strip():
            continue
        m = _clean(raw)
        nn = norm_name(m.nombre)
        if nn in nombres or (m.dominio and m.dominio in dominios):
            continue
        nombres.add(nn)
        if m.dominio:
            dominios.add(m.dominio)
        limpias.append(m)

    # 2. marca del brief
    idx_marca = next((i for i, m in enumerate(limpias) if _same_brand(ficha.marca, m.nombre, m.alias)), None)
    if idx_marca is None:
        dom = extract_domain(ficha.web) if ficha.web else ""
        marca = MarcaPropuesta(
            nombre=ficha.marca.strip(),
            nivel="foco",
            rol=ROL_MARCA,
            dominio=dom,
            alias=[],
            motivo="Marca del proyecto.",
        )
    else:
        marca = limpias.pop(idx_marca)
        marca = marca.model_copy(update={"nivel": "foco", "rol": ROL_MARCA})
        if not marca.dominio and ficha.web:
            marca = marca.model_copy(update={"dominio": extract_domain(ficha.web)})
    resto = [
        m.model_copy(update={"rol": ROL_DETECTADO}) if m.rol.strip().upper() == ROL_MARCA else m for m in limpias
    ]

    # 3. competidores declarados
    declarados: list[MarcaPropuesta] = []
    for nombre in ficha.competidores_declarados:
        nombre = nombre.strip()
        if not nombre or _same_brand(nombre, marca.nombre, marca.alias):
            continue
        idx = next((i for i, m in enumerate(resto) if _same_brand(nombre, m.nombre, m.alias)), None)
        if idx is None:
            declarados.append(
                MarcaPropuesta(
                    nombre=nombre,
                    nivel="foco",
                    rol=ROL_DECLARADO,
                    dominio="",
                    alias=[],
                    motivo="Competidor declarado en el brief.",
                )
            )
        else:
            m = resto.pop(idx)
            rol = m.rol if norm_name(m.rol) == norm_name(ROL_LIDER) else ROL_DECLARADO
            declarados.append(m.model_copy(update={"rol": rol}))

    # 4. orden de prioridad: marca, declarados, resto con foco primero, líder antes que el contexto
    def _rank(m: MarcaPropuesta) -> tuple[int, int]:
        return (0 if m.nivel == "foco" else 1, 0 if norm_name(m.rol) == norm_name(ROL_LIDER) else 1)

    resto.sort(key=_rank)
    ordenadas = [marca, *declarados, *resto]

    # 5. máximo de foco (la marca y los declarados primero) y máximo total
    focos = 0
    final: list[MarcaPropuesta] = []
    for m in ordenadas:
        if m.nivel == "foco":
            if focos >= max_foco:
                m = m.model_copy(update={"nivel": "contexto"})
            else:
                focos += 1
        final.append(m)
    obligatorias = 1 + len(declarados)
    final = final[: max(max_total, obligatorias)]
    return PropuestaMarcas(marcas=final)


# ---------------------------------------------------------------- generadores


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm_name(text)).strip("-") or "marca"


def mock_proposal(ficha: FichaMarca) -> PropuestaMarcas:
    """Propuesta determinista sin red: la marca del brief y sus competidores declarados."""
    marcas = [
        MarcaPropuesta(
            nombre=ficha.marca,
            nivel="foco",
            rol=ROL_MARCA,
            dominio=extract_domain(ficha.web) if ficha.web else f"{_slug(ficha.marca)}.example",
            alias=[],
            motivo="Marca del proyecto.",
        )
    ]
    for c in ficha.competidores_declarados:
        marcas.append(
            MarcaPropuesta(
                nombre=c,
                nivel="foco",
                rol=ROL_DECLARADO,
                dominio=f"{_slug(c)}.example",
                alias=[],
                motivo="Competidor declarado en el brief.",
            )
        )
    return PropuestaMarcas(marcas=marcas)


def _ficha_payload(ficha: FichaMarca, max_foco: int, max_total: int) -> str:
    data = {
        "ficha": {
            "marca": ficha.marca,
            "web": ficha.web,
            "sector": ficha.sector,
            "subsector": ficha.subsector,
            "servicios_prioritarios": ficha.servicios_prioritarios,
            "ciudades": ficha.ciudades,
            "competidores_declarados": ficha.competidores_declarados,
        },
        "limites": {"max_foco": max_foco, "max_total": max_total},
    }
    return "<datos>" + json.dumps(data, ensure_ascii=False) + "</datos>"


def _extract_json(text: str) -> dict:
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, flags=re.DOTALL)
    if m:
        t = m.group(1)
    else:
        a, b = t.find("{"), t.rfind("}")
        if a != -1 and b >= a:
            t = t[a : b + 1]
    return json.loads(t)


def _call_with_search(ficha: FichaMarca, model: str, max_foco: int, max_total: int) -> PropuestaMarcas:
    schema_hint = json.dumps(PropuestaMarcas.model_json_schema(), ensure_ascii=False)
    system = (
        prompt_text(PROMPT_VERSION)
        + "\n\nDevuelve EXCLUSIVAMENTE un objeto JSON válido que cumpla este JSON Schema:\n"
        + schema_hint
    )
    user = _ficha_payload(ficha, max_foco, max_total)
    last_err: Exception | None = None
    for intento in range(2):
        content = user if last_err is None else (
            f"{user}\n\nTu respuesta anterior no fue válida ({last_err}). Devuelve únicamente el JSON válido."
        )
        try:
            res = _openrouter.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": content}],
                model=model,
                temperature=0.0,
                json_mode=True,
                web_search=True,
                max_tokens=4000,
                retries=2,
            )
        except _openrouter.OpenRouterError as exc:
            if not getattr(exc, "retryable", False):
                raise _llm.LLMConfigError(str(exc)) from exc
            raise _llm.LLMProviderError(str(exc)) from exc
        track_usage(res.model or model, res.tokens_in, res.tokens_out, res.cost_usd, PROMPT_VERSION)
        try:
            prop = PropuestaMarcas.model_validate(_extract_json(res.text))
            # URLs de la búsqueda web como respaldo cuando el modelo no informa fuente_url
            for m in prop.marcas:
                if not m.fuente_url:
                    dom = extract_domain(m.dominio) if m.dominio else ""
                    m.fuente_url = next((u for u in res.citations if dom and dom in u), None)
            return prop
        except (json.JSONDecodeError, ValidationError) as exc:
            last_err = exc
    raise ProposalError(f"El modelo no devolvió una propuesta de marcas válida: {last_err}")


# ---------------------------------------------------------------- API pública


def propose_brands(
    ficha: FichaMarca,
    *,
    study_dir: Path | None = None,
    reference: bool | None = None,
    brief_text: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    write: bool = True,
) -> PropuestaMarcas:
    """Propone las marcas del estudio a partir de la ficha.

    - Modo de referencia (`reference=True`, o detectado con `geo.reference` si es `None`): devuelve las marcas
      de `marcas.csv` del kit sin ninguna llamada de red.
    - Proveedor `mock`: propuesta determinista (marca del brief + competidores declarados).
    - Proveedor `openrouter`: modelo `LLM_MODEL_PROPOSER` con búsqueda web, validado por código.

    Con `study_dir` y `write=True` guarda `propuesta_marcas.json` y `marcas.csv`.
    """
    if reference is None:
        reference, _ = _reference.detect_reference(
            brief_text=brief_text,
            csv_paths=None,
            prospect_brand=ficha.marca,
            prospect_domain=extract_domain(ficha.web) if ficha.web else None,
        )
    if reference:
        prop = PropuestaMarcas(marcas=read_marcas_csv(_reference.REFERENCE_DIR / "marcas.csv"))
        if study_dir is not None and write:
            Path(study_dir).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(_reference.REFERENCE_DIR / "marcas.csv", Path(study_dir) / "marcas.csv")
            write_json(Path(study_dir) / "propuesta_marcas.json", prop)
        return prop

    max_foco, max_total = limits()
    prov = active_provider(provider)
    if prov == "mock":
        raw = mock_proposal(ficha)
    else:
        raw = _call_with_search(ficha, model or proposer_model(), max_foco, max_total)
    prop = validate_brands(raw, ficha, max_foco=max_foco, max_total=max_total)
    if study_dir is not None and write:
        Path(study_dir).mkdir(parents=True, exist_ok=True)
        write_json(Path(study_dir) / "propuesta_marcas.json", raw)
        write_marcas_csv(Path(study_dir), prop.marcas)
    return prop
