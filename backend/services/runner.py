"""JobRunner: un trabajo a la vez, en un hilo, con progreso persistente, cancelación cooperativa y eventos SSE.

Sustituye a `geo/jobs.py` (que era del flujo Streamlit). Escribe `run/progress.json` de forma atómica para
sobrevivir a reinicios y `run/job.json` con los contadores acumulados (tiempo, llamadas, coste).

TODO(I1): cuando B integre `Run(run_dir=..., study_dir=...)` desaparece el parche de `engine.engine_paths`;
cuando C integre `geo.study`, el estudio en vivo (`_run_live_study`) llama a sus funciones reales.
"""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path
from typing import Any

from geo import settings as gs
from geo.llm import get_llm_stats, reset_llm_stats

from backend.errors import api_error, conflict, locked, not_found, unprocessable
from backend.services import engine, estimates, inputs, study_files as sf
from backend.services.events import EventBus
from backend.services.pipeline import ANALYSIS_STEPS, CHECKPOINTS, CHECKPOINT_TITLES, LIVE_STEPS, STEP_NAMES, STEP_TO_CHECKPOINT, steps_from
from backend.services.store import ProjectStore, atomic_write_json, now_iso, read_json

FINAL_STATES = ("esperando_revision", "completado", "error", "interrumpido")


class _Job:
    def __init__(self, pid: str, kind: str, base: dict[str, Any]) -> None:
        self.pid = pid
        self.kind = kind
        self.cancel = threading.Event()
        self.started = time.monotonic()
        self.base_elapsed = float(base.get("elapsed_s", 0.0))
        self.base_cost = float(base.get("coste_eur", 0.0))
        self.base_calls = int(base.get("llamadas", 0))
        self.current_step: str | None = None
        self.mock = True
        self.counter: dict[str, Any] | None = None
        self.live: dict[str, dict[str, Any]] = {}
        self.thread: threading.Thread | None = None

    @property
    def alive(self) -> bool:
        return self.thread is not None and self.thread.is_alive()


