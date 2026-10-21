"""Proyecto de ejemplo de Clínica Alborada Visión (el caso del kit), siempre disponible en la lista de proyectos.

Al arrancar el backend se comprueba si existe; si no (primer arranque o se borró), se crea con el brief y los
5 CSV del kit por el mismo camino que usa la web y se lanza en modo continuo. Como es el caso del kit, el
análisis no hace llamadas de red, cuesta 0 € y termina en unos segundos. Se desactiva con GEO_EJEMPLO=0.
"""

from __future__ import annotations

import logging
from typing import Any

from geo import settings as gs
from geo.reference import REFERENCE_DIR

from backend.services import inputs
from backend.services.runner import JobRunner
from backend.services.store import ProjectStore, atomic_write_json, read_json

log = logging.getLogger(__name__)

NOMBRE_EJEMPLO = "Ejemplo · Clínica Alborada Visión"
BRIEF_EJEMPLO = "Brief_de_ejemplo_Clinica_Alborada.md"
CSV_EJEMPLO = ("ejecuciones.csv", "marcas.csv", "banco_prompts.csv", "fuentes_catalogo.csv", "muestra_evaluada.csv")


def _marker(store: ProjectStore) -> Any:
    # Fuera de la carpeta de proyectos para que la lista no la confunda con un proyecto
    return store.root.parent / "ejemplo.json"


def example_id(store: ProjectStore) -> str | None:
    """Id del proyecto de ejemplo si sigue existiendo."""
    pid = (read_json(_marker(store), {}) or {}).get("id")
    return pid if pid and store.exists(pid) else None


def create_example(store: ProjectStore) -> str:
    """Crea el proyecto con el brief y los CSV del kit, listo para lanzar en modo continuo."""
    pid = store.create(NOMBRE_EJEMPLO, "cliente")["id"]
    inputs.ingest_brief(store, pid, (REFERENCE_DIR / BRIEF_EJEMPLO).read_text(encoding="utf-8"))
    inputs.upload_csvs(store, pid, [(n, (REFERENCE_DIR / n).read_bytes()) for n in CSV_EJEMPLO])
    inputs.refresh_readiness(store, pid)
    store.update(pid, revision="continuo")
    atomic_write_json(_marker(store), {"id": pid})
    return pid


def ensure_example(store: ProjectStore, runner: JobRunner) -> str | None:
    """Garantiza que el ejemplo existe y está analizado; si un arranque anterior lo dejó a medias, lo retoma."""
    if gs.get("GEO_EJEMPLO").strip().lower() in ("0", "false", "no"):
        return None
    pid = example_id(store) or create_example(store)
    estado = store.require(pid)["estado"]
    if estado == "listo_para_lanzar":
        runner.launch(pid, "run", confirmo_coste=True)
    elif estado in ("interrumpido", "error"):
        runner.launch(pid, "resume", confirmo_coste=True)
    return pid
