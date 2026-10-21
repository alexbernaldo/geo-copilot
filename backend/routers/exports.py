"""Router `exports`."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from backend.deps import get_store
from backend.services import results
from backend.services.store import ProjectStore

router = APIRouter()

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown; charset=utf-8",
}


@router.get("/projects/{id}/exports/{fmt}", summary="Descarga docx o md")
def get_projects_id_exports_fmt(
    id: str,
    fmt: str,
    store: ProjectStore = Depends(get_store),
) -> FileResponse:
    path = results.export_path(store, id, fmt)
    media_type = MEDIA_TYPES.get(fmt, "application/octet-stream")
    return FileResponse(path=path, media_type=media_type, filename=path.name)
