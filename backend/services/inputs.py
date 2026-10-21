"""Entradas de un proyecto: brief, datos del prospecto, CSV del estudio y detección interna del modo de referencia.

El resultado de la detección vive solo en `run/state.json` (`modo_referencia`) y en la primera línea de `trace.jsonl`.
Ningún modelo ni función pública de la API lo devuelve.
"""

from __future__ import annotations

import io
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from geo import reference as ref
from geo.schemas import FichaMarca

from backend.errors import api_error, unprocessable
from backend.services import study_files as sf
from backend.services.store import ProjectStore, atomic_write_json, now_iso, read_json

BRIEF_EXTS = (".md", ".txt", ".docx", ".pdf")
KIT_MARKER = ".kit"


# ---------------------------------------------------------------- brief
def extract_brief_text(filename: str, data: bytes, work: Path) -> str:
    """Texto plano de un brief subido (`.md`, `.txt`, `.docx`, `.pdf`)."""
    ext = Path(filename).suffix.lower()
    if ext not in BRIEF_EXTS:
        raise unprocessable("formato_no_admitido", "Formato no admitido. Sube un archivo .md, .docx, .txt o .pdf, o pega el texto.")
    if not data:
        raise unprocessable("archivo_vacio", "El archivo está vacío.")
    work.mkdir(parents=True, exist_ok=True)
    saved = work / f"brief_original{ext}"
    saved.write_bytes(data)
    try:
        if ext == ".pdf":
            # TODO(I1): pasar a geo.intake.read_brief_text cuando B añada .pdf (ver coord/peticiones/A.md).
            from pypdf import PdfReader

            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        else:
            from geo.intake import read_brief_text

            text = read_brief_text(saved)
    except HTTPException:
        raise
    except Exception as exc:
        raise unprocessable("brief_ilegible", f"No se pudo leer el archivo: {exc}") from exc
    if not text.strip():
        raise unprocessable("brief_vacio", "No se ha podido extraer texto del archivo.")
    return text


def save_brief(store: ProjectStore, pid: str, text: str) -> None:
    (store.inputs_dir(pid)).mkdir(parents=True, exist_ok=True)
    (store.inputs_dir(pid) / "brief.txt").write_text(text, encoding="utf-8")


def read_brief(store: ProjectStore, pid: str) -> str | None:
    p = store.inputs_dir(pid) / "brief.txt"
    return p.read_text(encoding="utf-8") if p.exists() else None


def ficha_preview_from_brief(text: str) -> dict[str, Any]:
    """Vista previa de la ficha con el parser de plantilla (sin coste, sin red)."""
    from geo.intake import load_brief

    try:
        ficha, faltantes = load_brief(text, provider="mock")
    except Exception as exc:
        raise unprocessable("brief_no_interpretable", f"No se pudo extraer la ficha del brief: {exc}") from exc
    return {"ficha": ficha.model_dump(mode="json"), "faltantes": list(faltantes), "origen_campos": {}}


def ingest_brief(store: ProjectStore, pid: str, texto: str) -> dict[str, Any]:
    """Guarda el brief, su vista previa de ficha y la marca/sector del proyecto; devuelve la vista previa."""
    save_brief(store, pid, texto)
    prev = ficha_preview_from_brief(texto)
    atomic_write_json(store.inputs_dir(pid) / "ficha_preview.json", prev)
    store.update(pid, marca=prev["ficha"].get("marca"), sector=prev["ficha"].get("sector"))
    detect_and_store(store, pid)
    refresh_readiness(store, pid)
    return prev


# ---------------------------------------------------------------- prospecto
def read_prospect(store: ProjectStore, pid: str) -> dict[str, Any] | None:
    return read_json(store.inputs_dir(pid) / "prospect.json")


def ficha_from_prospect(p: dict[str, Any]) -> FichaMarca:
    dom = (p.get("dominio") or "").strip()
    ciudad = (p.get("ciudad") or "").strip()
    return FichaMarca(
        marca=p["marca"].strip(), web=f"https://{dom}" if dom else None, sector=p["sector"].strip(),
        ciudades=[ciudad] if ciudad else [], ciudad_principal=ciudad or None,
        competidores_declarados=[c.strip() for c in p.get("competidores", []) if c.strip()],
        objetivo_principal=f"Incrementar la recomendación activa y el posicionamiento espontáneo de {p['marca'].strip()} en asistentes de IA.",
    )


