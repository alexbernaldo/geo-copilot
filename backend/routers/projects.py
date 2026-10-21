"""Router `projects`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Response, status

from backend.api_models import FichaResponse, Project, ProjectCreate, ProjectPatch
from backend.deps import get_store
from backend.errors import unprocessable
from backend.services import results
from backend.services.store import ProjectStore
from geo.schemas import FichaMarca

router = APIRouter()


@router.get("/projects", response_model=list[Project], summary="Lista de proyectos")
def get_projects(
    estado: str | None = None,
    q: str | None = None,
    archivados: bool = False,
    store: ProjectStore = Depends(get_store),
) -> Any:
    projects = store.list(estado=estado, q=q, archivados=archivados)
    return [store.view(p["id"]) for p in projects]


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED, summary="Crea un borrador")
def post_projects(
    body: ProjectCreate,
    store: ProjectStore = Depends(get_store),
) -> Any:
    p = store.create(body.nombre, body.tipo)
    return store.view(p["id"])


@router.get("/projects/{id}", response_model=Project, summary="Detalle del proyecto")
def get_projects_id(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return store.view(id)


@router.patch("/projects/{id}", response_model=Project, summary="Renombrar, revisión o archivar")
def patch_projects_id(
    id: str,
    body: ProjectPatch,
    store: ProjectStore = Depends(get_store),
) -> Any:
    updates = body.model_dump(exclude_unset=True)
    if updates:
        store.update(id, **updates)
    return store.view(id)


@router.delete("/projects/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Borrar (requiere ?confirm=<nombre>)")
def delete_projects_id(
    id: str,
    confirm: str = Query(...),
    store: ProjectStore = Depends(get_store),
) -> Response:
    p = store.require(id)
    if confirm != p.get("nombre"):
        raise unprocessable(
            "confirmacion_incorrecta",
            f"El parámetro confirm debe coincidir exactamente con el nombre del proyecto ('{p.get('nombre')}').",
        )
    store.delete(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/projects/{id}/duplicate", response_model=Project, status_code=status.HTTP_201_CREATED, summary="Duplica entradas y configuración")
def post_projects_id_duplicate(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    dup = store.duplicate(id)
    return store.view(dup["id"])


@router.get("/projects/{id}/ficha", response_model=FichaResponse, summary="Ficha de marca")
def get_projects_id_ficha(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_ficha(store, id)


@router.put("/projects/{id}/ficha", response_model=FichaResponse, summary="Guarda la ficha")
def put_projects_id_ficha(
    id: str,
    body: FichaMarca,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.put_ficha(store, id, body)
