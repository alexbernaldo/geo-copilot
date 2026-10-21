"""ProjectStore: CRUD de proyectos en disco (`data/projects/<id>/`) con escritura atómica y lock por proyecto."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.errors import api_error, not_found
from backend.services.pipeline import CHECKPOINTS, STEP_TO_CHECKPOINT

# Campos públicos de `project.json` (contrato `Project`). Nada de modo de referencia aquí.
PUBLIC_FIELDS: tuple[str, ...] = (
    "id", "nombre", "tipo", "marca", "sector", "origen_datos", "revision", "estado",
    "punto_control_pendiente", "checkpoints", "coste_eur", "creado", "actualizado", "archivado",
)
ESTADOS = ("borrador", "listo_para_lanzar", "en_ejecucion", "esperando_revision", "completado", "error", "interrumpido")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_write_json(path: Path, data: Any) -> None:
    """Escribe JSON de forma atómica (`.tmp` + `replace`)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{secrets.token_hex(3)}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path, default: Any = None, retries: int = 4) -> Any:
    """Lee JSON tolerando escrituras no atómicas del motor (reintenta si el archivo está a medias)."""
    for i in range(retries):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except (json.JSONDecodeError, UnicodeDecodeError):
            if i == retries - 1:
                return default
            time.sleep(0.05)
    return default


class ProjectStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.RLock] = {}
        self._guard = threading.Lock()

    # ---------- rutas ----------
    def project_dir(self, pid: str) -> Path:
        if not pid or "/" in pid or ".." in pid or pid.startswith("."):
            raise not_found()
        return self.root / pid

    def inputs_dir(self, pid: str) -> Path:
        return self.project_dir(pid) / "inputs"

    def study_dir(self, pid: str) -> Path:
        return self.project_dir(pid) / "study"

    def run_dir(self, pid: str) -> Path:
        return self.project_dir(pid) / "run"

    def exports_dir(self, pid: str) -> Path:
        return self.project_dir(pid) / "exports"

    def lock(self, pid: str) -> threading.RLock:
        with self._guard:
            return self._locks.setdefault(pid, threading.RLock())

    # ---------- CRUD ----------
    def exists(self, pid: str) -> bool:
        try:
            return (self.project_dir(pid) / "project.json").exists()
        except Exception:
            return False

    def require(self, pid: str) -> dict[str, Any]:
        data = read_json(self.project_dir(pid) / "project.json") if self.project_dir(pid).is_dir() else None
        if data is None:
            raise not_found()
        return data

    def create(self, nombre: str, tipo: str) -> dict[str, Any]:
        nombre = (nombre or "").strip()
        if not nombre:
            raise api_error(422, "nombre_vacio", "El nombre del proyecto no puede estar vacío.")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = f"p_{stamp}_{secrets.token_hex(3)}"
        ts = now_iso()
        data = {
            "id": pid, "nombre": nombre, "tipo": tipo, "marca": nombre if tipo == "prospecto" else None, "sector": None,
            "origen_datos": None, "revision": "pausas", "estado": "borrador", "punto_control_pendiente": None,
            "checkpoints": {"ficha": False, "competencia": False, "hallazgos": False, "plan": False},
            "coste_eur": 0.0, "creado": ts, "actualizado": ts, "archivado": False,
        }
        d = self.project_dir(pid)
        for sub in ("inputs/uploads", "study", "run", "exports"):
            (d / sub).mkdir(parents=True, exist_ok=True)
        atomic_write_json(d / "project.json", data)
        return data

    def update(self, pid: str, **fields: Any) -> dict[str, Any]:
        with self.lock(pid):
            data = self.require(pid)
            data.update({k: v for k, v in fields.items()})
            data["actualizado"] = now_iso()
            atomic_write_json(self.project_dir(pid) / "project.json", data)
            return data

    def delete(self, pid: str) -> None:
        with self.lock(pid):
            self.require(pid)
            shutil.rmtree(self.project_dir(pid), ignore_errors=True)

    def duplicate(self, pid: str) -> dict[str, Any]:
        """Copia configuración y entradas (no los resultados)."""
        with self.lock(pid):
            src = self.require(pid)
            new = self.create(f"{src['nombre']} (copia)", src["tipo"])
            nd, sd = self.project_dir(new["id"]), self.project_dir(pid)
            if (sd / "inputs").is_dir():
                shutil.copytree(sd / "inputs", nd / "inputs", dirs_exist_ok=True)
            if (sd / "study").is_dir():
                shutil.copytree(sd / "study", nd / "study", dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns("ejecuciones_meta.jsonl"))
            # la detección interna se recalcula al lanzar; aquí solo se arrastra la configuración pública
            keep = {k: src.get(k) for k in ("marca", "sector", "origen_datos", "revision")}
            self.update(new["id"], **keep)
            return self.require(new["id"])

    def list(self, estado: str | None = None, q: str | None = None, archivados: bool = False) -> list[dict[str, Any]]:
        out = []
        for d in sorted(self.root.iterdir()) if self.root.is_dir() else []:
            if not d.is_dir() or not (d / "project.json").exists():
                continue
            data = read_json(d / "project.json")
            if not data:
                continue
            if bool(data.get("archivado")) and not archivados:
                continue
            if estado and data.get("estado") != estado:
                continue
            if q:
                needle = q.strip().lower()
                if needle not in (data.get("nombre") or "").lower() and needle not in (data.get("marca") or "").lower():
                    continue
            out.append(data)
        out.sort(key=lambda p: p.get("actualizado", ""), reverse=True)
        return out

    # ---------- estado interno del motor ----------
    def state_path(self, pid: str) -> Path:
        return self.run_dir(pid) / "state.json"

    def read_state(self, pid: str) -> dict[str, Any]:
        return read_json(self.state_path(pid), {}) or {}

    def patch_state(self, pid: str, **fields: Any) -> dict[str, Any]:
        """Añade claves propias (p. ej. `modo_referencia`) a `state.json` sin tocar las del motor.

        Solo se llama con el trabajo parado: el motor reescribe el archivo entero mientras corre.
        """
        with self.lock(pid):
            st = self.read_state(pid)
            if not st:
                st = initial_state(pid)
            st.update(fields)
            atomic_write_json(self.state_path(pid), st)
            return st

    # ---------- vista pública ----------
    def view(self, pid: str) -> dict[str, Any]:
        """`Project` del contrato, con puntos de control y punto pendiente derivados de `state.json`."""
        data = self.require(pid)
        st = self.read_state(pid)
        cps = st.get("checkpoints", {}) if st else {}
        data["checkpoints"] = {key: bool(cps.get(name, False)) for _, (name, _, key) in CHECKPOINTS.items()}
        pend = None
        if data.get("estado") == "esperando_revision":
            for step, status in (st.get("steps", {}) or {}).items():
                if status == "awaiting_human" and step in STEP_TO_CHECKPOINT:
                    pend = STEP_TO_CHECKPOINT[step]
                    break
        data["punto_control_pendiente"] = pend
        return {k: data.get(k) for k in PUBLIC_FIELDS}


def initial_state(pid: str) -> dict[str, Any]:
    """Estado inicial con la misma forma que `Run._load_or_init_state` (el motor lo completa con `setdefault`)."""
    steps = ("intake", "market", "detect", "judge", "metrics", "findings", "plan", "review", "write", "export")
    return {
        "run_id": "run",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "modo": "cliente",
        "provider": "mock",
        "brief_path": "",
        "marca_prospecto": None,
        "models": {},
        "degradados": {},
        "steps": {s: "pending" for s in steps},
        "checkpoints": {name: False for name, _, _ in CHECKPOINTS.values()},
        "human_approvals": [],
    }