class JobRunner:
    def __init__(self, store: ProjectStore, bus: EventBus) -> None:
        self.store = store
        self.bus = bus
        self._job: _Job | None = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------ consulta
    def running_pid(self) -> str | None:
        with self._lock:
            return self._job.pid if self._job and self._job.alive else None

    def is_running(self, pid: str) -> bool:
        return self.running_pid() == pid

    def join(self, timeout: float = 60.0) -> None:
        """Espera a que termine el trabajo en curso (tests)."""
        job = self._job
        if job and job.thread:
            job.thread.join(timeout)

    def reconcile(self, pid: str) -> None:
        """Un proyecto `en_ejecucion` sin hilo vivo (servidor reiniciado) pasa a `interrumpido`."""
        p = self.store.require(pid)
        if p["estado"] == "en_ejecucion" and not self.is_running(pid):
            self.store.update(pid, estado="interrumpido")
            self._save_job_info(pid, error="El trabajo se interrumpió (se cerró el servidor).")

    # ------------------------------------------------------------ job.json
    def _job_info(self, pid: str) -> dict[str, Any]:
        return read_json(self.store.run_dir(pid) / "job.json", {}) or {}

    def _save_job_info(self, pid: str, **fields: Any) -> dict[str, Any]:
        info = self._job_info(pid)
        info.update(fields)
        atomic_write_json(self.store.run_dir(pid) / "job.json", info)
        return info

    # ------------------------------------------------------------ progreso
    def _traces(self, pid: str) -> list[dict[str, Any]]:
        out = []
        p = self.store.run_dir(pid) / "trace.jsonl"
        if p.exists():
            import json

            for line in p.read_text(encoding="utf-8").splitlines():
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out

    def _is_mock(self, pid: str) -> bool:
        return (self.store.read_state(pid).get("provider") or "mock") == "mock"

    def _cost_now(self, job: _Job) -> tuple[int, float, bool]:
        stats = get_llm_stats()
        mock = job.mock
        calls = job.base_calls + int(stats.get("calls", 0))
        cost = 0.0 if mock else job.base_cost + float(stats.get("estimated_cost_eur", 0.0))
        return calls, round(cost, 4), bool(stats.get("cost_is_real", False)) and not mock

    def progress(self, pid: str) -> dict[str, Any]:
        """`Progress` del contrato, reconstruido desde `state.json`, la traza y el trabajo en curso."""
        self.reconcile(pid)
        p = self.store.require(pid)
        st = self.store.read_state(pid)
        job = self._job if self.is_running(pid) else None
        steps_state = st.get("steps", {}) or {}
        degradados = st.get("degradados", {}) or {}
        traces = self._traces(pid)
        last: dict[str, dict[str, Any]] = {}
        for t in traces:
            last[t.get("step", "")] = t
        mock = (st.get("provider") or "mock") == "mock"
        ref = inputs.is_reference(self.store, pid)
        live = p.get("origen_datos") == "vivo" and not ref
        pasos: list[dict[str, Any]] = []
        for sid in (LIVE_STEPS if live else ()) + ANALYSIS_STEPS:
            if sid in LIVE_STEPS:
                info = (job.live.get(sid) if job else None) or (self._job_info(pid).get("live", {}) or {}).get(sid, {})
                estado = info.get("estado", "pendiente")
                pasos.append({"id": sid, "nombre": STEP_NAMES[sid], "estado": estado, "duracion_s": info.get("duracion_s"),
                              "llamadas": int(info.get("llamadas", 0)), "coste_eur": float(info.get("coste_eur", 0.0)), "error": info.get("error")})
                continue
            raw = steps_state.get(sid, "pending")
            if job and job.current_step == sid and raw != "done":
                estado = "en_curso"
            elif raw == "done":
                estado = "hecho_automatico" if sid in degradados else "hecho"
            elif raw == "error":
                estado = "error"
            elif raw == "awaiting_human":
                estado = "esperando_revision"
            else:
                estado = "pendiente"
            t = last.get(sid, {})
            pasos.append({
                "id": sid, "nombre": STEP_NAMES[sid], "estado": estado,
                "duracion_s": t.get("duration_s") if estado in ("hecho", "hecho_automatico") else None,
                "llamadas": int(t.get("llm_calls", 0) or 0),
                "coste_eur": 0.0 if mock else round(float(t.get("estimated_cost_eur", 0.0) or 0.0), 4),
                "error": degradados.get(sid) or (t.get("error") if estado in ("error", "hecho_automatico") else None),
            })
        info = self._job_info(pid)
        if job:
            estado_global = "en_ejecucion"
            llamadas, coste, real = self._cost_now(job)
            transcurrido = job.base_elapsed + (time.monotonic() - job.started)
            actual, contador = job.current_step, job.counter
        else:
            estado_global = p["estado"] if p["estado"] in FINAL_STATES else "interrumpido"
            llamadas, coste, real = int(info.get("llamadas", 0)), float(info.get("coste_eur", 0.0)), bool(info.get("coste_real", False))
            transcurrido, contador = float(info.get("elapsed_s", 0.0)), None
            actual = next((s["id"] for s in pasos if s["estado"] == "esperando_revision"), None)
        return {"estado": estado_global, "paso_actual": actual, "pasos": pasos, "contador": contador, "llamadas": llamadas,
                "coste_eur": coste, "coste_real": real, "transcurrido_s": round(transcurrido, 1)}

    def _persist_progress(self, pid: str) -> None:
        try:
            atomic_write_json(self.store.run_dir(pid) / "progress.json", self.progress(pid))
        except Exception:
            pass

    # ------------------------------------------------------------ lanzamiento
    def launch(self, pid: str, kind: str, *, confirmo_coste: bool = False, desde_paso: str | None = None,
               paso: str | None = None, reuse_confirmation: bool = False) -> dict[str, Any]:
        """Valida, prepara el estado y arranca el hilo. Devuelve el `Progress` inicial."""
        with self._lock:
            if self._job and self._job.alive:
                raise locked()
            p = self.store.require(pid)
            self._validate_kind(pid, p, kind, desde_paso, paso)
            inputs.detect_and_store(self.store, pid)
            ref = inputs.is_reference(self.store, pid)
            provider = estimates.effective_provider(self.store, pid)
            if provider == "openrouter" and not gs.has_openrouter_key():
                raise unprocessable("sin_clave", "Falta la clave de OpenRouter. Configúrala en Ajustes antes de lanzar el análisis.")
            if provider not in ("openrouter", "mock"):
                raise unprocessable("proveedor_no_valido", "El proveedor de IA configurado no es válido (usa openrouter).")
            live = p.get("origen_datos") == "vivo" and not ref and kind == "run"
            self._check_cost(pid, provider, kind, desde_paso, paso, live, confirmo_coste or reuse_confirmation)
            self._prepare_state(pid, p, provider, kind, desde_paso, paso)
            inputs.write_reference_check(self.store, pid, provider)
            info = self._job_info(pid)
            if kind == "run":
                info = {}
            base = {k: info.get(k, 0) for k in ("elapsed_s", "coste_eur", "llamadas")}
            job = _Job(pid, kind, base)
            job.mock = provider == "mock"
            self._job = job
            self.store.update(pid, estado="en_ejecucion")
            self._save_job_info(pid, error=None, coste_confirmado=bool(confirmo_coste or reuse_confirmation or info.get("coste_confirmado")),
                                **({"elapsed_s": 0.0, "coste_eur": 0.0, "llamadas": 0, "live": {}} if kind == "run" else {}))
            job.thread = threading.Thread(target=self._execute, args=(job, provider, live), name=f"job-{pid}", daemon=True)
            job.thread.start()
        return self.progress(pid)

    def _validate_kind(self, pid: str, p: dict[str, Any], kind: str, desde_paso: str | None, paso: str | None) -> None:
        estado = p["estado"]
        if kind == "run":
            if estado == "borrador":
                inputs.refresh_readiness(self.store, pid)
                p = self.store.require(pid)
            if p["estado"] == "borrador":
                falta = []
                if (inputs.read_prospect(self.store, pid) is None) if p["tipo"] == "prospecto" else (inputs.read_brief(self.store, pid) is None):
                    falta.append("brief" if p["tipo"] == "cliente" else "datos de la marca")
                if not inputs.study_ready(self.store, pid):
                    falta.append("datos del estudio")
                raise unprocessable("faltan_entradas", "Faltan datos para lanzar el análisis: " + ", ".join(falta) + ".", {"faltan": falta})
            if p["estado"] != "listo_para_lanzar":
                raise conflict("estado_no_valido", "Este proyecto ya se ha lanzado. Usa «Reanudar» o «Recalcular».")
        elif kind == "resume":
            if estado in ("interrumpido", "error"):
                return
            if estado == "esperando_revision":
                pend = [n for n, (name, step, _) in CHECKPOINTS.items() if self.store.read_state(pid).get("steps", {}).get(step) == "awaiting_human"]
                if pend:
                    raise conflict("punto_control_pendiente", f"Aprueba primero el punto de control «{CHECKPOINT_TITLES[pend[0]]}».")
                return
            raise conflict("estado_no_valido", "No hay nada que reanudar en este proyecto.")
        elif kind in ("retry", "recompute", "regenerate"):
            if estado in ("borrador", "listo_para_lanzar"):
                raise conflict("sin_resultados", "El proyecto todavía no se ha ejecutado.")
            if kind == "retry":
                steps = self.store.read_state(pid).get("steps", {})
                if paso not in ANALYSIS_STEPS:
                    raise unprocessable("paso_no_valido", "El paso indicado no existe.", {"pasos": list(ANALYSIS_STEPS)})
                deg = self.store.read_state(pid).get("degradados", {})
                if steps.get(paso) != "error" and paso not in deg:
                    raise conflict("paso_no_degradado", "Solo se pueden reintentar pasos con error o hechos en modo automático.")
            if kind == "recompute" and desde_paso not in ANALYSIS_STEPS:
                raise unprocessable("paso_no_valido", "El paso indicado no existe.", {"pasos": list(ANALYSIS_STEPS)})
            if kind == "regenerate" and estado != "completado":
                raise conflict("sin_propuesta", "La propuesta todavía no existe: espera a que termine el análisis.")

    def _steps_to_reset(self, kind: str, desde_paso: str | None, paso: str | None) -> list[str]:
        if kind == "retry":
            return steps_from(paso or "intake")
        if kind == "recompute":
            return steps_from(desde_paso or "intake")
        if kind == "regenerate":
            return steps_from("write")
        return []

    def _check_cost(self, pid: str, provider: str, kind: str, desde_paso: str | None, paso: str | None, live: bool, confirmado: bool) -> None:
        if provider == "mock":
            return
        if kind in ("run", "resume"):
            est = estimates.total_estimate(self.store, pid, live=live)
        else:
            est = estimates.analysis_estimate(self.store, pid, steps=self._steps_to_reset(kind, desde_paso, paso))
        if est["supera_tope"]:
            raise unprocessable("supera_tope", f"La estimación ({est['total_eur']:.2f} €) supera el tope de gasto ({est['tope_eur']:.2f} €). Ajusta el estudio o el tope en Ajustes.",
                                {"total_eur": est["total_eur"], "tope_eur": est["tope_eur"]})
        if est["total_eur"] > 0 and not confirmado:
            raise unprocessable("confirmacion_coste", "Confirma el coste estimado antes de continuar (confirmo_coste: true).", {"total_eur": est["total_eur"]})

    def _prepare_state(self, pid: str, p: dict[str, Any], provider: str, kind: str, desde_paso: str | None, paso: str | None) -> None:
        brief = self.store.inputs_dir(pid) / "brief.txt"
        prospecto = p["tipo"] == "prospecto"
        pros = inputs.read_prospect(self.store, pid) or {}
        st = self.store.read_state(pid) or {}
        st = self.store.patch_state(pid, modo=p["tipo"], provider=provider, brief_path=str(brief),
                                    marca_prospecto=pros.get("marca") if prospecto else None)
        reset = self._steps_to_reset(kind, desde_paso, paso)
        if reset:
            steps = st.get("steps", {})
            deg = st.get("degradados", {})
            for s in reset:
                steps[s] = "pending"
                deg.pop(s, None)
            self.store.patch_state(pid, steps=steps, degradados=deg)
        if kind == "resume":  # los pasos con error se vuelven a intentar
            steps = st.get("steps", {})
            changed = False
            for s, v in list(steps.items()):
                if v == "error":
                    steps[s] = "pending"
                    changed = True
            if changed:
                self.store.patch_state(pid, steps=steps)

    # ------------------------------------------------------------ hilo
    def _execute(self, job: _Job, provider: str, live: bool) -> None:
        pid = job.pid
        estado, error = "completado", None
        hooks = _Hooks(self, job)
        try:
            reset_llm_stats()
            if live:
                self._run_live_study(job)
            self._run_analysis(job, provider, hooks)
            estado = "esperando_revision" if self._awaiting(pid) is not None else "completado"
        except engine.JobCancelled:
            estado = "interrumpido"
            error = "Cancelado por el consultor."
        except Exception as exc:  # error del motor o de la API de IA
            estado, error = "error", _safe_message(exc)
        finally:
            self._finish(job, estado, error)

    def _awaiting(self, pid: str) -> int | None:
        steps = self.store.read_state(pid).get("steps", {})
        for step, n in STEP_TO_CHECKPOINT.items():
            if steps.get(step) == "awaiting_human":
                return n
        return None

    def _run_analysis(self, job: _Job, provider: str, hooks: "_Hooks") -> None:
        pid = job.pid
        p = self.store.require(pid)
        study = self.store.study_dir(pid)
        continuo = p.get("revision") == "continuo"
        prospect_ficha = None
        if p["tipo"] == "prospecto":
            pros = inputs.read_prospect(self.store, pid)
            prospect_ficha = inputs.ficha_from_prospect(pros) if pros else None
        with engine.engine_paths(study, prospect_ficha):
            run = engine.make_run(project_dir=self.store.project_dir(pid), study_dir=study, modo=p["tipo"],
                                  brief_path=self.store.inputs_dir(pid) / "brief.txt",
                                  marca_prospecto=(inputs.read_prospect(self.store, pid) or {}).get("marca") if p["tipo"] == "prospecto" else None,
                                  provider=provider, hooks=hooks)
            run.on_event = hooks.on_event
            run.on_progress = hooks.on_progress
            run.run_all(auto_approve=continuo, stop_at_checkpoint=not continuo)

    def _run_live_study(self, job: _Job) -> None:
        """Estudio en vivo (B2.3 y B2.4).

        TODO(I1): `geo.study` es del agente C. Se llama por la firma del contrato cuando exista.
        """
        try:
            from geo.study import runner as study_runner  # type: ignore
            from geo.study import sources as study_sources  # type: ignore
        except Exception as exc:
            raise RuntimeError("El estudio en vivo todavía no está disponible en esta instalación.") from exc
        pid = job.pid
        hooks = _Hooks(self, job)
        study = self.store.study_dir(pid)
        for sid in LIVE_STEPS:
            hooks.live_step(sid, "pendiente")
        hooks.live_step("queries", "en_curso")
        study_runner.run_study(study_dir=study, ficha=inputs.current_ficha(self.store, pid), config=sf.read_config(study),  # type: ignore[attr-defined]
                               on_progress=lambda h, t: hooks.on_progress("queries", h, t), should_cancel=job.cancel.is_set)
        hooks.live_step("queries", "hecho")
        hooks.before_step("sources")
        hooks.live_step("sources", "en_curso")
        study_sources.classify_sources(study_dir=study)  # type: ignore[attr-defined]
        hooks.live_step("sources", "hecho")

    def _finish(self, job: _Job, estado: str, error: str | None) -> None:
        pid = job.pid
        with self._lock:
            calls, cost, real = self._cost_now(job)
            elapsed = job.base_elapsed + (time.monotonic() - job.started)
            if estado in ("completado", "esperando_revision"):
                self._collect_exports(pid)
            if estado == "esperando_revision" and self._awaiting(pid) is None:
                estado = "completado"
            job.current_step = None
            job.counter = None
            self._save_job_info(pid, elapsed_s=round(elapsed, 1), llamadas=calls, coste_eur=cost, coste_real=real, error=error,
                                live=job.live)
            self.store.update(pid, estado=estado, coste_eur=cost)
            self._persist_progress(pid)
            if estado == "esperando_revision":
                n = self._awaiting(pid)
                if n is not None:
                    self.bus.publish(pid, "checkpoint", {"n": n, "nombre": CHECKPOINT_TITLES[n]})
            self.bus.flush(pid)
            payload: dict[str, Any] = {"estado": estado}
            if error:
                payload["error"] = error
            self.bus.publish(pid, "done", payload)
            self._job = None

    def _collect_exports(self, pid: str) -> None:
        run_dir, out = self.store.run_dir(pid), self.store.exports_dir(pid)
        out.mkdir(parents=True, exist_ok=True)
        for f in list(run_dir.glob("propuesta_*.docx")) + list(run_dir.glob("propuesta_*.md")):
            shutil.copyfile(f, out / f.name)

    # ------------------------------------------------------------ cancelar y aprobar
    def cancel(self, pid: str) -> dict[str, Any]:
        with self._lock:
            if not self.is_running(pid):
                raise conflict("sin_trabajo", "No hay ningún trabajo en ejecución en este proyecto.")
            self._job.cancel.set()  # type: ignore[union-attr]
        return self.progress(pid)

    def approve(self, pid: str, n: int, nota: str | None) -> dict[str, Any]:
        """Aprueba el punto de control `n` y retoma el trabajo desde el paso siguiente."""
        with self._lock:
            self.store.require(pid)
            if n not in CHECKPOINTS:
                raise unprocessable("punto_control_no_valido", "El punto de control debe estar entre 0 y 3.")
            if self.running_pid():
                raise conflict("trabajo_en_curso", "Hay un análisis en ejecución; espera a que pare en el punto de control.")
            name, step, _ = CHECKPOINTS[n]
            st = self.store.read_state(pid)
            if (st.get("steps", {}) or {}).get(step) != "awaiting_human":
                raise conflict("punto_control_no_pendiente", f"El punto de control «{CHECKPOINT_TITLES[n]}» no está esperando revisión.")
            steps = st["steps"]
            steps[step] = "done"
            cps = st.setdefault("checkpoints", {})
            cps[name] = True
            aprob = st.setdefault("human_approvals", [])
            aprob.append({"checkpoint": name, "timestamp": time_iso_local(), "note": nota or "Aprobado"})
            self.store.patch_state(pid, steps=steps, checkpoints=cps, human_approvals=aprob)
            if n == 1:
                mk = self.store.run_dir(pid) / "market.json"
                data = read_json(mk)
                if data is not None:
                    data["aprobado_por_humano"] = True
                    atomic_write_json(mk, data)
            confirmed = bool(self._job_info(pid).get("coste_confirmado"))
            self.launch(pid, "resume", reuse_confirmation=confirmed)
        return self.store.view(pid)


