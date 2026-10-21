"""Router `settings`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from backend.api_models import Limits, ModelPrices, ModelRoles, Settings, SettingsTest, SettingsUpdate
from backend.deps import get_data_dir
from geo import openrouter as orc
from geo import settings as gs

router = APIRouter()


def _get_settings_payload() -> Settings:
    cur = gs.current()
    raw_key = cur.get("OPENROUTER_API_KEY", "")
    has_key = bool(raw_key.strip())
    masked = gs.mask(raw_key) if has_key else None
    
    roles = ModelRoles(
        juez=cur.get("LLM_MODEL"),
        redaccion=cur.get("LLM_MODEL_WRITER"),
        propuesta=cur.get("LLM_MODEL_PROPOSER"),
        chatgpt=cur.get("ENGINE_MODEL_CHATGPT"),
        gemini=cur.get("ENGINE_MODEL_GEMINI"),
        claude=cur.get("ENGINE_MODEL_CLAUDE"),
        perplexity=cur.get("ENGINE_MODEL_PERPLEXITY"),
    )
    
    limits = Limits(
        concurrencia=gs.get_int("LLM_CONCURRENCY"),
        max_llamadas=gs.get_int("MAX_LLM_CALLS"),
        tope_gasto_eur=gs.get_float("MAX_BUDGET_EUR"),
        usd_eur=gs.get_float("USD_EUR"),
    )
    
    data_dir = str(get_data_dir())
    
    return Settings(
        clave_configurada=has_key,
        clave_mascara=masked,
        modelos=roles,
        limites=limits,
        carpeta_datos=data_dir,
        modelos_inexistentes=[],
    )


@router.get("/settings", response_model=Settings, summary="Ajustes (la clave nunca se devuelve)")
def get_settings() -> Settings:
    return _get_settings_payload()


@router.put("/settings", response_model=Settings, summary="Guarda ajustes")
def put_settings(body: SettingsUpdate) -> Settings:
    to_save: dict[str, str] = {}
    if body.clave is not None:
        to_save["OPENROUTER_API_KEY"] = body.clave
    if body.modelos:
        m = body.modelos
        if m.juez:
            to_save["LLM_MODEL"] = m.juez
        if m.redaccion:
            to_save["LLM_MODEL_WRITER"] = m.redaccion
        if m.propuesta:
            to_save["LLM_MODEL_PROPOSER"] = m.propuesta
        if m.chatgpt:
            to_save["ENGINE_MODEL_CHATGPT"] = m.chatgpt
        if m.gemini:
            to_save["ENGINE_MODEL_GEMINI"] = m.gemini
        if m.claude:
            to_save["ENGINE_MODEL_CLAUDE"] = m.claude
        if m.perplexity:
            to_save["ENGINE_MODEL_PERPLEXITY"] = m.perplexity
    if body.limites:
        lim = body.limites
        to_save["LLM_CONCURRENCY"] = str(lim.concurrencia)
        to_save["MAX_LLM_CALLS"] = str(lim.max_llamadas)
        to_save["MAX_BUDGET_EUR"] = str(lim.tope_gasto_eur)
        to_save["USD_EUR"] = str(lim.usd_eur)
    
    if to_save:
        gs.save(to_save)
    return _get_settings_payload()


@router.post("/settings/test", response_model=SettingsTest, summary="Prueba la conexión con OpenRouter")
def post_settings_test() -> SettingsTest:
    model = gs.get("LLM_MODEL") or "google/gemini-2.5-flash"
    try:
        res = orc.test_connection(model)
        info = res.get("key_info") or {}
        coste_eur = res.get("coste_usd", 0.0) * gs.get_float("USD_EUR") if res.get("coste_usd") else 0.0
        return SettingsTest(
            ok=True,
            latencia_ms=res.get("latencia_ms"),
            coste_eur=round(coste_eur, 5),
            gasto_clave_usd=info.get("usage"),
            limite_clave_usd=info.get("limit"),
            mensaje="Conexión con OpenRouter correcta.",
        )
    except Exception as exc:
        return SettingsTest(
            ok=False,
            mensaje=f"Error al conectar con OpenRouter: {exc}",
        )


@router.get("/settings/models", response_model=list[ModelPrices], summary="Catálogo de OpenRouter (caché 1 h)")
def get_settings_models() -> list[ModelPrices]:
    try:
        raw_models = orc.list_models()
    except Exception:
        raw_models = orc.cached_models() or []
    
    out: list[ModelPrices] = []
    for m in raw_models:
        out.append(
            ModelPrices(
                id=m["id"],
                nombre=m.get("name"),
                precio_in_usd_m=m.get("price_in_per_m"),
                precio_out_usd_m=m.get("price_out_per_m"),
                contexto=m.get("context_length"),
            )
        )
    return out
