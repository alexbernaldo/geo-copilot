"""Perfiles de sector (D3): textos y reglas que dependen del sector y no se deducen de los datos.

Un perfil (`geo/sector_profiles/<id>.yaml`) puede heredar de otro con `extiende`. Las secciones
`acciones` (por `template_id`) y `fases` (por número) se fusionan entrada a entrada; el resto de
claves del perfil hijo sustituyen a las del padre (los diccionarios se fusionan en profundidad).

Marcadores admitidos en los textos: `{marca}`, `{ciudades}`, `{ciudad_principal}`,
`{ciudad_crecimiento}`, `{servicios_prioritarios}`, `{diferencial}`, `{n_prompts}`,
`{n_ejecuciones}`, `{dom_directorios}`, `{dom_medios}`, `{dom_resenas}`, `{dom_rankings}`,
`{dom_foros}` y las variantes `*_coma`.
"""

from __future__ import annotations

import copy
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from geo.schemas import FichaMarca
from geo.text import normalize

PROFILES_DIR: Path = Path(__file__).resolve().parent / "sector_profiles"
DEFAULT_PROFILE_ID = "general"
KIT_PROFILE_ID = "referencia_kit"
_TEXT_KEYS = ("titulo", "descripcion", "kpi_tipo", "entregables_tipo")