def save_prospect(store: ProjectStore, pid: str, data: dict[str, Any]) -> dict[str, Any]:
    for k in ("marca", "dominio", "sector", "ciudad"):
        if not str(data.get(k, "")).strip():
            raise unprocessable("campo_obligatorio", f"El campo «{k}» es obligatorio.")
    atomic_write_json(store.inputs_dir(pid) / "prospect.json", data)
    ficha = ficha_from_prospect(data)
    atomic_write_json(store.inputs_dir(pid) / "ficha_preview.json", {"ficha": ficha.model_dump(mode="json"), "faltantes": [], "origen_campos": {}})
    return {"ficha": ficha.model_dump(mode="json"), "faltantes": [], "origen_campos": {}}


def current_ficha(store: ProjectStore, pid: str) -> FichaMarca | None:
    """Ficha vigente: la del motor si ya existe; si no, la vista previa del brief o del prospecto."""
    for p in (store.run_dir(pid) / "ficha.json", store.inputs_dir(pid) / "ficha_preview.json"):
        d = read_json(p)
        if d:
            try:
                return FichaMarca.model_validate(d.get("ficha", d))
            except Exception:
                continue
    return None


# ---------------------------------------------------------------- CSV del estudio
def _upload_paths(store: ProjectStore, pid: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    up = store.inputs_dir(pid) / "uploads"
    for f in sorted(up.glob("*.csv"), key=lambda p: p.stat().st_mtime) if up.is_dir() else []:
        kind = sf.identify(f)
        if kind:
            out[kind] = f
    return out


def upload_csvs(store: ProjectStore, pid: str, files: list[tuple[str, bytes]]) -> dict[str, Any]:
    """Guarda los CSV subidos, valida cada uno y normaliza al formato canónico si no hay errores bloqueantes."""
    if not files:
        raise unprocessable("sin_archivos", "No se ha recibido ningún archivo.")
    up = store.inputs_dir(pid) / "uploads"
    up.mkdir(parents=True, exist_ok=True)
    study = store.study_dir(pid)
    reports: list[dict[str, Any]] = []
    good: dict[str, Path] = {}
    try:  # TODO(I1): delegar siempre en geo.study.csv_io (agente C) cuando esté integrado.
        from geo.study import csv_io  # type: ignore
    except Exception:
        csv_io = None  # type: ignore
    for name, data in files:
        safe = Path(name).name or "archivo.csv"
        path = up / safe
        path.write_bytes(data)
        if csv_io is not None:
            kind = csv_io.identify(path)
            rep = sf.report_to_dict(csv_io.validate(kind, path)) if kind else sf.validate_file(path, safe)
            rep["archivo"] = rep.get("archivo") or safe
            rep["tipo"] = kind
        else:
            rep = sf.validate_file(path, safe)
        reports.append(rep)
        if rep["tipo"] and not rep["errores"]:
            good[rep["tipo"]] = path
    # Lo ya cargado antes cuenta para las comprobaciones cruzadas
    staged = Path(study.parent / "_staging")
    shutil.rmtree(staged, ignore_errors=True)
    staged.mkdir(parents=True)
    for k in sf.KINDS:
        if sf.study_file(study, k).exists() and not (study / KIT_MARKER).exists():
            shutil.copy(sf.study_file(study, k), sf.study_file(staged, k))
    if good:
        sf.normalize_into(staged, good)
        sf.cross_check(staged, [r for r in reports if r["tipo"] in good])
    bloqueado = any(r["errores"] for r in reports) or any(r["tipo"] is None for r in reports)
    if not bloqueado:
        if (study / KIT_MARKER).exists():  # datos del kit de una detección anterior: se sustituyen por lo subido
            for k in sf.KINDS:
                sf.study_file(study, k).unlink(missing_ok=True)
            (study / KIT_MARKER).unlink(missing_ok=True)
        sf.normalize_into(study, good)
        store.update(pid, origen_datos="csv")
    shutil.rmtree(staged, ignore_errors=True)
    resumen = None
    have = [k for k in sf.REQUIRED if sf.study_file(study, k).exists()]
    if not bloqueado and have:
        resumen = sf.study_summary(study)
    # la detección se hace con todo lo subido hasta ahora
    detect_and_store(store, pid)
    if (store.study_dir(pid) / KIT_MARKER).exists():
        resumen = sf.study_summary(study)
    return {"informes": reports, "resumen": resumen, "bloqueado": bool(bloqueado)}


# ---------------------------------------------------------------- detección interna
def detect_and_store(store: ProjectStore, pid: str) -> bool:
    """Evalúa el modo de referencia con todas las entradas actuales y lo guarda en `run/state.json`."""
    brief = read_brief(store, pid)
    prospect = read_prospect(store, pid)
    try:
        activo, motivo = ref.detect_reference(
            brief_text=brief,
            csv_paths=_upload_paths(store, pid) or None,
            prospect_brand=(prospect or {}).get("marca"),
            prospect_domain=(prospect or {}).get("dominio"),
        )
    except Exception:
        activo, motivo = False, ""
    store.patch_state(pid, modo_referencia={"activo": bool(activo), "motivo": motivo, "detectado_en": datetime.now().isoformat(timespec="seconds")})
    sync_reference_data(store, pid, bool(activo))
    return bool(activo)


def is_reference(store: ProjectStore, pid: str) -> bool:
    return bool((store.read_state(pid).get("modo_referencia") or {}).get("activo"))


def sync_reference_data(store: ProjectStore, pid: str, activo: bool) -> None:
    """En modo de referencia los datos del estudio son siempre los del kit."""
    study = store.study_dir(pid)
    study.mkdir(parents=True, exist_ok=True)
    marker = study / KIT_MARKER
    if activo:
        for kind in sf.KINDS:
            shutil.copyfile(ref.REFERENCE_DIR / sf.FILE_NAMES[kind], sf.study_file(study, kind))
        marker.write_text("1", encoding="utf-8")
        if store.require(pid).get("origen_datos") is None:
            store.update(pid, origen_datos="csv")
    elif marker.exists():
        for kind in sf.KINDS:
            sf.study_file(study, kind).unlink(missing_ok=True)
        marker.unlink()
        uploads = _upload_paths(store, pid)
        if uploads:
            sf.normalize_into(study, uploads)


def study_ready(store: ProjectStore, pid: str) -> bool:
    study = store.study_dir(pid)
    return all(sf.study_file(study, k).exists() for k in sf.REQUIRED)


def refresh_readiness(store: ProjectStore, pid: str) -> None:
    """Pasa de `borrador` a `listo_para_lanzar` (y al revés) según las entradas disponibles."""
    p = store.require(pid)
    if p["estado"] not in ("borrador", "listo_para_lanzar"):
        return
    entrada = read_prospect(store, pid) is not None if p["tipo"] == "prospecto" else read_brief(store, pid) is not None
    datos = study_ready(store, pid) or (p.get("origen_datos") == "vivo" and (store.study_dir(pid) / "config.json").exists()
                                           and study_ready(store, pid))
    nuevo = "listo_para_lanzar" if entrada and datos else "borrador"
    if nuevo != p["estado"]:
        store.update(pid, estado=nuevo)


def write_reference_check(store: ProjectStore, pid: str, provider: str) -> None:
    """Primera línea de `trace.jsonl`: resultado interno de la detección."""
    trace = store.run_dir(pid) / "trace.jsonl"
    if trace.exists() and trace.stat().st_size > 0:
        return
    info = store.read_state(pid).get("modo_referencia") or {}
    line = {"step": "reference_check", "started_at": now_iso(), "activo": bool(info.get("activo")), "motivo": info.get("motivo", ""), "provider": provider}
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text(json.dumps(line, ensure_ascii=False) + "\n", encoding="utf-8")
