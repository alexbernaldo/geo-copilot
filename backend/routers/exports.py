"""Router `exports` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.get("/projects/{id}/exports/{fmt}", summary='Descarga docx o md')
def get_projects_id_exports_fmt() -> None:
    not_implemented()
