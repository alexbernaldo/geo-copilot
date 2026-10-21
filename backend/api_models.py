"""Modelos Pydantic de petición/respuesta de la API (distintos de geo/schemas.py)."""

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: dict = {}


class ErrorResponse(BaseModel):
    error: ErrorBody


class Health(BaseModel):
    ok: bool
    version: str
