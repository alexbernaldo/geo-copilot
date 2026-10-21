"""Archivos del estudio (`study/*.csv`): reconocimiento, validación, resumen y edición de marcas y banco.

TODO(I1): `geo.study.csv_io` (agente C) es el dueño de `identify/validate/normalize_into`. Mientras no exista se usa
la implementación local de este módulo; cuando exista, `identify_and_validate` delega en él.
"""

from __future__ import annotations

import dataclasses
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from backend.services.pipeline import MAX_FOCO, MAX_MARCAS, MOTORES
from backend.services.store import atomic_write_json, read_json

KINDS: tuple[str, ...] = ("ejecuciones", "marcas", "banco_prompts", "fuentes_catalogo", "muestra_evaluada")
REQUIRED = ("ejecuciones", "marcas", "banco_prompts")

_COLUMNS: dict[str, tuple[str, ...]] = {
    "ejecuciones": ("Ejecucion_ID", "Sector", "Prompt_ID", "Familia", "Intención", "Prompt ejecutado", "Motor", "Repetición",
                    "Marcas a evaluar", "Respuesta completa", "Fuentes citadas", "Fecha/hora"),
    "marcas": ("Marca", "Nivel", "Rol", "Dominio_propio", "Alias"),
    "banco_prompts": ("Prompt_ID", "Sector", "Familia", "Intención", "Prioridad", "Uso", "Instanciación",
                      "Prompt (plantilla)", "Notas de instanciación"),
    "fuentes_catalogo": ("Dominio", "Tipo_de_fuente", "Calidad_de_fuente_0_1"),
    "muestra_evaluada": ("Sector", "Marca", "Prompt_ID", "Intención", "Prompt ejecutado", "Motor", "Repetición",
                         "Aparece (1/0)", "Posición", "Peso posición", "Tipo de mención", "Fuente citada",
                         "Respuesta completa", "Fecha/hora", "Notas", "Fuerza recomendación (-1 a 3)", "Sentimiento",
                         "Tipo de fuente", "Fuera de territorio", "Ejecucion_ID"),
}
_REQUIRED_COLS: dict[str, tuple[str, ...]] = {
    "ejecuciones": ("Ejecucion_ID", "Prompt_ID", "Motor", "Marcas a evaluar", "Respuesta completa"),
    "marcas": ("Marca", "Nivel", "Dominio_propio"),
    "banco_prompts": ("Prompt_ID", "Familia", "Instanciación", "Prompt (plantilla)"),
    "fuentes_catalogo": ("Dominio", "Tipo_de_fuente"),
    "muestra_evaluada": ("Marca", "Ejecucion_ID", "Aparece (1/0)"),
}
FILE_NAMES = {k: f"{k}.csv" for k in KINDS}
ESPONTANEAS = ("generico", "ciudad")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).replace("﻿", "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def study_file(study_dir: Path, kind: str) -> Path:
    return Path(study_dir) / FILE_NAMES[kind]


# ---------------------------------------------------------------- reconocimiento y validación
def identify(path: Path) -> str | None:
    """Tipo de archivo por sus columnas (tolerante a BOM, mayúsculas y tildes)."""
    try:
        cols = {norm(c) for c in pd.read_csv(path, encoding="utf-8-sig", nrows=0).columns}
    except Exception:
        return None
    for kind in ("muestra_evaluada", "ejecuciones", "banco_prompts", "marcas", "fuentes_catalogo"):
        if {norm(c) for c in _REQUIRED_COLS[kind]} <= cols:
            return kind
    return None


def _canonical(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Renombra las cabeceras al nombre exacto del kit."""
    by_norm = {norm(c): c for c in _COLUMNS[kind]}
    return df.rename(columns={c: by_norm[norm(c)] for c in df.columns if norm(c) in by_norm})


def validate_file(path: Path, display_name: str | None = None) -> dict[str, Any]:
    """`ValidationFile` del contrato para un CSV suelto (sin comprobaciones cruzadas)."""
    name = display_name or path.name
    kind = identify(path)
    rep: dict[str, Any] = {"archivo": name, "tipo": kind, "filas": 0, "columnas_reconocidas": [], "errores": [],
                           "avisos": [], "filas_con_error": []}
    try:
        df = read_csv(path)
    except Exception as exc:  # archivo ilegible
        rep["errores"].append(f"No se puede leer el archivo como CSV: {exc}")
        return rep
    rep["filas"] = int(len(df))
    if kind is None:
        rep["errores"].append("No se reconoce el tipo de archivo: faltan columnas obligatorias de ningún archivo del estudio.")
        return rep
    df = _canonical(df, kind)
    rep["columnas_reconocidas"] = [c for c in _COLUMNS[kind] if c in df.columns]
    for c in _REQUIRED_COLS[kind]:
        if c not in df.columns:
            rep["errores"].append(f"Falta la columna obligatoria «{c}».")
    if rep["errores"]:
        return rep
    bad: list[dict[str, Any]] = []
    if kind == "ejecuciones":
        dup = df[df.duplicated("Ejecucion_ID", keep=False)]
        if len(dup):
            rep["errores"].append(f"Hay {dup['Ejecucion_ID'].nunique()} Ejecucion_ID duplicados.")
            bad += [{"fila": int(i) + 2, "motivo": "Ejecucion_ID duplicado", "valor": r["Ejecucion_ID"]} for i, r in dup.head(10).iterrows()]
        motores = df[~df["Motor"].isin(MOTORES)]
        if len(motores):
            rep["errores"].append(f"{len(motores)} filas con motor desconocido (válidos: {', '.join(MOTORES)}).")
            bad += [{"fila": int(i) + 2, "motivo": "Motor desconocido", "valor": r["Motor"]} for i, r in motores.head(10).iterrows()]
        if "Fuentes citadas" in df.columns and len(df):
            vacias = float((df["Fuentes citadas"].str.strip() == "").mean())
            if vacias > 0.2:
                rep["avisos"].append(f"El {vacias * 100:.0f} % de las ejecuciones no tiene fuentes citadas.".replace(".", ","))
    elif kind == "marcas":
        dup = df[df.duplicated("Marca", keep=False)]
        if len(dup):
            rep["errores"].append("Hay marcas repetidas en marcas.csv.")
        if (df["Nivel"].str.lower().isin(["foco", "contexto"]) == False).any():  # noqa: E712
            rep["errores"].append("La columna «Nivel» solo admite «foco» o «contexto».")
    elif kind == "banco_prompts":
        dup = df[df.duplicated("Prompt_ID", keep=False)]
        if len(dup):
            rep["errores"].append("Hay Prompt_ID duplicados en el banco.")
    rep["filas_con_error"] = bad
    return rep


def cross_check(study_dir: Path, reports: list[dict[str, Any]]) -> None:
    """Comprobaciones entre archivos (prompt/marca inexistentes, dominios fuera del catálogo)."""
    d = Path(study_dir)
    ej, ma, ba, fu = (study_file(d, k) for k in ("ejecuciones", "marcas", "banco_prompts", "fuentes_catalogo"))
    by_kind = {r["tipo"]: r for r in reports if r.get("tipo")}
    if "ejecuciones" in by_kind and not by_kind["ejecuciones"]["errores"]:
        rep = by_kind["ejecuciones"]
        df = _canonical(read_csv(ej), "ejecuciones")
        if ba.exists():
            bank = set(_canonical(read_csv(ba), "banco_prompts")["Prompt_ID"])
            missing = df[~df["Prompt_ID"].isin(bank)]
            if len(missing):
                rep["errores"].append(f"{len(missing)} ejecuciones usan un Prompt_ID que no está en el banco de prompts.")
                rep["filas_con_error"] += [{"fila": int(i) + 2, "motivo": "Prompt_ID fuera del banco", "valor": r["Prompt_ID"]}
                                           for i, r in missing.head(10).iterrows()]
        if ma.exists():
            names = set(_canonical(read_csv(ma), "marcas")["Marca"])
            unknown: set[str] = set()
            for cell in df["Marcas a evaluar"]:
                unknown |= {m.strip() for m in cell.split("|") if m.strip() and m.strip() not in names}
            if unknown:
                rep["errores"].append("Marcas a evaluar que no están en marcas.csv: " + ", ".join(sorted(unknown)[:5]) + ".")
        if fu.exists():
            cat = set(_canonical(read_csv(fu), "fuentes_catalogo")["Dominio"].str.lower())
            doms: set[str] = set()
            for cell in df.get("Fuentes citadas", pd.Series(dtype=str)):
                doms |= {m.strip().lower() for m in cell.split("|") if m.strip()}
            fuera = doms - cat
            if fuera:
                rep["avisos"].append(f"{len(fuera)} dominios citados no están en el catálogo de fuentes (se clasificarán automáticamente).")


def normalize_into(study_dir: Path, files: dict[str, Path]) -> None:
    """Copia cada CSV al formato canónico del kit (UTF-8 con BOM, cabeceras exactas) dentro de `study_dir`."""
    for kind, src in files.items():
        df = _canonical(read_csv(src), kind)
        cols = [c for c in _COLUMNS[kind] if c in df.columns] + [c for c in df.columns if c not in _COLUMNS[kind]]
        write_csv(df[cols], study_file(study_dir, kind))


def study_summary(study_dir: Path) -> dict[str, Any]:
    """`StudySummary` del contrato a partir de los CSV ya normalizados."""
    d = Path(study_dir)
    ej, ba, ma = (study_file(d, k) for k in ("ejecuciones", "banco_prompts", "marcas"))
    out: dict[str, Any] = {"ejecuciones": 0, "motores": [], "repeticiones": 0, "prompts": 0, "marcas": 0,
                           "espontaneas": 0, "asistidas": 0, "ciudades": []}
    if ma.exists():
        out["marcas"] = int(len(read_csv(ma)))
    inst: dict[str, str] = {}
    if ba.exists():
        bank = read_csv(ba)
        inst = dict(zip(bank["Prompt_ID"], bank["Instanciación"]))
        out["prompts"] = int(len(bank))
    if ej.exists():
        df = read_csv(ej)
        out["ejecuciones"] = int(len(df))
        out["motores"] = sorted(df["Motor"].unique())
        reps = pd.to_numeric(df["Repetición"], errors="coerce").dropna()
        out["repeticiones"] = int(reps.max()) if len(reps) else 0
        out["prompts"] = int(df["Prompt_ID"].nunique()) or out["prompts"]
        esp = df["Prompt_ID"].map(inst).isin(ESPONTANEAS)
        out["espontaneas"], out["asistidas"] = int(esp.sum()), int((~esp).sum())
    return out


# ---------------------------------------------------------------- marcas, banco, configuración
def read_brands(study_dir: Path) -> list[dict[str, Any]]:
    p = study_file(study_dir, "marcas")
    if not p.exists():
        return []
    df = _canonical(read_csv(p), "marcas")
    ficha_meta = read_json(Path(study_dir) / "propuesta_marcas.json", {}) or {}
    extra = {m.get("nombre"): m for m in ficha_meta.get("marcas", [])} if isinstance(ficha_meta, dict) else {}
    out = []
    for _, r in df.iterrows():
        e = extra.get(r["Marca"], {})
        out.append({"nombre": r["Marca"], "nivel": r["Nivel"].lower(), "rol": r.get("Rol", ""), "dominio": r["Dominio_propio"],
                    "alias": [a.strip() for a in r.get("Alias", "").split("|") if a.strip()],
                    "motivo": e.get("motivo"), "fuente_url": e.get("fuente_url")})
    return out


def write_brands(study_dir: Path, marcas: list[dict[str, Any]]) -> None:
    df = pd.DataFrame([{"Marca": m["nombre"], "Nivel": m["nivel"], "Rol": m.get("rol", ""), "Dominio_propio": m.get("dominio", ""),
                        "Alias": " | ".join(m.get("alias", []))} for m in marcas], columns=list(_COLUMNS["marcas"]))
    write_csv(df, study_file(study_dir, "marcas"))
    atomic_write_json(Path(study_dir) / "propuesta_marcas.json", {"marcas": marcas})


def validate_brands(marcas: list[dict[str, Any]], marca_proyecto: str | None, declarados: list[str]) -> list[str]:
    """Reglas de B2.1 aplicadas a la tabla editada. Devuelve la lista de problemas (vacía si es válida)."""
    probs: list[str] = []
    if not marcas:
        probs.append("Añade al menos una marca.")
    if sum(1 for m in marcas if m["nivel"] == "foco") > MAX_FOCO:
        probs.append(f"Como máximo {MAX_FOCO} marcas de foco.")
    if len(marcas) > MAX_MARCAS:
        probs.append(f"Como máximo {MAX_MARCAS} marcas en total.")
    names = [norm(m["nombre"]) for m in marcas]
    if len(set(names)) != len(names):
        probs.append("Hay marcas con el mismo nombre.")
    doms = [norm(m["dominio"]) for m in marcas if m.get("dominio")]
    if len(set(doms)) != len(doms):
        probs.append("Hay marcas con el mismo dominio.")
    if marca_proyecto and norm(marca_proyecto) not in names:
        probs.append(f"Falta la marca del proyecto ({marca_proyecto}).")
    elif marca_proyecto:
        m = next(m for m in marcas if norm(m["nombre"]) == norm(marca_proyecto))
        if m["nivel"] != "foco":
            probs.append("La marca del proyecto debe ser de nivel foco.")
    for c in declarados:
        if norm(c) not in names:
            probs.append(f"Falta el competidor declarado en el brief: {c}.")
    return probs


def read_prompts(study_dir: Path) -> list[dict[str, Any]]:
    p = study_file(study_dir, "banco_prompts")
    if not p.exists():
        return []
    df = _canonical(read_csv(p), "banco_prompts")
    return [{"prompt_id": r["Prompt_ID"], "familia": r["Familia"], "intencion": r["Intención"], "prioridad": r.get("Prioridad", "P1"),
             "uso": r.get("Uso", ""), "instanciacion": r["Instanciación"], "plantilla": r["Prompt (plantilla)"]}
            for _, r in df.iterrows()]


def write_prompts(study_dir: Path, plantillas: list[dict[str, Any]], sector: str = "") -> None:
    df = pd.DataFrame([{"Prompt_ID": t["prompt_id"], "Sector": sector, "Familia": t["familia"], "Intención": t["intencion"],
                        "Prioridad": t["prioridad"], "Uso": t.get("uso", ""), "Instanciación": t["instanciacion"],
                        "Prompt (plantilla)": t["plantilla"], "Notas de instanciación": ""} for t in plantillas],
                      columns=list(_COLUMNS["banco_prompts"]))
    write_csv(df, study_file(study_dir, "banco_prompts"))
    atomic_write_json(Path(study_dir) / "propuesta_banco.json", {"prompts": plantillas})


_PLACEHOLDERS = {"generico": set(), "ciudad": {"[CIUDAD]"}, "marca": {"[MARCA_A]"}, "par": {"[MARCA_A]", "[MARCA_B]"}}


def validate_prompts(plantillas: list[dict[str, Any]], marcas: list[str]) -> list[str]:
    """Reglas de B2.2: marcadores válidos por instanciación y ningún prompt espontáneo nombra marcas."""
    probs: list[str] = []
    ids = [t["prompt_id"] for t in plantillas]
    if len(set(ids)) != len(ids):
        probs.append("Hay Prompt_ID repetidos.")
    for t in plantillas:
        found = set(re.findall(r"\[[A-Z_]+\]", t["plantilla"]))
        allowed = _PLACEHOLDERS[t["instanciacion"]]
        if found - allowed:
            probs.append(f"{t['prompt_id']}: marcadores no válidos para «{t['instanciacion']}»: {', '.join(sorted(found - allowed))}.")
        if allowed - found:
            probs.append(f"{t['prompt_id']}: falta el marcador {', '.join(sorted(allowed - found))}.")
        if t["instanciacion"] in ESPONTANEAS:
            low = norm(t["plantilla"])
            for m in marcas:
                if norm(m) and norm(m) in low:
                    probs.append(f"{t['prompt_id']}: un prompt espontáneo no puede nombrar la marca «{m}».")
    return probs


def instantiate(plantillas: list[dict[str, Any]], marcas: list[dict[str, Any]], ciudades: list[str],
                marca_proyecto: str | None) -> list[dict[str, Any]]:
    """Instanciación por código (B2.2). TODO(I1): sustituir por `geo.study.prompt_bank.instantiate` cuando exista."""
    foco = [m["nombre"] for m in marcas if m["nivel"] == "foco"]
    todas = [m["nombre"] for m in marcas]
    lider = next((m["nombre"] for m in marcas if "líder" in (m.get("rol") or "").lower() or "lider" in norm(m.get("rol") or "")), None)
    out: list[dict[str, Any]] = []
    for t in plantillas:
        kind = t["instanciacion"]
        if kind == "generico":
            out.append({"prompt_id": t["prompt_id"], "prompt": t["plantilla"], "instanciacion": kind, "marcas_a_evaluar": todas, "ciudad": None})
        elif kind == "ciudad":
            for c in ciudades[:3]:
                out.append({"prompt_id": t["prompt_id"], "prompt": t["plantilla"].replace("[CIUDAD]", c), "instanciacion": kind,
                            "marcas_a_evaluar": todas, "ciudad": c})
        elif kind == "marca":
            for m in foco:
                out.append({"prompt_id": t["prompt_id"], "prompt": t["plantilla"].replace("[MARCA_A]", m), "instanciacion": kind,
                            "marcas_a_evaluar": [m], "ciudad": None})
        elif kind == "par":
            pares: list[tuple[str, str]] = []
            if marca_proyecto:
                pares += [(marca_proyecto, f) for f in foco if f != marca_proyecto]
            if lider:
                pares += [(lider, f) for f in foco if f != lider and (lider, f) not in pares]
            for a, b in pares[:6]:
                out.append({"prompt_id": t["prompt_id"], "prompt": t["plantilla"].replace("[MARCA_A]", a).replace("[MARCA_B]", b),
                            "instanciacion": kind, "marcas_a_evaluar": [a, b], "ciudad": None})
    return out


DEFAULT_CONFIG = {"tamano": "estandar", "motores": list(MOTORES), "repeticiones": 2}


def read_config(study_dir: Path) -> dict[str, Any]:
    cfg = read_json(Path(study_dir) / "config.json", None)
    return cfg if isinstance(cfg, dict) else dict(DEFAULT_CONFIG, motores=list(MOTORES))


def write_config(study_dir: Path, cfg: dict[str, Any]) -> None:
    atomic_write_json(Path(study_dir) / "config.json", cfg)


def report_to_dict(rep: Any) -> dict[str, Any]:
    """Convierte el `ValidationReport` de `geo.study.csv_io` (modelo, dataclass o dict) al `ValidationFile` del contrato."""
    if hasattr(rep, "model_dump"):
        d = rep.model_dump()
    elif dataclasses.is_dataclass(rep):
        d = dataclasses.asdict(rep)
    else:
        d = dict(rep)
    return {"archivo": d.get("archivo", ""), "tipo": d.get("tipo"), "filas": int(d.get("filas", 0)),
            "columnas_reconocidas": list(d.get("columnas_reconocidas", [])), "errores": list(d.get("errores", [])),
            "avisos": list(d.get("avisos", [])), "filas_con_error": list(d.get("filas_con_error", []))}
