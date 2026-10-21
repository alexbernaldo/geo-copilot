"""backend/services/invalidation.py: Mapa de invalidación (B3) y cálculo de costes para /invalidation."""

from __future__ import annotations

from typing import Any

from backend.errors import unprocessable
from backend.services import estimates
from backend.services.store import ProjectStore

MAPA_INVALIDACION: dict[str, list[str]] = {
    # Ficha: mercado, hallazgos, plan, redacción, revisión, exportación
    "ficha": ["market", "findings", "plan", "review", "write", "export"],
    # Competencia: hallazgos y posteriores (o si marcas añadidas: detect, judge, etc.)
    "competencia": ["market", "findings", "plan", "review", "write", "export"],
    # Hallazgos: plan, redacción, revisión, exportación
    "hallazgos": ["plan", "review", "write", "export"],
    # Plan: revalidación de presupuesto, redacción, revisión, exportación
    "plan": ["review", "write", "export"],
    # Discrepancia del juez resuelta: métricas y todo lo posterior
    "discrepancia": ["metrics", "market", "findings", "plan", "review", "write", "export"],
}


def get_invalidation(store: ProjectStore, pid: str, cambio: str) -> dict[str, Any]:
    store.require(pid)
    pasos = MAPA_INVALIDACION.get(cambio)
    if pasos is None:
        raise unprocessable(
            "cambio_desconocido",
            f"Tipo de cambio no válido: {cambio}. Debe ser uno de: {list(MAPA_INVALIDACION.keys())}.",
        )
    est = estimates.analysis_estimate(store, pid, steps=pasos)
    return {
        "pasos": pasos,
        "estimacion": est,
    }
