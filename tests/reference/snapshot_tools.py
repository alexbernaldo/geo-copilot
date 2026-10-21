"""Utilidades de la instantánea de regresión del kit (WB2).

`build_snapshot(run_dir)` extrae de una carpeta de ejecución los artefactos que se
comparan; `write_snapshot` los vuelca a `tests/reference/snapshot/`.
Regenerar solo de forma deliberada: `python -m tests.reference.snapshot_tools`.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshot"
_CLAVES_FECHA = {"fecha", "fecha_hora", "created_at", "timestamp", "generated_at", "generado"}


def _sin_fechas(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sin_fechas(v) for k, v in obj.items() if k.lower() not in _CLAVES_FECHA}
    if isinstance(obj, list):
        return [_sin_fechas(v) for v in obj]
    return obj


def _tablas(run_dir: Path) -> dict[str, pd.DataFrame]:
    d = run_dir / "tablas"
    return {p.stem: pd.read_parquet(p) for p in sorted(d.glob("T*.parquet"))}


def _leer(run_dir: Path, nombre: str) -> Any:
    return json.loads((run_dir / nombre).read_text(encoding="utf-8"))


def build_snapshot(run_dir: Path) -> dict[str, Any]:
    """Devuelve {'json': {nombre: obj}, 'tablas': {nombre: DataFrame}}."""
    rev = _leer(run_dir, "revision.json")
    prop = _leer(run_dir, "propuesta.json")
    return {
        "json": {
            "metrics.json": _leer(run_dir, "metrics.json"),
            "findings.json": _sin_fechas(_leer(run_dir, "findings.json")),
            "plan.json": _sin_fechas(_leer(run_dir, "plan.json")),
            "revision.json": {
                "cifras_verificadas": rev["cifras_verificadas"],
                "cifras_no_trazables": rev["cifras_no_trazables"],
                "n_incidencias": len(rev["incidencias"]),
                "aprobado": rev["aprobado"],
            },
            "secciones.json": prop["secciones"],
        },
        "tablas": _tablas(run_dir),
    }


def write_snapshot(snap: dict[str, Any], dest: Path = SNAPSHOT_DIR) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for nombre, obj in snap["json"].items():
        (dest / nombre).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    tdir = dest / "tablas"
    tdir.mkdir(exist_ok=True)
    for nombre, df in snap["tablas"].items():
        df.to_csv(tdir / f"{nombre}.csv", index=False, encoding="utf-8-sig")


def run_kit(root: Path) -> Path:
    """Ejecuta el pipeline en mock con el kit y devuelve la carpeta de ejecución."""
    os.environ["LLM_PROVIDER"] = "mock"
    from geo.orchestrator import Run
    from geo.reference import REFERENCE_DIR

    run = Run(
        modo="cliente",
        brief_path=REFERENCE_DIR / "Brief_de_ejemplo_Clinica_Alborada.md",
        provider="mock",
        run_dir=root / "regresion",
        study_dir=REFERENCE_DIR,
    )
    run.run_all(auto_approve=True)
    return run.run_dir


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        write_snapshot(build_snapshot(run_kit(Path(tmp))))
    print(f"Instantánea escrita en {SNAPSHOT_DIR}")
