"""Tests de CRUD de proyectos y operaciones básicas."""

from fastapi.testclient import TestClient


def test_crud_projects(client: TestClient) -> None:
    # 1. Crear proyecto
    res = client.post("/api/projects", json={"nombre": "Proyecto Test", "tipo": "cliente"})
    assert res.status_code == 201
    data = res.json()
    pid = data["id"]
    assert data["nombre"] == "Proyecto Test"
    assert data["tipo"] == "cliente"
    assert data["estado"] == "borrador"
    assert data["archivado"] is False

    # 2. Leer detalle
    res = client.get(f"/api/projects/{pid}")
    assert res.status_code == 200
    assert res.json()["id"] == pid

    # 3. Listar proyectos
    res = client.get("/api/projects")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert pid in ids

    # 4. Patch (renombrar y cambiar revisión)
    res = client.patch(f"/api/projects/{pid}", json={"nombre": "Proyecto Renombrado", "revision": "continuo"})
    assert res.status_code == 200
    data = res.json()
    assert data["nombre"] == "Proyecto Renombrado"
    assert data["revision"] == "continuo"

    # 5. Duplicar proyecto
    res = client.post(f"/api/projects/{pid}/duplicate")
    assert res.status_code == 201
    dup = res.json()
    dup_id = dup["id"]
    assert dup_id != pid
    assert "copia" in dup["nombre"]
    assert dup["revision"] == "continuo"

    # 6. Borrar con confirmación errónea -> 422
    res = client.delete(f"/api/projects/{pid}?confirm=nombre_incorrecto")
    assert res.status_code == 400

    # 7. Borrar con confirmación correcta -> 204
    res = client.delete(f"/api/projects/{pid}?confirm=Proyecto Renombrado")
    assert res.status_code == 204

    # 8. Comprobar que ya no existe -> 404
    res = client.get(f"/api/projects/{pid}")
    assert res.status_code == 404


def test_create_validation_error(client: TestClient) -> None:
    res = client.post("/api/projects", json={"nombre": "   ", "tipo": "cliente"})
    assert res.status_code == 422


def test_not_found(client: TestClient) -> None:
    res = client.get("/api/projects/p_inexistente")
    assert res.status_code == 404
