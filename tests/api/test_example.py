"""Proyecto de ejemplo de Clínica Alborada Visión, creado al arrancar el backend."""

import time

import pytest
from fastapi.testclient import TestClient

import backend.deps as deps
from backend.main import app
from backend.services.example import NOMBRE_EJEMPLO, ensure_example, example_id


def _esperar(pid: str, timeout: float = 30.0) -> dict:
    store, runner = deps.get_store(), deps.get_runner()
    inicio = time.monotonic()
    while time.monotonic() - inicio < timeout:
        if not runner.running_pid():
            p = store.view(pid)
            if p["estado"] not in ("listo_para_lanzar", "en_ejecucion"):
                return p
        time.sleep(0.2)
    raise TimeoutError(pid)


def test_el_ejemplo_se_crea_completado_y_sin_coste() -> None:
    pid = ensure_example(deps.get_store(), deps.get_runner())
    assert pid
    p = _esperar(pid)
    assert p["nombre"] == NOMBRE_EJEMPLO
    assert p["marca"] == "Clínica Alborada Visión"
    assert p["estado"] == "completado"
    assert p["checkpoints"] == {"ficha": True, "competencia": True, "hallazgos": True, "plan": True}
    assert p["coste_eur"] == 0.0


def test_no_se_duplica_y_vuelve_si_se_borra() -> None:
    store, runner = deps.get_store(), deps.get_runner()
    pid = ensure_example(store, runner)
    _esperar(pid)
    assert ensure_example(store, runner) == pid
    assert len(store.list()) == 1

    store.delete(pid)
    assert example_id(store) is None
    nuevo = ensure_example(store, runner)
    assert nuevo and nuevo != pid
    _esperar(nuevo)
    assert len(store.list()) == 1


def test_se_puede_desactivar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_EJEMPLO", "0")
    assert ensure_example(deps.get_store(), deps.get_runner()) is None
    assert deps.get_store().list() == []


def test_la_app_lo_prepara_al_arrancar() -> None:
    with TestClient(app) as client:
        pid = example_id(deps.get_store())
        assert pid
        _esperar(pid)
        nombres = [p["nombre"] for p in client.get("/api/projects").json()]
        assert nombres == [NOMBRE_EJEMPLO]
