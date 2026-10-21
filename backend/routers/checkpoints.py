"""Router `checkpoints` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.post("/projects/{id}/checkpoints/{n}/approve", summary='Aprueba un punto de control')
def post_projects_id_checkpoints_n_approve() -> None:
    not_implemented()


@router.get("/projects/{id}/invalidation", summary='Qué se recalcula y cuánto cuesta')
def get_projects_id_invalidation() -> None:
    not_implemented()


@router.post("/projects/{id}/recompute", summary='Recalcula desde un paso')
def post_projects_id_recompute() -> None:
    not_implemented()
