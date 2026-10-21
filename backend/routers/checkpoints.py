"""Router `checkpoints`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status

from backend.api_models import Invalidation, Progress, Project, Recompute
from backend.deps import get_runner, get_store
from backend.services import invalidation
from backend.services.runner import JobRunner
from backend.services.store import ProjectStore

router = APIRouter()


@router.post(
    "/projects/{id}/checkpoints/{n}/approve",
    response_model=Project,
    summary="Aprueba un punto de control",
)
def post_projects_id_checkpoints_n_approve(
    id: str,
    n: int,
    body: dict[str, Any] | None = None,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    nota = (body or {}).get("nota") if body else None
    return runner.approve(id, n, nota)


@router.get(
    "/projects/{id}/invalidation",
    response_model=Invalidation,
    summary="Qué se recalcula y cuánto cuesta",
)
def get_projects_id_invalidation(
    id: str,
    cambio: str = Query(..., description="Tipo de cambio: ficha, competencia, hallazgos, plan, discrepancia"),
    store: ProjectStore = Depends(get_store),
) -> Any:
    return invalidation.get_invalidation(store, id, cambio)


@router.post(
    "/projects/{id}/recompute",
    response_model=Progress,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Recalcula desde un paso",
)
def post_projects_id_recompute(
    id: str,
    body: Recompute,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    confirmo = bool(body.confirmo_coste)
    return runner.launch(id, "recompute", desde_paso=body.desde_paso, confirmo_coste=confirmo)
