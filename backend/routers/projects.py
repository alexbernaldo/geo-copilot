"""Router `projects` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.get("/projects", summary='Lista de proyectos')
def get_projects() -> None:
    not_implemented()


@router.post("/projects", summary='Crea un borrador')
def post_projects() -> None:
    not_implemented()


@router.get("/projects/{id}", summary='Detalle del proyecto')
def get_projects_id() -> None:
    not_implemented()


@router.patch("/projects/{id}", summary='Renombrar, revisión o archivar')
def patch_projects_id() -> None:
    not_implemented()


@router.delete("/projects/{id}", summary='Borrar (requiere ?confirm=<nombre>)')
def delete_projects_id() -> None:
    not_implemented()


@router.post("/projects/{id}/duplicate", summary='Duplica entradas y configuración')
def post_projects_id_duplicate() -> None:
    not_implemented()


@router.get("/projects/{id}/ficha", summary='Ficha de marca')
def get_projects_id_ficha() -> None:
    not_implemented()


@router.put("/projects/{id}/ficha", summary='Guarda la ficha')
def put_projects_id_ficha() -> None:
    not_implemented()
