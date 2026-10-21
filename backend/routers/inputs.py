"""Router `inputs`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Request

from backend.api_models import FichaPreview, ProspectData
from backend.deps import get_store
from backend.errors import unprocessable
from backend.services import inputs
from backend.services.store import ProjectStore

router = APIRouter()


@router.post(
    "/projects/{id}/brief",
    response_model=FichaPreview,
    summary="Sube el brief (multipart) o pega texto; devuelve vista previa de la ficha",
)
async def post_projects_id_brief(
    id: str,
    request: Request,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        texto = body.get("texto", "")
        if not texto or not texto.strip():
            raise unprocessable("brief_vacio", "El texto del brief no puede estar vacío.")
        inputs.save_brief(store, id, texto)
        prev = inputs.ficha_preview_from_brief(texto)
        inputs.atomic_write_json(store.inputs_dir(id) / "ficha_preview.json", prev)
        store.update(id, marca=prev["ficha"].get("marca"), sector=prev["ficha"].get("sector"))
        inputs.detect_and_store(store, id)
        inputs.refresh_readiness(store, id)
        return prev
    else:
        form = await request.form()
        archivo = form.get("archivo")
        if not archivo or not hasattr(archivo, "read"):
            raise unprocessable("archivo_faltante", "No se ha proporcionado ningún archivo en el formulario.")
        data = await archivo.read()
        filename = getattr(archivo, "filename", "brief.txt") or "brief.txt"
        texto = inputs.extract_brief_text(filename, data, store.inputs_dir(id))
        inputs.save_brief(store, id, texto)
        prev = inputs.ficha_preview_from_brief(texto)
        inputs.atomic_write_json(store.inputs_dir(id) / "ficha_preview.json", prev)
        store.update(id, marca=prev["ficha"].get("marca"), sector=prev["ficha"].get("sector"))
        inputs.detect_and_store(store, id)
        inputs.refresh_readiness(store, id)
        return prev


@router.post("/projects/{id}/prospect", response_model=FichaPreview, summary="Datos de la marca prospecto")
def post_projects_id_prospect(
    id: str,
    body: ProspectData,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    data = body.model_dump()
    res = inputs.save_prospect(store, id, data)
    store.update(id, marca=data.get("marca"), sector=data.get("sector"))
    inputs.detect_and_store(store, id)
    inputs.refresh_readiness(store, id)
    return res
