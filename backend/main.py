"""Crea la app FastAPI, monta los routers bajo /api y sirve frontend/dist en /."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api_models import Health
from backend.deps import VERSION, get_runner, get_store
from backend.routers import checkpoints, estimates, exports, inputs, projects, results, run, settings, study, traces
from backend.services.example import ensure_example

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        ensure_example(get_store(), get_runner())
    except Exception:  # el ejemplo nunca impide arrancar la aplicación
        logging.getLogger(__name__).exception("No se pudo preparar el proyecto de ejemplo")
    yield


app = FastAPI(title="GEO Copilot API", version=VERSION, docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)


def _error(status: int, code: str, message: str, detail: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "detail": detail or {}}})


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        d = exc.detail
        return _error(exc.status_code, d["code"], d.get("message", ""), d.get("detail"))
    return _error(exc.status_code, "error", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error(422, "entrada_invalida", "Los datos enviados no son válidos.", {"errores": exc.errors()})


@app.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(ok=True, version=VERSION)


for module in (projects, inputs, study, run, checkpoints, results, exports, settings, estimates, traces):
    app.include_router(module.router, prefix="/api")

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