class _SafeDict(dict):
    """Deja intactos los marcadores desconocidos en lugar de fallar."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _deep_merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


@lru_cache(maxsize=None)
def _load_cached(profile_id: str) -> dict[str, Any]:
    path = PROFILES_DIR / f"{profile_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No existe el perfil de sector '{profile_id}' en {PROFILES_DIR}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    parent = raw.get("extiende")
    if parent:
        raw = _deep_merge(_load_cached(str(parent)), {k: v for k, v in raw.items() if k != "extiende"})
    raw["id"] = profile_id
    return raw


def load_profile(profile_id: str) -> dict[str, Any]:
    """Devuelve una copia del perfil `profile_id` ya fusionado con sus ancestros."""
    return copy.deepcopy(_load_cached(profile_id))


def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILES_DIR.glob("*.yaml"))


def _is_kit_brand(marca: str) -> bool:
    from geo.reference import REFERENCE_BRAND, normalize_for_fingerprint

    return normalize_for_fingerprint(marca) == normalize_for_fingerprint(REFERENCE_BRAND)


def select_profile(ficha: FichaMarca | None = None, profile_id: str | None = None) -> dict[str, Any]:
    """Elige el perfil: el indicado, el del kit (si la marca es la del kit) o el que case con el sector."""
    if profile_id:
        return load_profile(profile_id)
    if ficha is None:
        return load_profile(DEFAULT_PROFILE_ID)
    if ficha.marca and _is_kit_brand(ficha.marca):
        return load_profile(KIT_PROFILE_ID)
    texto = normalize(
        " ".join(
            [ficha.sector or "", ficha.subsector or "", *ficha.servicios, *ficha.restricciones_normativas]
        )
    )
    for pid in list_profiles():
        if pid in (DEFAULT_PROFILE_ID, KIT_PROFILE_ID):
            continue
        prof = _load_cached(pid)
        claves = [normalize(c) for c in prof.get("detectar_si", [])]
        if any(c and c in texto for c in claves):
            return load_profile(pid)
    return load_profile(DEFAULT_PROFILE_ID)


# ---------- Contexto de marcadores ----------
def _join_es(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " y " + items[-1]


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s


def action_context(
    ficha: FichaMarca,
    domains_by_type: dict[str, list[str]] | None = None,
    *,
    n_prompts: int | None = None,
    n_ejecuciones: int | None = None,
) -> dict[str, str]:
    """Valores de los marcadores a partir de la ficha y del catálogo de fuentes del proyecto."""
    if domains_by_type is None:
        from geo.config import get_catalog_domains_by_type

        by_type = get_catalog_domains_by_type()
    else:
        by_type = domains_by_type
    ciudades = [c for c in ficha.ciudades if c]
    principal = ficha.ciudad_principal or (ciudades[0] if ciudades else "")
    crecimiento = ficha.ciudad_crecimiento or next((c for c in ciudades if c != principal), principal)

    def doms(tipo: str, solo_example: bool = False) -> list[str]:
        ds = by_type.get(tipo, [])
        if solo_example:
            ds = [d for d in ds if d.endswith(".example")] or ds
        return ds

    def lst(tipo: str, vacio: str, solo_example: bool = False) -> tuple[str, str]:
        ds = doms(tipo, solo_example)
        return (_join_es(ds) or vacio, ", ".join(ds) or vacio)

    dir_, dir_c = lst("Directorio / comparador", "los directorios sectoriales")
    med, med_c = lst("Medio", "los medios especializados")
    res, res_c = lst("Plataforma de reseñas", "las plataformas de reseñas")
    ran, ran_c = lst("Ranking / institución", "los rankings y guías del sector", solo_example=True)
    for_, for_c = lst("Red social / foro", "los foros y comunidades del sector", solo_example=True)
    serv = [_lower_first(s) for s in ficha.servicios_prioritarios if s]
    return {
        "marca": ficha.marca,
        "ciudades": " y ".join(ciudades[:2]) or principal,
        "ciudad_principal": principal,
        "ciudad_crecimiento": crecimiento,
        "servicios_prioritarios": _join_es(serv) or "los servicios prioritarios",
        "diferencial": _lower_first(ficha.diferenciales[0]) if ficha.diferenciales else "su propuesta diferencial",
        "n_prompts": str(n_prompts) if n_prompts is not None else "",
        "n_ejecuciones": str(n_ejecuciones) if n_ejecuciones is not None else "",
        "dom_directorios": dir_,
        "dom_directorios_coma": dir_c,
        "dom_medios": med,
        "dom_medios_coma": med_c,
        "dom_resenas": res,
        "dom_resenas_coma": res_c,
        "dom_rankings": ran,
        "dom_rankings_coma": ran_c,
        "dom_foros": for_,
        "dom_foros_coma": for_c,
    }


def render_text(text: str, ctx: dict[str, str]) -> str:
    return text.format_map(_SafeDict(ctx))


# ---------- Acciones ----------
def raw_action_library(profile_id: str = DEFAULT_PROFILE_ID) -> list[dict[str, object]]:
    """Esqueleto + textos del perfil sin rellenar marcadores."""
    from geo.config import ACTION_SKELETON

    acciones = load_profile(profile_id).get("acciones", {})
    out: list[dict[str, object]] = []
    for sk in ACTION_SKELETON:
        tpl = dict(sk)
        tpl.update(acciones.get(str(sk["template_id"]), {}))
        out.append(tpl)
    return out


def build_action_library(
    profile: dict[str, Any], ctx: dict[str, str]
) -> list[dict[str, object]]:
    """Biblioteca de acciones con los textos del perfil y los marcadores rellenados."""
    from geo.config import ACTION_SKELETON

    acciones = profile.get("acciones", {})
    out: list[dict[str, object]] = []
    for sk in ACTION_SKELETON:
        tpl = dict(sk)
        textos = acciones.get(str(sk["template_id"]), {})
        for k in _TEXT_KEYS:
            if k not in textos:
                continue
            v = textos[k]
            tpl[k] = [render_text(str(e), ctx) for e in v] if isinstance(v, list) else render_text(str(v), ctx)
        out.append(tpl)
    return out


def phase_defs(
    profile: dict[str, Any], ctx: dict[str, str], semanas: dict[int, tuple[int, int]]
) -> dict[int, tuple[str, tuple[int, int], str]]:
    """Definición de las 4 fases del plan: nombre y objetivo del perfil, semanas fijas."""
    fases = {int(k): v for k, v in profile.get("fases", {}).items()}
    return {
        n: (
            render_text(str(fases[n]["nombre"]), ctx),
            semanas[n],
            render_text(str(fases[n]["objetivo"]), ctx),
        )
        for n in semanas
    }


# ---------- Normativa ----------
def compliance_rules(profile: dict[str, Any]) -> list[tuple[re.Pattern[str], str]]:
    """Reglas regex de promesas/superlativos del perfil como (patrón, sugerencia)."""
    reglas = profile.get("normativa", {}).get("prohibidas_regex", [])
    out: list[tuple[re.Pattern[str], str]] = []
    for r in reglas:
        out.append((re.compile(str(r["patron"]), flags=re.IGNORECASE), str(r["sugerencia"])))
    return out


def plan_texts(profile: dict[str, Any], ctx: dict[str, str]) -> dict[str, Any]:
    """Textos del plan (medición, riesgos, supuestos) con marcadores rellenados."""
    p = profile.get("plan", {})
    return {
        "medicion": render_text(str(p.get("medicion", "")), ctx),
        "riesgos": [render_text(str(x), ctx) for x in p.get("riesgos", [])],
        "supuestos": [render_text(str(x), ctx) for x in p.get("supuestos", [])],
    }
