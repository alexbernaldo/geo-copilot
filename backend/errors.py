"""Errores de la API con la forma `{"error": {"code", "message", "detail"}}` (los traduce `main.py`)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def api_error(status: int, code: str, message: str, detail: dict[str, Any] | None = None) -> HTTPException:
    """Construye una `HTTPException` con el cuerpo de error del contrato (mensaje siempre en español)."""
    return HTTPException(status_code=status, detail={"code": code, "message": message, "detail": detail or {}})


def not_found(what: str = "El proyecto") -> HTTPException:
    return api_error(404, "no_encontrado", f"{what} no existe.")


def conflict(code: str, message: str, detail: dict[str, Any] | None = None) -> HTTPException:
    return api_error(409, code, message, detail)


def unprocessable(code: str, message: str, detail: dict[str, Any] | None = None) -> HTTPException:
    return api_error(422, code, message, detail)


def locked(message: str = "Ya hay un análisis en ejecución. Espera a que termine o cancélalo.") -> HTTPException:
    return api_error(423, "trabajo_en_curso", message)
