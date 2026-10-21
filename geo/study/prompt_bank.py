"""WC2 · Propuesta del banco de prompts e instanciación por código (B2.2)."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, Field

from geo import llm as _llm
from geo import reference as _reference
from geo.schemas import FichaMarca, Prompt
from geo.study.brands import MarcaPropuesta, read_marcas_csv
from geo.study.common import (
    BANCO_COLUMNS,
    active_provider,
    extract_domain,
    norm_name,
    prompt_text,
    proposer_model,
    read_csv_flex,
    strip_accents,
    write_csv,
    write_json,
)

PROMPT_VERSION = "prompt_bank_v1"
MAX_CIUDADES = 3
MAX_PARES = 6

# Código → (nombre de la familia, intención, instanciaciones permitidas)
FAMILIAS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "DG": ("Descubrimiento genérico", "Descubrimiento", ("generico",)),
    "DP": ("Descubrimiento por perfil", "Descubrimiento", ("generico",)),
    "LO": ("Localización", "Descubrimiento", ("ciudad",)),
    "CO": ("Comparación de opciones", "Comparación", ("generico",)),
    "CM": ("Comparación de marcas", "Comparación", ("par", "marca")),
    "VR": ("Validación reputacional", "Validación", ("marca",)),
    "FU": ("Fuentes y citación", "Validación", ("generico",)),
    "DF": ("Decisión final", "Decisión", ("generico", "marca")),
    "PR": ("Precio y valor", "Decisión", ("generico",)),
}
_CODIGO_POR_NOMBRE = {norm_name(v[0]): k for k, v in FAMILIAS.items()}

NOTAS_INSTANCIACION: dict[str, str] = {
    "generico": "Una sola ejecución; se evalúan todas las marcas del sector",
    "ciudad": "Se instancia con cada ciudad; se evalúan todas las marcas",
    "marca": "Se instancia con cada marca foco; se evalúa solo esa marca",
    "par": "Pares estratégicos: marca del proyecto contra cada foco y líder contra cada foco",
}


class PlantillaLLM(BaseModel):
    familia: str  # código DG, DP, LO, CO, CM, VR, FU, DF, PR
    prioridad: Literal["P1", "P2"] = "P1"
    uso: Literal["Publicable", "Diagnóstico"] = "Publicable"
    instanciacion: Literal["generico", "ciudad", "marca", "par"]
    plantilla: str


class PropuestaBancoLLM(BaseModel):
    plantillas: list[PlantillaLLM] = Field(default_factory=list)


class PropuestaBanco(BaseModel):
    prompts: list[Prompt]
    descartados: list[dict[str, str]] = Field(default_factory=list)  # {plantilla, motivo}


class PromptInstanciado(BaseModel):
    prompt_id: str
    prompt: str
    instanciacion: Literal["generico", "ciudad", "marca", "par"]
    marcas_a_evaluar: list[str]
    ciudad: str | None = None
    familia: str = ""
    intencion: str = ""
    prioridad: str = "P1"
    uso: str = "Publicable"


# ---------------------------------------------------------------- CSV del banco


def banco_to_df(bank: list[Prompt], sector: str) -> pd.DataFrame:
    rows = [
        {
            "Prompt_ID": p.prompt_id,
            "Sector": sector,
            "Familia": p.familia,
            "Intención": p.intencion,
            "Prioridad": p.prioridad,
            "Uso": p.uso,
            "Instanciación": p.instanciacion,
            "Prompt (plantilla)": p.plantilla,
            "Notas de instanciación": NOTAS_INSTANCIACION.get(p.instanciacion, ""),
        }
        for p in bank
    ]
    return pd.DataFrame(rows, columns=BANCO_COLUMNS)


def write_banco_csv(study_dir: Path, bank: list[Prompt], sector: str) -> Path:
    path = Path(study_dir) / "banco_prompts.csv"
    write_csv(banco_to_df(bank, sector), path)
    return path


def read_banco_csv(path: Path) -> list[Prompt]:
    df = read_csv_flex(Path(path))
    cols = {c.replace("﻿", "").strip(): c for c in df.columns}
    out: list[Prompt] = []
    for _, r in df.iterrows():
        out.append(
            Prompt(
                prompt_id=str(r[cols["Prompt_ID"]]).strip(),
                familia=str(r[cols["Familia"]]).strip(),
                intencion=str(r[cols["Intención"]]).strip(),  # type: ignore[arg-type]
                prioridad=str(r[cols["Prioridad"]]).strip(),
                uso=str(r[cols["Uso"]]).strip(),
                instanciacion=str(r[cols["Instanciación"]]).strip(),  # type: ignore[arg-type]
                plantilla=str(r[cols["Prompt (plantilla)"]]).strip(),
            )
        )
    return out


# ---------------------------------------------------------------- validación por código

_MARKERS = ("[CIUDAD]", "[MARCA_A]", "[MARCA_B]")
_ID_RX = re.compile(r"^[A-Z]{3}-(DG|DP|LO|CO|CM|VR|FU|DF|PR)-\d{2}$")
_STOP = {"de", "del", "la", "las", "los", "el", "y", "en", "para", "con", "por", "un", "una"}


def sector_code(ficha: FichaMarca) -> str:
    """Tres letras del sector para el Prompt_ID: usa lo que va entre paréntesis si lo hay."""
    base = ficha.sector or ficha.subsector or "GEN"
    m = re.search(r"\(([^)]+)\)", base)
    if m:
        base = m.group(1)
    for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+", base):
        if norm_name(w) not in _STOP and len(strip_accents(w)) >= 3:
            return strip_accents(w).upper()[:3]
    letters = re.sub(r"[^A-Z]", "", strip_accents(base).upper())
    return (letters + "XXX")[:3]


def marker_problem(instanciacion: str, plantilla: str) -> str:
    """Devuelve el motivo si los marcadores no corresponden a la instanciación; cadena vacía si son correctos."""
    presentes = {m for m in _MARKERS if m in plantilla}
    esperados = {
        "generico": set(),
        "ciudad": {"[CIUDAD]"},
        "marca": {"[MARCA_A]"},
        "par": {"[MARCA_A]", "[MARCA_B]"},
    }[instanciacion]
    if presentes != esperados:
        falta = ", ".join(sorted(esperados - presentes))
        sobra = ", ".join(sorted(presentes - esperados))
        partes = []
        if falta:
            partes.append(f"falta {falta}")
        if sobra:
            partes.append(f"sobra {sobra}")
        return f"marcadores incorrectos para «{instanciacion}»: " + " y ".join(partes)
    return ""


def names_brand(plantilla: str, marcas: list[Any]) -> str | None:
    """Devuelve el nombre de la primera marca (o alias) que aparece en la plantilla, o None."""
    texto = f" {norm_name(plantilla)} "
    for m in marcas:
        candidatos = [m.nombre, *list(getattr(m, "alias", []) or [])]
        for c in candidatos:
            n = norm_name(c)
            if len(n) >= 3 and f" {n} " in texto:
                return c
    return None


def validate_bank(
    prop: PropuestaBancoLLM,
    ficha: FichaMarca,
    marcas: list[Any],
    *,
    ya_validas: list[Prompt] | None = None,
) -> PropuestaBanco:
    """Valida las plantillas del modelo y les asigna Prompt_ID `<SECTOR3>-<FAMILIA>-<nn>`.

    Rechaza: familia desconocida, instanciación no permitida para la familia, marcadores incorrectos,
    plantillas espontáneas (`generico`/`ciudad`) que nombran una marca, plantillas vacías o repetidas.
    """
    s3 = sector_code(ficha)
    validas: list[Prompt] = list(ya_validas or [])
    descartados: list[dict[str, str]] = []
    vistos = {norm_name(p.plantilla) for p in validas}
    contador: dict[str, int] = {}
    for p in validas:
        m = re.match(r"^[A-Z]{3}-([A-Z]{2})-(\d{2})$", p.prompt_id)
        if m:
            contador[m.group(1)] = max(contador.get(m.group(1), 0), int(m.group(2)))

    for pl in prop.plantillas:
        texto = pl.plantilla.strip()
        codigo = pl.familia.strip().upper()
        if codigo not in FAMILIAS:
            codigo = _CODIGO_POR_NOMBRE.get(norm_name(pl.familia), "")
        motivo = ""
        if codigo not in FAMILIAS:
            motivo = f"familia desconocida «{pl.familia}»"
        elif len(texto) < 10:
            motivo = "plantilla vacía o demasiado corta"
        elif pl.instanciacion not in FAMILIAS[codigo][2]:
            motivo = f"la familia {codigo} no admite la instanciación «{pl.instanciacion}»"
        else:
            motivo = marker_problem(pl.instanciacion, texto)
            if not motivo and pl.instanciacion in ("generico", "ciudad"):
                marca = names_brand(texto, marcas)
                if marca:
                    motivo = f"una plantilla espontánea nombra a «{marca}»"
            if not motivo and norm_name(texto) in vistos:
                motivo = "plantilla repetida"
        if motivo:
            descartados.append({"plantilla": texto, "motivo": motivo})
            continue
        nombre, intencion, _ = FAMILIAS[codigo]
        contador[codigo] = contador.get(codigo, 0) + 1
        vistos.add(norm_name(texto))
        validas.append(
            Prompt(
                prompt_id=f"{s3}-{codigo}-{contador[codigo]:02d}",
                familia=nombre,
                intencion=intencion,  # type: ignore[arg-type]
                prioridad=pl.prioridad,
                uso=pl.uso,
                instanciacion=pl.instanciacion,
                plantilla=texto,
            )
        )
    orden = list(FAMILIAS)

    def _clave(p: Prompt) -> tuple[int, str]:
        codigo = p.prompt_id.split("-")[1] if "-" in p.prompt_id else ""
        return (orden.index(codigo) if codigo in orden else len(orden), p.prompt_id)

    validas.sort(key=_clave)
    return PropuestaBanco(prompts=validas, descartados=descartados)


def missing_families(bank: list[Prompt]) -> list[str]:
    presentes = {p.prompt_id.split("-")[1] for p in bank if _ID_RX.match(p.prompt_id)}
    return [c for c in FAMILIAS if c not in presentes]


# ---------------------------------------------------------------- plantillas simuladas (proveedor mock)

# (familia, prioridad, uso, instanciación, plantilla con {sector} y {servicio})
MOCK_TEMPLATES: list[tuple[str, str, str, str, str]] = [
    ("DG", "P1", "Publicable", "generico", "¿Cuáles son las mejores opciones de {sector} en España?"),
    ("DG", "P1", "Publicable", "generico", "Estoy buscando {servicio}. ¿Qué empresas o centros me recomendarías en España?"),
    ("DG", "P2", "Publicable", "generico", "¿Qué proveedores de {sector} destacan ahora mismo en España?"),
    ("DP", "P1", "Publicable", "generico", "Soy un particular y necesito {servicio}. ¿Qué opciones de {sector} me recomendarías?"),
    ("DP", "P1", "Publicable", "generico", "Tengo poco presupuesto y quiero {servicio}. ¿Qué alternativas fiables hay en {sector}?"),
    ("DP", "P2", "Publicable", "generico", "Busco {servicio} para mi familia. ¿Qué opciones de {sector} son más adecuadas?"),
    ("DP", "P2", "Publicable", "generico", "Somos una empresa y necesitamos {servicio}. ¿Qué proveedores de {sector} recomiendas?"),
    ("LO", "P1", "Publicable", "ciudad", "¿Qué opciones de {sector} recomendadas hay en [CIUDAD]?"),
    ("LO", "P2", "Publicable", "ciudad", "Busco {servicio} en [CIUDAD]. ¿Cuál me recomiendas?"),
    ("CO", "P1", "Publicable", "generico", "¿Qué diferencias hay entre las principales opciones de {sector} en España?"),
    ("CO", "P1", "Publicable", "generico", "¿Qué criterios importan más al comparar opciones de {sector}?"),
    ("CO", "P2", "Publicable", "generico", "¿Qué ventajas e inconvenientes tienen las grandes cadenas frente a los centros independientes en {sector}?"),
    ("CM", "P1", "Publicable", "par", "Diferencias entre [MARCA_A] y [MARCA_B] a la hora de elegir {sector}."),
    ("CM", "P1", "Publicable", "par", "¿[MARCA_A] o [MARCA_B]? ¿Cuál elegirías para {servicio} y por qué?"),
    ("CM", "P1", "Publicable", "marca", "¿Qué ventajas tiene [MARCA_A] frente a otras opciones de {sector}?"),
    ("VR", "P1", "Publicable", "marca", "¿Qué opinión tienen los clientes de [MARCA_A]?"),
    ("VR", "P1", "Publicable", "marca", "¿Qué debería revisar antes de contratar a [MARCA_A]?"),
    ("VR", "P2", "Diagnóstico", "marca", "¿Qué riesgos o inconvenientes debería considerar antes de elegir [MARCA_A]?"),
    ("FU", "P1", "Publicable", "generico", "¿Qué fuentes fiables recomiendan para elegir {sector}?"),
    ("FU", "P2", "Publicable", "generico", "¿Dónde puedo encontrar rankings u opiniones independientes sobre {sector}?"),
    ("DF", "P1", "Publicable", "generico", "Voy a decidirme ya por {servicio}. ¿Qué opción de {sector} elegirías?"),
    ("DF", "P1", "Publicable", "marca", "Estoy a punto de contratar a [MARCA_A]. ¿Es una buena elección o mirarías otra opción?"),
    ("DF", "P2", "Publicable", "generico", "¿Qué opción de {sector} elegirías por relación calidad-precio?"),
    ("PR", "P1", "Publicable", "generico", "¿Cuánto cuesta {servicio} en España y de qué depende el precio?"),
    ("PR", "P2", "Publicable", "generico", "¿Qué opciones de {sector} ofrecen mejor relación calidad-precio?"),
]


def sector_text(ficha: FichaMarca) -> str:
    """Sector en minúsculas y sin paréntesis, para insertarlo en una frase."""
    return re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", ficha.sector or "")).strip().lower() or "este sector"


def servicio_text(ficha: FichaMarca) -> str:
    if ficha.servicios_prioritarios:
        return ficha.servicios_prioritarios[0].strip().lower()
    if ficha.servicios:
        return ficha.servicios[0].strip().lower()
    return sector_text(ficha)


def mock_proposal(ficha: FichaMarca) -> PropuestaBancoLLM:
    s, v = sector_text(ficha), servicio_text(ficha)
    return PropuestaBancoLLM(
        plantillas=[
            PlantillaLLM(
                familia=f, prioridad=pr, uso=u, instanciacion=i, plantilla=t.format(sector=s, servicio=v)  # type: ignore[arg-type]
            )
            for f, pr, u, i, t in MOCK_TEMPLATES
        ]
    )


# ---------------------------------------------------------------- llamada al modelo


def _payload(ficha: FichaMarca, marcas: list[Any], feedback: str = "") -> str:
    data: dict[str, Any] = {
        "ficha": {
            "marca": ficha.marca,
            "sector": ficha.sector,
            "subsector": ficha.subsector,
            "servicios_prioritarios": ficha.servicios_prioritarios,
            "publicos": ficha.publicos,
            "ciudades": ficha.ciudades,
        },
        "marcas": [{"nombre": m.nombre, "nivel": m.nivel, "rol": m.rol} for m in marcas],
    }
    if feedback:
        data["correcciones"] = feedback
    return "<datos>" + json.dumps(data, ensure_ascii=False) + "</datos>"


def _call(
    ficha: FichaMarca,
    marcas: list[Any],
    feedback: str,
    provider: str,
    model: str,
    use_cache: bool = True,
) -> PropuestaBancoLLM:
    if os.environ.get("FAKE_OR_BANK_BAD"):
        use_cache = False
    return _llm.complete_json(
        prompt_text(PROMPT_VERSION),
        _payload(ficha, marcas, feedback),
        PropuestaBancoLLM,
        model=model,
        prompt_version=PROMPT_VERSION,
        mock_builder=lambda: mock_proposal(ficha),
        provider=provider,
        use_cache=use_cache,
    )


# ---------------------------------------------------------------- API pública


def propose_bank(
    ficha: FichaMarca,
    marcas: list[Any],
    *,
    study_dir: Path | None = None,
    reference: bool | None = None,
    brief_text: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    write: bool = True,
    use_cache: bool = True,
) -> PropuestaBanco:
    """Propone el banco de prompts para las 9 familias de la metodología.

    - Modo de referencia: devuelve las 25 plantillas de `banco_prompts.csv` del kit sin red.
    - Resto: LLM (`LLM_MODEL_PROPOSER`, sin búsqueda web), validado por código; si hay plantillas rechazadas o
      familias sin cubrir se pide una corrección al modelo (una sola vez).
    Con `study_dir` y `write=True` guarda `propuesta_banco.json` y `banco_prompts.csv`.
    """
    if reference is None:
        reference, _ = _reference.detect_reference(
            brief_text=brief_text,
            csv_paths=None,
            prospect_brand=ficha.marca,
            prospect_domain=extract_domain(ficha.web) if ficha.web else None,
        )
    if reference:
        prompts = read_banco_csv(_reference.REFERENCE_DIR / "banco_prompts.csv")
        res = PropuestaBanco(prompts=prompts)
        if study_dir is not None and write:
            Path(study_dir).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(_reference.REFERENCE_DIR / "banco_prompts.csv", Path(study_dir) / "banco_prompts.csv")
            write_json(Path(study_dir) / "propuesta_banco.json", res)
        return res

    prov = active_provider(provider)
    mdl = model or proposer_model()
    primera = _call(ficha, marcas, "", prov, mdl, use_cache=use_cache)
    res = validate_bank(primera, ficha, marcas)
    faltan = missing_families(res.prompts)
    if res.descartados or faltan:
        notas = []
        if res.descartados:
            notas.append(
                "Estas plantillas se rechazaron: "
                + "; ".join(f"«{d['plantilla'][:80]}» ({d['motivo']})" for d in res.descartados[:8])
            )
        if faltan:
            notas.append("Faltan plantillas válidas de las familias: " + ", ".join(faltan) + ".")
        segunda = _call(ficha, marcas, " ".join(notas) + " Devuelve el banco completo corregido.", prov, mdl, use_cache=use_cache)
        res2 = validate_bank(segunda, ficha, marcas)
        todos_descartados = list(res.descartados)
        for d in res2.descartados:
            if d not in todos_descartados:
                todos_descartados.append(d)
        if len(res2.prompts) >= len(res.prompts):
            res = PropuestaBanco(prompts=res2.prompts, descartados=todos_descartados)
        else:
            res = PropuestaBanco(prompts=res.prompts, descartados=todos_descartados)
    if not res.prompts:
        from geo.study.brands import ProposalError

        raise ProposalError("El modelo no devolvió ninguna plantilla de prompt válida.")
    if study_dir is not None and write:
        Path(study_dir).mkdir(parents=True, exist_ok=True)
        write_json(Path(study_dir) / "propuesta_banco.json", res)
        write_banco_csv(Path(study_dir), res.prompts, ficha.sector)
    return res


# ---------------------------------------------------------------- instanciación


def _is_marca_proyecto(m: Any) -> bool:
    return bool(getattr(m, "es_marca_brief", False)) or "MARCA DEL BRIEF" in str(m.rol).upper()


def _lider(marcas: list[Any]) -> Any | None:
    candidatas = [m for m in marcas if "lider" in norm_name(m.rol)]
    foco = [m for m in candidatas if m.nivel == "foco"]
    return (foco or candidatas or [None])[0]


def strategic_pairs(marcas: list[Any], max_pares: int = MAX_PARES) -> list[tuple[Any, Any]]:
    """Pares estratégicos (sin repetir, máximo 6).

    Como en el kit, cuando hay dos líderes (uno foco, «de referencia», y otro, el «líder real del mercado»):
    el líder de referencia contra cada otro foco y cada otro foco contra el líder del mercado.
    Con un solo líder: la marca del proyecto contra cada foco y el líder contra cada foco.
    """
    focos = [m for m in marcas if m.nivel == "foco"]
    proyecto = next((m for m in marcas if _is_marca_proyecto(m)), None)
    lideres = [m for m in marcas if "lider" in norm_name(m.rol)]
    ref = next((m for m in lideres if m.nivel == "foco"), None)
    mercado = next((m for m in lideres if ref is not None and m.nombre != ref.nombre), None)
    pares: list[tuple[Any, Any]] = []
    vistos: set[frozenset[str]] = set()

    def _add(a: Any, b: Any) -> None:
        if a is None or b is None or a.nombre == b.nombre:
            return
        k = frozenset((a.nombre, b.nombre))
        if k not in vistos:
            vistos.add(k)
            pares.append((a, b))

    if ref is not None and mercado is not None:
        for f in focos:
            _add(ref, f)
        for f in focos:
            if f.nombre != ref.nombre:
                _add(f, mercado)
    else:
        lider = _lider(marcas)
        for f in focos:
            _add(proyecto, f)
        for f in focos:
            _add(lider, f)
    return pares[:max_pares]


def cities_for(ficha: FichaMarca) -> list[str]:
    ciudades = [c.strip() for c in ficha.ciudades if c.strip()]
    if not ciudades and ficha.ciudad_principal:
        ciudades = [ficha.ciudad_principal.strip()]
    return ciudades[:MAX_CIUDADES]


def instantiate(bank: list[Prompt], marcas: list[Any], ficha: FichaMarca) -> list[PromptInstanciado]:
    """Instancia el banco: `generico` 1; `ciudad` 1 por ciudad de la ficha (máx. 3); `marca` 1 por marca foco;
    `par` 1 por par estratégico (máx. 6)."""
    todas = [m.nombre for m in marcas]
    focos = [m for m in marcas if m.nivel == "foco"]
    pares = strategic_pairs(marcas)
    ciudades = cities_for(ficha)
    out: list[PromptInstanciado] = []

    def _mk(p: Prompt, texto: str, evalua: list[str], ciudad: str | None = None) -> PromptInstanciado:
        return PromptInstanciado(
            prompt_id=p.prompt_id,
            prompt=texto,
            instanciacion=p.instanciacion,
            marcas_a_evaluar=evalua,
            ciudad=ciudad,
            familia=p.familia,
            intencion=p.intencion,
            prioridad=p.prioridad,
            uso=p.uso,
        )

    for p in bank:
        if p.instanciacion == "generico":
            out.append(_mk(p, p.plantilla, list(todas)))
        elif p.instanciacion == "ciudad":
            for c in ciudades:
                out.append(_mk(p, p.plantilla.replace("[CIUDAD]", c), list(todas), c))
        elif p.instanciacion == "marca":
            for m in focos:
                out.append(_mk(p, p.plantilla.replace("[MARCA_A]", m.nombre), [m.nombre]))
        elif p.instanciacion == "par":
            for a, b in pares:
                texto = p.plantilla.replace("[MARCA_A]", a.nombre).replace("[MARCA_B]", b.nombre)
                out.append(_mk(p, texto, [a.nombre, b.nombre]))
    return out


def load_marcas(study_dir: Path) -> list[MarcaPropuesta]:
    return read_marcas_csv(Path(study_dir) / "marcas.csv")
