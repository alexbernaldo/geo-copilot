"""Router `run`."""

from __future__ import annotations

import asyncio
import queue
import time
from typing import Any
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from backend.api_models import ConfirmaCoste, Progress
from backend.deps import get_bus, get_runner, get_store
from backend.services.events import EventBus, PING_SECONDS, sse_message
from backend.services.runner import JobRunner
from backend.services.store import ProjectStore

router = APIRouter()


@router.post("/projects/{id}/run", response_model=Progress, status_code=status.HTTP_202_ACCEPTED, summary="Lanza el análisis (423 si hay otro trabajo)")
def post_projects_id_run(
    id: str,
    body: ConfirmaCoste | None = None,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    confirmo = bool(body.confirmo_coste) if body else False
    return runner.launch(id, "run", confirmo_coste=confirmo)


@router.post("/projects/{id}/run/resume", response_model=Progress, status_code=status.HTTP_202_ACCEPTED, summary="Reanuda tras interrupción o aprobación")
def post_projects_id_run_resume(
    id: str,
    body: ConfirmaCoste | None = None,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    confirmo = bool(body.confirmo_coste) if body else False
    return runner.launch(id, "resume", confirmo_coste=confirmo)


@router.post("/projects/{id}/run/retry-step", response_model=Progress, status_code=status.HTTP_202_ACCEPTED, summary="Reintenta un paso degradado")
def post_projects_id_run_retry_step(
    id: str,
    body: dict[str, Any],
    runner: JobRunner = Depends(get_runner),
) -> Any:
    paso = body.get("paso")
    confirmo = bool(body.get("confirmo_coste", False))
    return runner.launch(id, "retry", paso=paso, confirmo_coste=confirmo)


@router.post("/projects/{id}/run/cancel", response_model=Progress, summary="Cancela (termina tras la llamada en curso)")
def post_projects_id_run_cancel(
    id: str,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    return runner.cancel(id)


@router.get("/projects/{id}/progress", response_model=Progress, summary="Progreso")
def get_projects_id_progress(
    id: str,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    return runner.progress(id)


@router.get("/projects/{id}/events", summary="SSE de progreso (ver contracts/events.md)")
async def get_projects_id_events(
    id: str,
    request: Request,
    store: ProjectStore = Depends(get_store),
    bus: EventBus = Depends(get_bus),
    runner: JobRunner = Depends(get_runner),
) -> StreamingResponse:
    store.require(id)
    q = bus.subscribe(id)

    async def event_generator():
        try:
            # 1. Snapshot inicial
            prog = runner.progress(id)
            yield sse_message("snapshot", prog)
            
            last_ping = time.monotonic()
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Non-blocking get with short sleep
                    ev, data = q.get_nowait()
                    yield sse_message(ev, data)
                    last_ping = time.monotonic()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                
                # Check 15s ping
                now = time.monotonic()
                if now - last_ping >= PING_SECONDS:
                    yield sse_message("ping", {})
                    last_ping = now
        finally:
            bus.unsubscribe(id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
