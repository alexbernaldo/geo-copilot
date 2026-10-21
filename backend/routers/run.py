"""Router `run` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.post("/projects/{id}/run", summary='Lanza el análisis (423 si hay otro trabajo)')
def post_projects_id_run() -> None:
    not_implemented()


@router.post("/projects/{id}/run/resume", summary='Reanuda tras interrupción o aprobación')
def post_projects_id_run_resume() -> None:
    not_implemented()


@router.post("/projects/{id}/run/retry-step", summary='Reintenta un paso degradado')
def post_projects_id_run_retry_step() -> None:
    not_implemented()


@router.post("/projects/{id}/run/cancel", summary='Cancela (termina tras la llamada en curso)')
def post_projects_id_run_cancel() -> None:
    not_implemented()


@router.get("/projects/{id}/progress", summary='Progreso')
def get_projects_id_progress() -> None:
    not_implemented()


@router.get("/projects/{id}/events", summary='SSE de progreso (ver contracts/events.md)')
def get_projects_id_events() -> None:
    not_implemented()
