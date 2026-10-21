"""backend/deps.py: Inyección de dependencias y servicios singleton para FastAPI."""

from __future__ import annotations

from pathlib import Path
from geo import settings as _settings
from backend.services.events import EventBus
from backend.services.runner import JobRunner
from backend.services.store import ProjectStore

VERSION = "1.0.0"

ROOT = Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    raw = _settings.get("GEO_DATA_DIR") or "./data"
    p = Path(raw)
    if not p.is_absolute():
        p = ROOT / p
    return p / "projects"


_store: ProjectStore | None = None
_bus: EventBus | None = None
_runner: JobRunner | None = None


def get_store() -> ProjectStore:
    global _store
    if _store is None:
        _store = ProjectStore(get_data_dir())
    return _store


def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def get_runner() -> JobRunner:
    global _runner
    if _runner is None:
        _runner = JobRunner(get_store(), get_bus())
    return _runner
