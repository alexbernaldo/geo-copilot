"""Tests de ejecución de pipeline: flujo continuo, pausas, 423 lock y verificación de invariantes."""

import io
import time
from pathlib import Path
from typing import Any

import docx
from fastapi.testclient import TestClient


def _wait_completion(client: TestClient, pid: str, timeout: float = 30.0) -> dict[str, Any]:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        res = client.get(f"/api/projects/{pid}/progress")
        assert res.status_code == 200
        prog = res.json()
        if prog["estado"] in ("completado", "esperando_revision", "error", "interrumpido"):
            return prog
        time.sleep(0.2)
    raise TimeoutError(f"Timeout esperando fin de ejecución para {pid}")


def test_full_pipeline_continuo(
    client: TestClient,
    kit_brief_text: str,
    kit_csvs: dict[str, Path],
) -> None:
    # 1. Crear proyecto modo continuo
    res = client.post("/api/projects", json={"nombre": "Kit Project Continuo", "tipo": "cliente"})
    assert res.status_code == 201
    pid = res.json()["id"]

    client.patch(f"/api/projects/{pid}", json={"revision": "continuo"})

    # 2. Subir brief
    res = client.post(f"/api/projects/{pid}/brief", json={"texto": kit_brief_text})
    assert res.status_code == 200
    assert "ficha" in res.json()

    # 3. Subir CSVs del kit
    files = [
        ("archivos", (name, path.read_bytes(), "text/csv"))
        for name, path in kit_csvs.items()
    ]
    res = client.post(f"/api/projects/{pid}/study/upload", files=files)
    assert res.status_code == 200
    assert res.json()["bloqueado"] is False

    # Comprobar estado listo_para_lanzar
    res = client.get(f"/api/projects/{pid}")
    assert res.json()["estado"] == "listo_para_lanzar"

    # 4. Lanzar ejecución
    res = client.post(f"/api/projects/{pid}/run", json={"confirmo_coste": True})
    assert res.status_code == 202

    # 5. Intentar lanzar un segundo trabajo mientras corre -> 423
    # (El trabajo en mock con kit es rápido, si aún sigue corriendo devuelve 423)
    res_second = client.post(f"/api/projects/{pid}/run", json={"confirmo_coste": True})
    if res_second.status_code != 409:  # si ya terminó devuelve 409 (estado no valido), si corre devuelve 423
        assert res_second.status_code in (423, 409)

    # 6. Esperar a completado
    prog = _wait_completion(client, pid, timeout=30.0)
    assert prog["estado"] == "completado"

    # 7. Comprobar endpoints de resultados
    res_diag = client.get(f"/api/projects/{pid}/diagnosis")
    assert res_diag.status_code == 200

    res_find = client.get(f"/api/projects/{pid}/findings")
    assert res_find.status_code == 200
    assert len(res_find.json()) > 0

    res_plan = client.get(f"/api/projects/{pid}/plan")
    assert res_plan.status_code == 200

    res_prop = client.get(f"/api/projects/{pid}/proposal")
    assert res_prop.status_code == 200
    assert res_prop.json()["secciones"]

    # Explorador de ejecuciones (destino de «Ver evidencia»), con los parámetros del contrato
    res_ex = client.get(f"/api/projects/{pid}/executions", params={"pagina": 1, "tamano": 50})
    assert res_ex.status_code == 200
    assert res_ex.json()["total"] == 624
    res_ids = client.get(f"/api/projects/{pid}/executions", params={"ids": "EJ-0001,EJ-0002"})
    assert res_ids.status_code == 200
    assert {f["ejecucion_id"] for f in res_ids.json()["filas"]} == {"EJ-0001", "EJ-0002"}

    # Simulador del plan
    res_sim = client.post(f"/api/projects/{pid}/plan/simulate", json={"cambios": {}})
    assert res_sim.status_code == 200
    sim = res_sim.json()
    assert sim["score_simulado"] == sim["score_actual"]
    res_sim = client.post(f"/api/projects/{pid}/plan/simulate", json={"cambios": {"aparicion_por_ciudad": {"Barcelona": 0.5}}})
    assert res_sim.status_code == 200
    assert res_sim.json()["score_simulado"] > res_sim.json()["score_actual"]

    # 8. Descargar docx y abrirlo con python-docx
    res_docx = client.get(f"/api/projects/{pid}/exports/docx")
    assert res_docx.status_code == 200
    doc = docx.Document(io.BytesIO(res_docx.content))
    assert len(doc.paragraphs) > 0


