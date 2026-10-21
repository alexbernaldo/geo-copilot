"""WC1 · Importación y validación de los CSV del estudio (formato del kit)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel

from geo.study.common import (
    KIND_COLUMNS,
    KIND_FILENAMES,
    KINDS,
    MOTORES,
    TIPOS_FUENTE_CLASIFICABLES,
    extract_domain,
    header_key,
    norm_name,
    read_csv_flex,
    split_domains,
    split_pipe,
    write_csv,
)

Kind = Literal["ejecuciones", "marcas", "banco_prompts", "fuentes_catalogo", "muestra_evaluada"]

MAX_ERROR_EXAMPLES = 20

# Columnas obligatorias por tipo (nombres canónicos). El resto son opcionales y se rellenan al normalizar.
REQUIRED: dict[str, list[str]] = {
    "ejecuciones": [
        "Ejecucion_ID",
        "Prompt_ID",
        "Familia",
        "Intención",
        "Prompt ejecutado",
        "Motor",
        "Repetición",
        "Marcas a evaluar",
        "Respuesta completa",
    ],
    "marcas": ["Marca", "Nivel", "Rol", "Dominio_propio"],
    "banco_prompts": [
        "Prompt_ID",
        "Familia",
        "Intención",
        "Prioridad",
        "Uso",
        "Instanciación",
        "Prompt (plantilla)",
    ],
    "fuentes_catalogo": ["Dominio", "Tipo_de_fuente", "Calidad_de_fuente_0_1"],
    "muestra_evaluada": [
        "Ejecucion_ID",
        "Marca",
        "Aparece (1/0)",
        "Posición",
        "Peso posición",
        "Tipo de mención",
        "Fuerza recomendación (-1 a 3)",
        "Sentimiento",
        "Tipo de fuente",
    ],
}

# Orden de comprobación en identify(): lo más específico primero (la muestra contiene casi todas las columnas de ejecuciones).
_IDENTIFY_ORDER: tuple[str, ...] = (
    "muestra_evaluada",
    "ejecuciones",
    "banco_prompts",
    "marcas",
    "fuentes_catalogo",
)

_VALID_NIVEL = {"foco", "contexto"}
_VALID_INTENCION = {"Descubrimiento", "Comparación", "Validación", "Decisión"}
_VALID_INSTANCIACION = {"generico", "ciudad", "marca", "par"}
_VALID_TIPOS_FUENTE = set(TIPOS_FUENTE_CLASIFICABLES) | {"Sin fuente"}


class StudySummary(BaseModel):
    """Resumen del estudio cargado o generado (mismo contrato que StudySummary de la API)."""

    ejecuciones: int
    motores: list[str]
    repeticiones: int
    prompts: int
    marcas: int
    espontaneas: int
    asistidas: int
    ciudades: list[str] = []


@dataclass
class ValidationReport:
    """Informe de validación de un archivo (contrato ValidationFile de la API)."""

    archivo: str
    tipo: str | None
    filas: int = 0
    columnas_reconocidas: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    filas_con_error: list[dict[str, Any]] = field(default_factory=list)

    @property
    def bloqueado(self) -> bool:
        return bool(self.errores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "archivo": self.archivo,
            "tipo": self.tipo,
            "filas": self.filas,
            "columnas_reconocidas": list(self.columnas_reconocidas),
            "errores": list(self.errores),
            "avisos": list(self.avisos),
            "filas_con_error": list(self.filas_con_error),
        }


class StudyValidationError(ValueError):
    """Hay errores bloqueantes en los archivos del estudio."""

    def __init__(self, informes: list[ValidationReport]):
        self.informes = informes
        msgs = [f"{r.archivo}: {e}" for r in informes for e in r.errores]
        super().__init__("; ".join(msgs[:5]) or "Archivos del estudio no válidos.")


@dataclass
class StudyContext:
    """Datos de otros archivos del mismo estudio para las comprobaciones cruzadas."""

    prompt_ids: set[str] | None = None
    marcas: set[str] | None = None  # nombres normalizados
    dominios_catalogo: set[str] | None = None
    ejecucion_ids: set[str] | None = None


# ---------------------------------------------------------------- lectura canónica


def _canonical_map(kind: str) -> dict[str, str]:
    return {header_key(c): c for c in KIND_COLUMNS[kind]}


def _recognized(df: pd.DataFrame, kind: str) -> dict[str, str]:
    """Devuelve {columna_original: columna_canónica} para las cabeceras reconocidas."""
    cmap = _canonical_map(kind)
    out: dict[str, str] = {}
    for col in df.columns:
        canon = cmap.get(header_key(col))
        if canon and canon not in out.values():
            out[col] = canon
    return out


def read_kind(path: Path, kind: str) -> pd.DataFrame:
    """Lee un CSV y devuelve un DataFrame (texto) con las cabeceras canónicas; las opcionales ausentes van vacías."""
    df = read_csv_flex(path)
    rec = _recognized(df, kind)
    df = df.rename(columns=rec)
    for col in KIND_COLUMNS[kind]:
        if col not in df.columns:
            df[col] = ""
    return df[KIND_COLUMNS[kind]].copy()


def identify(path: Path) -> Kind | None:
    """Reconoce el tipo de CSV por sus columnas (no por el nombre del archivo)."""
    try:
        df = read_csv_flex(Path(path))
    except Exception:
        return None
    keys = {header_key(c) for c in df.columns}
    for kind in _IDENTIFY_ORDER:
        if all(header_key(c) in keys for c in REQUIRED[kind]):
            if kind == "ejecuciones" and header_key("Aparece (1/0)") in keys:
                continue
            return kind  # type: ignore[return-value]
    return None


# ---------------------------------------------------------------- validación


def _add_row_error(rep: ValidationReport, fila: int, motivo: str, **extra: Any) -> None:
    if len(rep.filas_con_error) < MAX_ERROR_EXAMPLES:
        rep.filas_con_error.append({"fila": fila, "motivo": motivo, **extra})


def _fila(idx: int) -> int:
    """Número de fila en el archivo (cabecera = 1)."""
    return idx + 2


def _count_msg(items: list[str], limit: int = 5) -> str:
    shown = ", ".join(items[:limit])
    extra = len(items) - limit
    return f"{shown} y {extra} más" if extra > 0 else shown


def validate(kind: str, path: Path, context: StudyContext | None = None) -> ValidationReport:
    """Valida un archivo del estudio. Con `context` añade las comprobaciones cruzadas con otros archivos."""
    path = Path(path)
    rep = ValidationReport(archivo=path.name, tipo=kind if kind in KINDS else None)
    if kind not in KINDS:
        rep.errores.append(f"Tipo de archivo desconocido: {kind}.")
        return rep
    try:
        raw = read_csv_flex(path)
    except Exception as exc:
        rep.errores.append(f"No se pudo leer el archivo: {exc}")
        return rep

    rep.filas = int(len(raw))
    rec = _recognized(raw, kind)
    rep.columnas_reconocidas = list(rec.values())
    for col in REQUIRED[kind]:
        if col not in rec.values():
            rep.errores.append(f"Falta la columna obligatoria «{col}».")
    if rep.errores:
        return rep

    df = raw.rename(columns=rec)
    ctx = context or StudyContext()
    {
        "ejecuciones": _validate_ejecuciones,
        "marcas": _validate_marcas,
        "banco_prompts": _validate_banco,
        "fuentes_catalogo": _validate_fuentes,
        "muestra_evaluada": _validate_muestra,
    }[kind](df, rep, ctx)
    return rep


def _validate_ejecuciones(df: pd.DataFrame, rep: ValidationReport, ctx: StudyContext) -> None:
    ids = df["Ejecucion_ID"].str.strip()
    for i, v in ids.items():
        if not v:
            _add_row_error(rep, _fila(int(i)), "Ejecucion_ID vacío", columna="Ejecucion_ID")
    vacios = int((ids == "").sum())
    if vacios:
        rep.errores.append(f"{vacios} filas con Ejecucion_ID vacío.")
    dup = ids[(ids != "") & ids.duplicated(keep=False)]
    if not dup.empty:
        dup_ids = sorted(set(dup))
        rep.errores.append(f"Ejecucion_ID duplicado: {_count_msg(dup_ids)}.")
        for i, v in dup.items():
            _add_row_error(rep, _fila(int(i)), "Ejecucion_ID duplicado", columna="Ejecucion_ID", valor=v)

    motores_ok = {m.lower(): m for m in MOTORES}
    malos = df.loc[~df["Motor"].str.strip().str.lower().isin(motores_ok)]
    if not malos.empty:
        vals = sorted(set(malos["Motor"]))
        rep.errores.append(f"Motor desconocido: {_count_msg([v or '(vacío)' for v in vals])}. Válidos: {', '.join(MOTORES)}.")
        for i, v in malos["Motor"].items():
            _add_row_error(rep, _fila(int(i)), "Motor desconocido", columna="Motor", valor=v)

    rep_bad = df.loc[~df["Repetición"].str.strip().str.fullmatch(r"\d+")]
    if not rep_bad.empty:
        rep.errores.append(f"Repetición no numérica en {len(rep_bad)} filas.")
        for i, v in rep_bad["Repetición"].items():
            _add_row_error(rep, _fila(int(i)), "Repetición no numérica", columna="Repetición", valor=v)

    if ctx.prompt_ids is not None:
        miss = df.loc[~df["Prompt_ID"].str.strip().isin(ctx.prompt_ids)]
        if not miss.empty:
            rep.errores.append(
                f"Prompt_ID que no está en el banco de prompts: {_count_msg(sorted(set(miss['Prompt_ID'])))}."
            )
            for i, v in miss["Prompt_ID"].items():
                _add_row_error(rep, _fila(int(i)), "Prompt_ID fuera del banco", columna="Prompt_ID", valor=v)

    if ctx.marcas is not None:
        desconocidas: dict[str, int] = {}
        for i, v in df["Marcas a evaluar"].items():
            for nombre in split_pipe(v):
                if norm_name(nombre) not in ctx.marcas:
                    desconocidas[nombre] = desconocidas.get(nombre, 0) + 1
                    _add_row_error(
                        rep, _fila(int(i)), "Marca fuera de marcas.csv", columna="Marcas a evaluar", valor=nombre
                    )
        if desconocidas:
            rep.errores.append(f"Marca en «Marcas a evaluar» que no está en marcas.csv: {_count_msg(sorted(desconocidas))}.")

    # avisos
    vacias = int((df["Fuentes citadas"].str.strip() == "").sum())
    if rep.filas and vacias:
        pct = 100.0 * vacias / rep.filas
        pct_txt = f"{pct:.1f}".replace(".", ",")
        rep.avisos.append(f"Fuentes citadas vacías en el {pct_txt} % de las filas ({vacias} de {rep.filas}).")
    if ctx.dominios_catalogo is not None:
        citados: set[str] = set()
        for v in df["Fuentes citadas"]:
            citados.update(extract_domain(d) for d in split_domains(v))
        fuera = sorted(d for d in citados if d and d not in ctx.dominios_catalogo)
        if fuera:
            rep.avisos.append(
                f"{len(fuera)} dominios citados no están en el catálogo de fuentes (se clasificarán automáticamente): {_count_msg(fuera)}."
            )
    if ctx.prompt_ids is not None:
        usados = set(df["Prompt_ID"].str.strip())
        sin = sorted(ctx.prompt_ids - usados)
        if sin:
            rep.avisos.append(f"Prompts del banco sin ejecuciones: {_count_msg(sin)}.")


def _validate_marcas(df: pd.DataFrame, rep: ValidationReport, ctx: StudyContext) -> None:
    nombres = df["Marca"].str.strip()
    for i, v in nombres.items():
        if not v:
            _add_row_error(rep, _fila(int(i)), "Marca vacía", columna="Marca")
    if (nombres == "").any():
        rep.errores.append("Hay filas con el nombre de la marca vacío.")
    norm = nombres.map(norm_name)
    dup = norm[(norm != "") & norm.duplicated(keep=False)]
    if not dup.empty:
        rep.errores.append(f"Marca duplicada: {_count_msg(sorted(set(nombres[dup.index])))}.")
        for i in dup.index:
            _add_row_error(rep, _fila(int(i)), "Marca duplicada", columna="Marca", valor=nombres[i])
    malos = df.loc[~df["Nivel"].str.strip().str.lower().isin(_VALID_NIVEL)]
    if not malos.empty:
        rep.errores.append(f"Nivel no válido (debe ser foco o contexto) en {len(malos)} filas.")
        for i, v in malos["Nivel"].items():
            _add_row_error(rep, _fila(int(i)), "Nivel no válido", columna="Nivel", valor=v)
    if not (df["Rol"].str.upper().str.contains("MARCA DEL BRIEF")).any():
        rep.avisos.append("Ninguna marca tiene el rol «MARCA DEL BRIEF»; el análisis necesita una marca del proyecto.")
    sin_dom = int((df["Dominio_propio"].str.strip() == "").sum())
    if sin_dom:
        rep.avisos.append(f"{sin_dom} marcas sin dominio propio.")
    if int((df["Nivel"].str.strip().str.lower() == "foco").sum()) > 4:
        rep.avisos.append("Hay más de 4 marcas de nivel foco.")


def _validate_banco(df: pd.DataFrame, rep: ValidationReport, ctx: StudyContext) -> None:
    ids = df["Prompt_ID"].str.strip()
    if (ids == "").any():
        rep.errores.append("Hay filas con Prompt_ID vacío.")
    dup = ids[(ids != "") & ids.duplicated(keep=False)]
    if not dup.empty:
        rep.errores.append(f"Prompt_ID duplicado: {_count_msg(sorted(set(dup)))}.")
        for i, v in dup.items():
            _add_row_error(rep, _fila(int(i)), "Prompt_ID duplicado", columna="Prompt_ID", valor=v)
    malos = df.loc[~df["Instanciación"].str.strip().isin(_VALID_INSTANCIACION)]
    if not malos.empty:
        rep.errores.append(f"Instanciación no válida (generico, ciudad, marca o par) en {len(malos)} filas.")
        for i, v in malos["Instanciación"].items():
            _add_row_error(rep, _fila(int(i)), "Instanciación no válida", columna="Instanciación", valor=v)
    malos = df.loc[~df["Intención"].str.strip().isin(_VALID_INTENCION)]
    if not malos.empty:
        rep.errores.append(f"Intención no válida en {len(malos)} filas.")
        for i, v in malos["Intención"].items():
            _add_row_error(rep, _fila(int(i)), "Intención no válida", columna="Intención", valor=v)
    if (df["Prompt (plantilla)"].str.strip() == "").any():
        rep.errores.append("Hay plantillas de prompt vacías.")
    for i, row in df.iterrows():
        inst = row["Instanciación"].strip()
        tpl = row["Prompt (plantilla)"]
        problema = ""
        if inst in ("generico", "ciudad", "marca") and "[MARCA_B]" in tpl:
            problema = "[MARCA_B] solo se usa en «par»"
        elif inst == "ciudad" and "[CIUDAD]" not in tpl:
            problema = "falta [CIUDAD]"
        elif inst in ("generico", "marca") and "[CIUDAD]" in tpl:
            problema = "[CIUDAD] solo se usa en «ciudad»"
        elif inst == "marca" and "[MARCA_A]" not in tpl:
            problema = "falta [MARCA_A]"
        elif inst == "par" and ("[MARCA_A]" not in tpl or "[MARCA_B]" not in tpl):
            problema = "faltan [MARCA_A] y [MARCA_B]"
        elif inst in ("generico", "ciudad") and "[MARCA_A]" in tpl:
            problema = "una plantilla espontánea no debe nombrar marcas"
        if problema:
            rep.avisos.append(f"Fila {_fila(int(i))} ({row['Prompt_ID']}): {problema}.")


def _validate_fuentes(df: pd.DataFrame, rep: ValidationReport, ctx: StudyContext) -> None:
    dom = df["Dominio"].str.strip()
    if (dom == "").any():
        rep.errores.append("Hay filas con el dominio vacío.")
    dup = dom[(dom != "") & dom.str.lower().duplicated(keep=False)]
    if not dup.empty:
        rep.errores.append(f"Dominio duplicado en el catálogo: {_count_msg(sorted(set(dup)))}.")
        for i, v in dup.items():
            _add_row_error(rep, _fila(int(i)), "Dominio duplicado", columna="Dominio", valor=v)
    malos = df.loc[~df["Tipo_de_fuente"].str.strip().isin(_VALID_TIPOS_FUENTE)]
    if not malos.empty:
        rep.errores.append(f"Tipo de fuente no válido en {len(malos)} filas.")
        for i, v in malos["Tipo_de_fuente"].items():
            _add_row_error(rep, _fila(int(i)), "Tipo de fuente no válido", columna="Tipo_de_fuente", valor=v)
    for i, v in df["Calidad_de_fuente_0_1"].items():
        try:
            q = float(str(v).replace(",", "."))
            ok = 0.0 <= q <= 1.0
        except ValueError:
            ok = False
        if not ok:
            _add_row_error(rep, _fila(int(i)), "Calidad fuera de 0-1", columna="Calidad_de_fuente_0_1", valor=v)
    if any(e["motivo"] == "Calidad fuera de 0-1" for e in rep.filas_con_error):
        rep.errores.append("Calidad de fuente no numérica o fuera del rango 0-1.")


def _validate_muestra(df: pd.DataFrame, rep: ValidationReport, ctx: StudyContext) -> None:
    malos = df.loc[~df["Aparece (1/0)"].str.strip().isin({"0", "1"})]
    if not malos.empty:
        rep.errores.append(f"«Aparece (1/0)» debe ser 0 o 1 ({len(malos)} filas incorrectas).")
        for i, v in malos["Aparece (1/0)"].items():
            _add_row_error(rep, _fila(int(i)), "Aparece no es 0/1", columna="Aparece (1/0)", valor=v)
    fuerza = df["Fuerza recomendación (-1 a 3)"].str.strip()
    malos = df.loc[~fuerza.isin({"-1", "0", "1", "2", "3"})]
    if not malos.empty:
        rep.errores.append(f"Fuerza de recomendación fuera de -1 a 3 en {len(malos)} filas.")
        for i, v in malos["Fuerza recomendación (-1 a 3)"].items():
            _add_row_error(rep, _fila(int(i)), "Fuerza fuera de rango", columna="Fuerza recomendación (-1 a 3)", valor=v)
    if ctx.ejecucion_ids is not None:
        fuera = sorted(set(df["Ejecucion_ID"].str.strip()) - ctx.ejecucion_ids)
        if fuera:
            rep.avisos.append(f"Ejecuciones de la muestra que no están en ejecuciones.csv: {_count_msg(fuera)}.")


# ---------------------------------------------------------------- conjunto de archivos


def build_context(files: dict[str, Path], study_dir: Path | None = None) -> StudyContext:
    """Construye el contexto cruzado con los archivos del conjunto y, si faltan, los ya guardados en study_dir."""
    resolved: dict[str, Path] = {}
    for kind in KINDS:
        if kind in files:
            resolved[kind] = Path(files[kind])
        elif study_dir is not None and (Path(study_dir) / KIND_FILENAMES[kind]).exists():
            resolved[kind] = Path(study_dir) / KIND_FILENAMES[kind]
    ctx = StudyContext()

    def _safe(kind: str) -> pd.DataFrame | None:
        if kind not in resolved:
            return None
        try:
            raw = read_csv_flex(resolved[kind])
            if any(c not in _recognized(raw, kind).values() for c in REQUIRED[kind]):
                return None
            return read_kind(resolved[kind], kind)
        except Exception:
            return None

    banco = _safe("banco_prompts")
    if banco is not None:
        ctx.prompt_ids = set(banco["Prompt_ID"].str.strip())
    marcas = _safe("marcas")
    if marcas is not None:
        ctx.marcas = set()
        for _, r in marcas.iterrows():
            ctx.marcas.add(norm_name(r["Marca"]))
    fuentes = _safe("fuentes_catalogo")
    if fuentes is not None:
        ctx.dominios_catalogo = {extract_domain(d) for d in fuentes["Dominio"] if d.strip()}
    ej = _safe("ejecuciones")
    if ej is not None:
        ctx.ejecucion_ids = set(ej["Ejecucion_ID"].str.strip())
    return ctx


def validate_set(files: dict[str, Path], study_dir: Path | None = None) -> list[ValidationReport]:
    """Valida un conjunto {tipo: ruta} con comprobaciones cruzadas entre archivos."""
    ctx = build_context(files, study_dir)
    return [validate(kind, Path(p), ctx) for kind, p in files.items()]


def identify_all(paths: list[Path]) -> tuple[dict[str, Path], list[ValidationReport]]:
    """Reconoce varios archivos. Devuelve {tipo: ruta} y un informe por cada archivo no reconocido o repetido."""
    found: dict[str, Path] = {}
    problemas: list[ValidationReport] = []
    for p in paths:
        p = Path(p)
        kind = identify(p)
        if kind is None:
            problemas.append(
                ValidationReport(
                    archivo=p.name,
                    tipo=None,
                    errores=["No se reconoce el tipo de archivo por sus columnas."],
                )
            )
        elif kind in found:
            problemas.append(
                ValidationReport(
                    archivo=p.name,
                    tipo=kind,
                    errores=[f"Hay dos archivos de tipo {kind}: {found[kind].name} y {p.name}."],
                )
            )
        else:
            found[kind] = p
    return found, problemas


# ---------------------------------------------------------------- normalización


def _normalize_df(kind: str, df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].astype(str).str.strip()
    if kind == "ejecuciones":
        canon = {m.lower(): m for m in MOTORES}
        out["Motor"] = out["Motor"].map(lambda v: canon.get(v.strip().lower(), v))
        out["Repetición"] = out["Repetición"].map(lambda v: str(int(v)))
        out["Marcas a evaluar"] = out["Marcas a evaluar"].map(lambda v: " | ".join(split_pipe(v)))
        out["Fuentes citadas"] = out["Fuentes citadas"].map(
            lambda v: ", ".join(dict.fromkeys(extract_domain(d) for d in split_domains(v) if extract_domain(d)))
        )
    elif kind == "marcas":
        out["Nivel"] = out["Nivel"].str.lower()
        out["Dominio_propio"] = out["Dominio_propio"].map(lambda v: extract_domain(v) if v else "")
        out["Alias"] = out["Alias"].map(lambda v: " | ".join(split_pipe(v)))
    elif kind == "fuentes_catalogo":
        out["Dominio"] = out["Dominio"].map(extract_domain)
        out["Calidad_de_fuente_0_1"] = out["Calidad_de_fuente_0_1"].map(lambda v: str(float(str(v).replace(",", "."))))
    return out


def normalize_into(study_dir: Path, files: dict[str, Path]) -> StudySummary:
    """Valida los archivos y los copia a `study_dir` con el formato canónico del kit (UTF-8 con BOM, ` | ` y `, `).

    Lanza `StudyValidationError` si hay errores bloqueantes (no escribe nada en ese caso).
    """
    study_dir = Path(study_dir)
    informes = validate_set({k: Path(v) for k, v in files.items()}, study_dir)
    if any(r.bloqueado for r in informes):
        raise StudyValidationError([r for r in informes if r.bloqueado])
    study_dir.mkdir(parents=True, exist_ok=True)
    for kind, path in files.items():
        df = _normalize_df(kind, read_kind(Path(path), kind))
        write_csv(df, study_dir / KIND_FILENAMES[kind])
    return summarize(study_dir)


# ---------------------------------------------------------------- resumen


def detect_cities(banco: pd.DataFrame, ejecuciones: pd.DataFrame) -> list[str]:
    """Ciudades usadas en los prompts `ciudad`: compara el prompt ejecutado con la plantilla con [CIUDAD]."""
    ciudades: dict[str, None] = {}
    plantillas = banco.loc[banco["Instanciación"].str.strip() == "ciudad"]
    for _, row in plantillas.iterrows():
        tpl = row["Prompt (plantilla)"]
        if "[CIUDAD]" not in tpl:
            continue
        partes = [re.escape(p) for p in tpl.split("[CIUDAD]")]
        rx = re.compile("^" + "(.+?)".join(partes) + "$", re.DOTALL)
        sub = ejecuciones.loc[ejecuciones["Prompt_ID"].str.strip() == row["Prompt_ID"].strip(), "Prompt ejecutado"]
        for texto in sub.unique():
            m = rx.match(str(texto).strip())
            if m:
                ciudades[m.group(1).strip()] = None
    return list(ciudades)


def summarize(study_dir: Path) -> StudySummary:
    """Resumen del estudio guardado en `study_dir` (ejecuciones, motores, prompts, marcas, reparto espontáneo/asistido)."""
    study_dir = Path(study_dir)

    def _read(kind: str) -> pd.DataFrame | None:
        p = study_dir / KIND_FILENAMES[kind]
        return read_kind(p, kind) if p.exists() else None

    ej = _read("ejecuciones")
    banco = _read("banco_prompts")
    marcas = _read("marcas")
    n_ej = 0 if ej is None else len(ej)
    motores = [] if ej is None else [m for m in MOTORES if m in set(ej["Motor"])]
    reps = 0
    if ej is not None and n_ej:
        reps = int(pd.to_numeric(ej["Repetición"], errors="coerce").fillna(0).max())
    esp = asi = 0
    ciudades: list[str] = []
    if ej is not None and banco is not None and n_ej:
        inst = dict(zip(banco["Prompt_ID"].str.strip(), banco["Instanciación"].str.strip()))
        tipos = ej["Prompt_ID"].str.strip().map(inst)
        esp = int(tipos.isin({"generico", "ciudad"}).sum())
        asi = int(tipos.isin({"marca", "par"}).sum())
        ciudades = detect_cities(banco, ej)
    if ej is not None and n_ej:
        n_prompts = int(ej["Prompt_ID"].str.strip().nunique())
    else:
        n_prompts = 0 if banco is None else len(banco)
    return StudySummary(
        ejecuciones=n_ej,
        motores=motores,
        repeticiones=reps,
        prompts=n_prompts,
        marcas=0 if marcas is None else len(marcas),
        espontaneas=esp,
        asistidas=asi,
        ciudades=ciudades,
    )
