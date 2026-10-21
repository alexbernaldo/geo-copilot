"""Router `traces`."""

from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, Depends

from backend.deps import get_store
from backend.services.store import ProjectStore

router = APIRouter()


@router.get("/projects/{id}/traces", summary="trace.jsonl como lista")
def get_projects_id_traces(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> list[dict[str, Any]]:
    store.require(id)
    p = store.run_dir(id) / "trace.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out
