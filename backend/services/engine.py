"""Adaptador entre la API y el motor `geo/`.

TODO(I1): el motor (agente B) todavía no acepta `Run(run_dir=..., study_dir=...)`. Mientras tanto este módulo:
  - abre el `Run` con `runs_root=<proyecto>` y `run_id="run"` (así `run_dir` es `data/projects/<id>/run`);
  - redirige temporalmente `load_marcas/load_ejecuciones/load_fuentes` del orquestador a `study/` del proyecto.
Cuando `Run.__init__` acepte `study_dir`, el parche deja de aplicarse solo.
"""

from __future__ import annotations

import inspect
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from geo import orchestrator as orch
from geo.schemas import FichaMarca

from backend.services import study_files as sf

ENGINE_LOCK = threading.RLock()


class JobCancelled(Exception):
    """El consultor canceló el trabajo; se detiene entre pasos."""


def _supports_study_dir() -> bool:
    return "study_dir" in inspect.signature(orch.Run.__init__).parameters


@contextmanager
def engine_paths(study_dir: Path, prospect_ficha: FichaMarca | None = None) -> Iterator[None]:
    """Hace que el orquestador lea los datos del estudio del proyecto (parche temporal, un solo trabajo a la vez)."""
    if _supports_study_dir():
        yield
        return
    from geo import loader

    d = Path(study_dir)
    with ENGINE_LOCK:
        saved = (orch.load_marcas, orch.load_ejecuciones, orch.load_fuentes, orch._prospect_ficha)
        fuentes = sf.study_file(d, "fuentes_catalogo")

        orch.load_marcas = lambda: loader.load_marcas(sf.study_file(d, "marcas"))  # type: ignore[assignment]
        orch.load_ejecuciones = lambda: loader.load_ejecuciones(sf.study_file(d, "ejecuciones"), sf.study_file(d, "banco_prompts"))  # type: ignore[assignment]
        orch.load_fuentes = lambda: loader.load_fuentes(fuentes) if fuentes.exists() else {}  # type: ignore[assignment]
        if prospect_ficha is not None:
            orch._prospect_ficha = lambda *_a, **_k: prospect_ficha  # type: ignore[assignment]
        try:
            yield
        finally:
            orch.load_marcas, orch.load_ejecuciones, orch.load_fuentes, orch._prospect_ficha = saved  # type: ignore[assignment]


class JobRun(orch.Run):
    """`Run` con cancelación cooperativa y aviso de inicio de paso (el orquestador solo avisa al terminar)."""

    job_hooks: Any = None

    def _run_tracked_step(self, step: str, output_file: Path, *args: Any, **kwargs: Any) -> None:
        hooks = self.job_hooks
        if hooks is not None:
            hooks.before_step(step)
            will_run = kwargs.get("force") or not (self.state["steps"].get(step) == "done" and Path(output_file).exists())
            if will_run:
                hooks.step_started(step)
        super()._run_tracked_step(step, output_file, *args, **kwargs)


def make_run(*, project_dir: Path, study_dir: Path, modo: str, brief_path: Path, marca_prospecto: str | None,
             provider: str, hooks: Any = None) -> JobRun:
    params = inspect.signature(orch.Run.__init__).parameters
    kw: dict[str, Any] = {"modo": modo, "brief_path": brief_path, "marca_prospecto": marca_prospecto, "provider": provider}
    if "study_dir" in params:
        kw["study_dir"] = study_dir
    if "run_dir" in params:
        kw["run_dir"] = Path(project_dir) / "run"
    else:
        kw.update(run_id="run", runs_root=Path(project_dir))
    run = JobRun(**kw)
    run.job_hooks = hooks
    return run
