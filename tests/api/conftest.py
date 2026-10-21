"""Fixtures para los tests de la API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

import backend.deps as deps
from backend.main import app
from backend.services.events import EventBus
from backend.services.runner import JobRunner
from backend.services.store import ProjectStore

from geo.config import BRIEF_MD

ROOT = Path(__file__).resolve().parents[2]
KIT_DIR = ROOT / "geo" / "reference_data"
BRIEF_PATH = BRIEF_MD


@pytest.fixture(autouse=True)
def setup_api_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    data_dir = tmp_path / "data" / "projects"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GEO_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    store = ProjectStore(data_dir)
    bus = EventBus()
    runner = JobRunner(store, bus)

    monkeypatch.setattr(deps, "_store", store)
    monkeypatch.setattr(deps, "_bus", bus)
    monkeypatch.setattr(deps, "_runner", runner)

    yield

    running = runner.running_pid()
    if running:
        try:
            runner.cancel(running)
            runner.join(timeout=2.0)
        except Exception:
            pass


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def kit_brief_text() -> str:
    return BRIEF_PATH.read_text(encoding="utf-8")


@pytest.fixture
def kit_csvs() -> dict[str, Path]:
    return {
        "ejecuciones.csv": KIT_DIR / "ejecuciones.csv",
        "marcas.csv": KIT_DIR / "marcas.csv",
        "banco_prompts.csv": KIT_DIR / "banco_prompts.csv",
    }
