"""Routers de la API. En W0 todos devuelven 501 `no_implementado`."""

from fastapi import HTTPException


def not_implemented() -> None:
    raise HTTPException(status_code=501, detail={"code": "no_implementado", "message": "Esta ruta todavía no está implementada.", "detail": {}})