def time_iso_local() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


def _safe_message(exc: Exception) -> str:
    """Mensaje de error apto para el consultor (nunca incluye claves)."""
    msg = str(exc) or exc.__class__.__name__
    key = gs.get("OPENROUTER_API_KEY")
    if key:
        msg = msg.replace(key, "…")
    return msg[:500]


class _Hooks:
    """Puente entre el motor y el runner: cancelación, eventos SSE y contadores."""

    def __init__(self, runner: JobRunner, job: _Job) -> None:
        self.r, self.job = runner, job

    def before_step(self, step: str) -> None:
        if self.job.cancel.is_set():
            raise engine.JobCancelled()

    def step_started(self, step: str) -> None:
        self.job.current_step = step
        self.job.counter = None
        self.r.bus.publish(self.job.pid, "step", {"paso": step, "estado": "en_curso"})
        self.r._persist_progress(self.job.pid)

    def live_step(self, step: str, estado: str) -> None:
        self.job.live.setdefault(step, {})["estado"] = estado
        if estado == "en_curso":
            self.job.current_step = step
        self.r.bus.publish(self.job.pid, "step", {"paso": step, "estado": estado})

    def on_event(self, step: str, estado: str, info: dict[str, Any]) -> None:
        pid = self.job.pid
        if estado == "done":
            deg = step in (self.r.store.read_state(pid).get("degradados") or {})
            mock = self.job.mock
            payload = {"paso": step, "estado": "hecho_automatico" if deg else "hecho", "duracion_s": info.get("duration_s"),
                       "llamadas": int(info.get("llm_calls", 0) or 0), "coste_eur": 0.0 if mock else float(info.get("cost_eur", 0.0) or 0.0)}
            self.r.bus.publish(pid, "step", payload)
            self.r.bus.flush(pid)
            self._cost()
            self.r._persist_progress(pid)

    def on_progress(self, step: str, hechos: int, total: int) -> None:
        self.job.counter = {"paso": step, "hechos": int(hechos), "total": int(total)}
        self.r.bus.publish_limited(self.job.pid, "counter", dict(self.job.counter))
        self._cost()
        if self.job.cancel.is_set():
            raise engine.JobCancelled()

    def _cost(self) -> None:
        calls, cost, real = self.r._cost_now(self.job)
        self.r.bus.publish_limited(self.job.pid, "cost", {"llamadas": calls, "coste_eur": cost, "coste_real": real})
