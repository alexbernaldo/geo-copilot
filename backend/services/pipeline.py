"""Constantes del pipeline que la API expone (orden de ejecución, nombres, puntos de control)."""

from __future__ import annotations

# Orden real de ejecución de `Run.run_all` (PIPELINE_STEPS del orquestador no coincide con él).
ANALYSIS_STEPS: tuple[str, ...] = (
    "intake", "detect", "judge", "metrics", "market", "findings", "plan", "write", "review", "export",
)
LIVE_STEPS: tuple[str, ...] = ("queries", "sources")

STEP_NAMES: dict[str, str] = {
    "queries": "Ejecutar consultas",
    "sources": "Clasificar fuentes",
    "intake": "Ficha",
    "detect": "Detección",
    "judge": "Juez",
    "metrics": "Métricas",
    "market": "Mercado",
    "findings": "Hallazgos",
    "plan": "Plan",
    "write": "Redacción",
    "review": "Revisión",
    "export": "Exportación",
}

# Punto de control n -> (nombre en state.json, paso tras el que se para, clave pública)
CHECKPOINTS: dict[int, tuple[str, str, str]] = {
    0: ("checkpoint_0_brief", "intake", "ficha"),
    1: ("checkpoint_1_competidores", "market", "competencia"),
    2: ("checkpoint_2_hallazgos", "findings", "hallazgos"),
    3: ("checkpoint_3_plan", "plan", "plan"),
}
CHECKPOINT_TITLES: dict[int, str] = {0: "Ficha", 1: "Competencia", 2: "Hallazgos", 3: "Plan"}
STEP_TO_CHECKPOINT: dict[str, int] = {step: n for n, (_, step, _) in CHECKPOINTS.items()}

# Mapa B3: qué se recalcula al editar cada cosa (primer paso a invalidar).
INVALIDATION_FROM: dict[str, str] = {
    "ficha": "market",
    "market": "findings",
    "findings": "plan",
    "plan": "write",
}

MOTORES: tuple[str, ...] = ("ChatGPT", "Gemini", "Perplexity", "Claude")
MAX_FOCO = 4
MAX_MARCAS = 12


def steps_from(step: str) -> list[str]:
    """Paso `step` y todos los posteriores en orden de ejecución."""
    return list(ANALYSIS_STEPS[ANALYSIS_STEPS.index(step):])
