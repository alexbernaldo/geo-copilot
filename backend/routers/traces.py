"""Router `traces` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.get("/projects/{id}/traces", summary='trace.jsonl como lista')
def get_projects_id_traces() -> None:
    not_implemented()