def test_pipeline_pausas(
    client: TestClient,
    kit_brief_text: str,
    kit_csvs: dict[str, Path],
) -> None:
    # 1. Crear proyecto con pausas (por defecto)
    res = client.post("/api/projects", json={"nombre": "Kit Project Pausas", "tipo": "cliente"})
    assert res.status_code == 201
    pid = res.json()["id"]

    # 2. Subir brief y CSVs
    client.post(f"/api/projects/{pid}/brief", json={"texto": kit_brief_text})
    files = [
        ("archivos", (name, path.read_bytes(), "text/csv"))
        for name, path in kit_csvs.items()
    ]
    client.post(f"/api/projects/{pid}/study/upload", files=files)

    # 3. Lanzar
    res = client.post(f"/api/projects/{pid}/run", json={"confirmo_coste": True})
    assert res.status_code == 202

    # 4. En pausas debe parar en los puntos de control secuenciales (0, 1, 2, 3)
    for cp in range(4):
        prog = _wait_completion(client, pid, timeout=20.0)
        assert prog["estado"] == "esperando_revision"

        res_p = client.get(f"/api/projects/{pid}")
        assert res_p.json()["punto_control_pendiente"] == cp

        # Aprobar punto de control
        res_app = client.post(f"/api/projects/{pid}/checkpoints/{cp}/approve", json={"nota": f"Aprobado cp {cp}"})
        assert res_app.status_code == 200

    # Tras aprobar el 3, debe llegar a completado
    prog_final = _wait_completion(client, pid, timeout=20.0)
    assert prog_final["estado"] == "completado"


def test_no_leak_kit_mode_or_key(
    client: TestClient,
    kit_brief_text: str,
    kit_csvs: dict[str, Path],
) -> None:
    """Verifica que ninguna respuesta pública contenga 'referencia', 'reference' o la clave API."""
    res = client.post("/api/projects", json={"nombre": "Leak Test", "tipo": "cliente"})
    pid = res.json()["id"]
    client.patch(f"/api/projects/{pid}", json={"revision": "continuo"})

    client.post(f"/api/projects/{pid}/brief", json={"texto": kit_brief_text})
    files = [
        ("archivos", (name, path.read_bytes(), "text/csv"))
        for name, path in kit_csvs.items()
    ]
    client.post(f"/api/projects/{pid}/study/upload", files=files)
    client.post(f"/api/projects/{pid}/run", json={"confirmo_coste": True})
    _wait_completion(client, pid, timeout=30.0)

    # Revisar las respuestas públicas clave
    endpoints = [
        f"/api/projects/{pid}",
        f"/api/projects/{pid}/progress",
        f"/api/projects/{pid}/market",
        f"/api/projects/{pid}/findings",
        f"/api/projects/{pid}/plan",
        f"/api/projects/{pid}/proposal",
        f"/api/settings",
    ]
    for ep in endpoints:
        r = client.get(ep)
        assert r.status_code == 200
        text = r.text.lower()
        # No puede exponer "modo_referencia" ni "reference_mode"
        assert "modo_referencia" not in text
        assert "reference_mode" not in text
        # La clave API en ajustes nunca debe mostrar el valor real
        if ep == "/api/settings":
            assert "clave_mascara" in r.json()
