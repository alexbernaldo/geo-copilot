"""Router `inputs` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.post("/projects/{id}/brief", summary='Sube el brief (multipart) o pega texto; devuelve vista previa de la ficha')
def post_projects_id_brief() -> None:
    not_implemented()


@router.post("/projects/{id}/prospect", summary='Datos de la marca prospecto')
def post_projects_id_prospect() -> None:
    not_implemented()
