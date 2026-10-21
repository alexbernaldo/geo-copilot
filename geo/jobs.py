"""Trabajos en segundo plano para ejecutar análisis desde la UI."""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from geo.config import RUNS_DIR, BRIEF_MD
from geo.orchestrator import Run
from geo import settings as _settings

_JOBS: dict[str, threading.Thread] = {}
_JOBS_LOCK = threading.Lock()


def _progress_path(run_id: str) -> Path:
    return RUNS_DIR / run_id / "progress.json"


def _write_progress(run_id: str, data: dict[str, Any]) -> None:
    p = _progress_path(run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


class _Progress:
    def __init__(self, run_id: str, run: Run) -> None:
        self.run_id = run_id
        self.run = run
        self.status = "running"
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.t0 = time.time()
        self.steps: dict[str, dict[str, Any]] = {s: {"status": "pending"} for s in run.state.get("steps", {}) or {}}
        # init steps from PIPELINE_STEPS
        from geo.orchestrator import PIPELINE_STEPS
        self.steps = {s: {"status": "pending"} for s in PIPELINE_STEPS}
        self.current: str | None = None
        self.judge_done = 0
        self.judge_total = 0
        self.llm_calls = 0
        self.cost_eur = 0.0
        self.cost_is_real = False
        self.error: str | None = None
        self.models = run.state.get("models", {})
        self._last_write = 0.0
        self._lock = threading.Lock()

    def _snapshot(self) -> dict[str, Any]:
        from geo.llm import get_llm_stats
        stats = get_llm_stats()
        return {
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at,
            "elapsed_s": round(time.time() - self.t0, 1),
            "provider": self.run.provider,
            "models": self.models,
            "steps": self.steps,
            "current": self.current,
            "judge": {"done": self.judge_done, "total": self.judge_total},
            "llm_calls": stats.get("calls", 0),
            "cost_eur": stats.get("estimated_cost_eur", 0.0),
            "cost_is_real": stats.get("cost_is_real", False),
            "error": self.error,
            "degradados": self.run.state.get("degradados", {}),
        }

    def _flush(self, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self._last_write < 0.4):
            return
        self._last_write = now
        try:
            _write_progress(self.run_id, self._snapshot())
        except Exception:
            pass

    def on_event(self, step: str, estado: str, info: dict) -> None:
        with self._lock:
            if step not in self.steps:
                self.steps[step] = {"status": "pending"}
            if estado == "start":
                self.steps[step]["status"] = "running"
                self.current = step
            elif estado == "degraded":
                self.steps[step]["status"] = "degraded"
                self.steps[step]["error"] = (info or {}).get("error")
            elif estado == "done":
                self.steps[step]["status"] = "done"
                self.steps[step]["duration_s"] = (info or {}).get("duration_s")
                self.steps[step]["llm_calls"] = (info or {}).get("llm_calls")
            elif estado == "error":
                self.steps[step]["status"] = "error"
                self.error = (info or {}).get("error")
            self._flush(force=True)

    def on_progress(self, step: str, hechos: int, total: int) -> None:
        with self._lock:
            if step == "judge":
                self.judge_done = hechos
                self.judge_total = total
            self._flush(force=False)


def start(*, modo: str, provider: str, brief_path: str | Path | None,
          marca_prospecto: str | None, meta: dict | None = None) -> str:
    # one at a time
    with _JOBS_LOCK:
        for rid, t in list(_JOBS.items()):
            if t.is_alive():
                raise RuntimeError("Ya hay un análisis en curso.")
    # copy brief
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{ts}_ui"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    bp = Path(brief_path) if brief_path else BRIEF_MD
    if bp and Path(bp).exists() and Path(bp).is_file():
        ext = Path(bp).suffix or ".md"
        dest = run_dir / f"brief_original{ext}"
        shutil.copyfile(bp, dest)
        bp = dest
    run = Run(run_id=run_id, modo=modo, brief_path=bp, marca_prospecto=marca_prospecto, provider=provider)
    # models from settings
    run.state["models"] = {
        "juez_y_revisor": _settings.get("LLM_MODEL"),
        "estrategia_y_redaccion": _settings.get("LLM_MODEL_WRITER"),
    }
    run._save_state()
    progress = _Progress(run_id, run)
    run.on_event = progress.on_event
    run.on_progress = progress.on_progress

    def _worker():
        try:
            run.run_all(auto_approve=True, force=True)
            progress.status = "done"
        except Exception as exc:
            progress.status = "error"
            progress.error = str(exc)
        finally:
            progress._flush(force=True)
            with _JOBS_LOCK:
                _JOBS.pop(run_id, None)

    t = threading.Thread(target=_worker, daemon=True)
    with _JOBS_LOCK:
        _JOBS[run_id] = t
    t.start()
    # initial progress file
    progress._flush(force=True)
    return run_id


def is_running(run_id: str) -> bool:
    with _JOBS_LOCK:
        t = _JOBS.get(run_id)
        if t is not None:
            return t.is_alive()
    # check progress file
    p = _progress_path(run_id)
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return d.get("status") == "running"
        except Exception:
            return False
    return False


def any_running() -> str | None:
    with _JOBS_LOCK:
        for rid, t in _JOBS.items():
            if t.is_alive():
                return rid
    # check progress files
    if RUNS_DIR.exists():
        for rd in RUNS_DIR.iterdir():
            if not rd.is_dir():
                continue
            p = rd / "progress.json"
            if p.exists():
                try:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    if d.get("status") == "running":
                        return rd.name
                except Exception:
                    pass
    return None


def read_progress(run_id: str) -> dict | None:
    p = _progress_path(run_id)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if d.get("status") == "running":
        # check thread alive
        alive = False
        with _JOBS_LOCK:
            t = _JOBS.get(run_id)
            if t is not None and t.is_alive():
                alive = True
        if not alive:
            # check any thread
            if not any_running() or any_running() != run_id:
                # mark interrupted
                d["status"] = "interrupted"
                try:
                    _write_progress(run_id, d)
                except Exception:
                    pass
    return d


def list_runs() -> list[dict]:
    out: list[dict] = []
    if not RUNS_DIR.exists():
        return out
    for rd in RUNS_DIR.iterdir():
        if not rd.is_dir():
            continue
        state_path = rd / "state.json"
        if not state_path.exists():
            continue
        try:
            st = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        # cost from progress if exists
        cost_eur = 0.0
        degradados = st.get("degradados", {})
        status = "done"
        prog = rd / "progress.json"
        if prog.exists():
            try:
                pd_ = json.loads(prog.read_text(encoding="utf-8"))
                status = pd_.get("status", status)
                cost_eur = pd_.get("cost_eur", cost_eur)
                degradados = pd_.get("degradados", degradados)
            except Exception:
                pass
        # infer status from steps
        steps = st.get("steps", {})
        if status == "running":
            pass
        elif any(v == "error" for v in steps.values()):
            status = "error"
        elif all(v == "done" for v in steps.values()) and steps:
            status = "done"
        else:
            if status not in ("done", "error", "interrupted"):
                status = "running" if any(v in ("running", "pending") for v in steps.values()) else status
        out.append({
            "run_id": rd.name,
            "marca": _marca_from_state(st),
            "modo": st.get("modo"),
            "provider": st.get("provider"),
            "created_at": st.get("created_at"),
            "status": status,
            "cost_eur": cost_eur,
            "degradados": degradados,
        })
    # demo first, then date desc
    def key(x):
        return (0 if x["run_id"] == "demo" else 1, -( _parse_date(x.get("created_at")) ))
    out.sort(key=lambda x: (0 if x["run_id"] == "demo" else 1, x.get("created_at") or "", ), reverse=False)
    # sort non-demo by created_at desc
    demo = [r for r in out if r["run_id"] == "demo"]
    rest = sorted([r for r in out if r["run_id"] != "demo"], key=lambda x: x.get("created_at") or "", reverse=True)
    return demo + rest


def _marca_from_state(st: dict) -> str:
    # try ficha.json
    return st.get("marca_prospecto") or "Alborada"


def _parse_date(s):
    return s or ""
