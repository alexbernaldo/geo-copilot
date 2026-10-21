"""Router `settings` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.get("/settings", summary='Ajustes (la clave nunca se devuelve)')
def get_settings() -> None:
    not_implemented()


@router.put("/settings", summary='Guarda ajustes')
def put_settings() -> None:
    not_implemented()


@router.post("/settings/test", summary='Prueba la conexión con OpenRouter')
def post_settings_test() -> None:
    not_implemented()


@router.get("/settings/models", summary='Catálogo de OpenRouter (caché 1 h)')
def get_settings_models() -> None:
    not_implemented()
