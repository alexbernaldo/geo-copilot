"""Router `estimates` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.get("/estimates/study", summary='Estimación del estudio en vivo')
def get_estimates_study() -> None:
    not_implemented()


@router.get("/estimates/analysis", summary='Estimación del análisis')
def get_estimates_analysis() -> None:
    not_implemented()
