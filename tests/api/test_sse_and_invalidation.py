"""Tests de SSE, invalidación y protección contra llamadas a red en GET."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient


def test_invalidation_and_recompute(
    client: TestClient,
    kit_brief_text: str,
    kit_csvs: dict[str, Path],
) -> None:
    # 1. Crear y completar proyecto
    res = client.post("/api/projects", json={"nombre": "Inval Test", "tipo": "cliente"})
    pid = res.json()["id"]
    client.patch(f"/api/projects/{pid}", json={"revision": "continuo"})
    client.post(f"/api/projects/{pid}/brief", json={"texto": kit_brief_text})
    files = [("archivos", (name, path.read_bytes(), "text/csv")) for name, path in kit_csvs.items()]
    client.post(f"/api/projects/{pid}/study/upload", files=files)
    client.post(f"/api/projects/{pid}/run", json={"confirmo_coste": True})

    # Esperar a completado
    import time
    for _ in range(60):
        if client.get(f"/api/projects/{pid}/progress").json()["estado"] == "completado":
            break
        time.sleep(0.2)

    # 2. Consultar invalidación para cambio de ficha
    res = client.get(f"/api/projects/{pid}/invalidation?cambio=ficha")
    assert res.status_code == 200
    data = res.json()
    assert "pasos" in data
    assert "market" in data["pasos"]
    assert "estimacion" in data

    # 3. Lanzar recompute desde 'plan'
    res = client.post(f"/api/projects/{pid}/recompute", json={"desde_paso": "plan", "confirmo_coste": True})
    assert res.status_code == 202
    assert res.json()["estado"] == "en_ejecucion"


def test_no_openrouter_call_on_get(
    client: TestClient,
    kit_brief_text: str,
    kit_csvs: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica que ningún GET realice llamadas de red a OpenRouter."""
    res = client.post("/api/projects", json={"nombre": "No Net Test", "tipo": "cliente"})
    pid = res.json()["id"]
    client.patch(f"/api/projects/{pid}", json={"revision": "continuo"})
    client.post(f"/api/projects/{pid}/brief", json={"texto": kit_brief_text})
    files = [("archivos", (name, path.read_bytes(), "text/csv")) for name, path in kit_csvs.items()]
    client.post(f"/api/projects/{pid}/study/upload", files=files)
    client.post(f"/api/projects/{pid}/run", json={"confirmo_coste": True})

    import time
    for _ in range(60):
        if client.get(f"/api/projects/{pid}/progress").json()["estado"] == "completado":
            break
        time.sleep(0.2)

    import geo.openrouter as orc

    def _fail(*args, **kwargs):
        raise AssertionError("Se intentó llamar a OpenRouter en un método GET!")

    monkeypatch.setattr(orc, "chat", _fail)

    # Rutas GET
    endpoints = [
        f"/api/projects/{pid}",
        f"/api/projects/{pid}/progress",
        f"/api/projects/{pid}/diagnosis",
        f"/api/projects/{pid}/market",
        f"/api/projects/{pid}/findings",
        f"/api/projects/{pid}/plan",
        f"/api/projects/{pid}/proposal",
        f"/api/projects/{pid}/quality",
        f"/api/projects/{pid}/traces",
        "/api/settings",
        "/api/settings/models",
    ]
    for ep in endpoints:
        r = client.get(ep)
        assert r.status_code == 200


def test_sse_snapshot(client: TestClient) -> None:
    res = client.post("/api/projects", json={"nombre": "SSE Test", "tipo": "cliente"})
    pid = res.json()["id"]

    # Conectar a SSE y leer primer evento (snapshot)
    with client.stream("GET", f"/api/projects/{pid}/events") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("event:"):
                assert "snapshot" in line
                break
