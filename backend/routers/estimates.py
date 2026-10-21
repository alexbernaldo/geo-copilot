"""Router `estimates`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query

from backend.api_models import Estimate
from backend.deps import get_store
from backend.services import estimates
from backend.services.store import ProjectStore

router = APIRouter()


@router.get("/estimates/study", response_model=Estimate, summary="Estimación del estudio en vivo")
def get_estimates_study(
    project_id: str = Query(..., description="ID del proyecto"),
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(project_id)
    return estimates.study_estimate(store, project_id)


@router.get("/estimates/analysis", response_model=Estimate, summary="Estimación del análisis")
def get_estimates_analysis(
    project_id: str = Query(..., description="ID del proyecto"),
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(project_id)
    return estimates.analysis_estimate(store, project_id)
