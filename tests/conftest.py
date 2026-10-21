"""Configuración común de pytest: asegura que la raíz del repositorio esté en sys.path."""

import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from geo.config import BRIEF_MD, RUNS_DIR


@pytest.fixture(scope="session", autouse=True)
def _demo_run_ready() -> None:
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["OPENROUTER_API_KEY"] = ""
    if not (RUNS_DIR / "demo" / "propuesta.json").exists():
        from geo.orchestrator import Run

        Run(run_id="demo", modo="cliente", brief_path=BRIEF_MD, provider="mock").run_all(auto_approve=True)
