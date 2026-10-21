"""Estimaciones de coste (nunca llaman a OpenRouter: precios solo del catálogo ya en caché)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geo import settings as gs
from geo.llm import estimate_cost_for_model

from backend.services import engine, inputs, study_files as sf
from backend.services.pipeline import ANALYSIS_STEPS, MOTORES, STEP_NAMES
from backend.services.store import ProjectStore

WEB_SEARCH_USD = 0.008          # coste orientativo de búsqueda web por consulta del estudio en vivo
STUDY_TOKENS_IN = 300
STUDY_TOKENS_OUT = 1100
SECONDS_PER_STUDY_CALL = 9.0


def effective_provider(store: ProjectStore, pid: str) -> str:
    """Proveedor con el que se ejecutaría el proyecto: `mock` en modo de referencia, el de Ajustes en los demás."""
    if inputs.is_reference(store, pid):
        return "mock"
    return (gs.get("LLM_PROVIDER") or "mock").strip().lower()


def _empty(tope: float) -> dict[str, Any]:
    return {"pasos": [], "total_llamadas": 0, "total_eur": 0.0, "minutos": 0.0, "supera_tope": False, "tope_eur": tope}


def _finish(pasos: list[dict[str, Any]], minutos: float) -> dict[str, Any]:
    tope = gs.get_float("MAX_BUDGET_EUR")
    total = round(sum(p["eur"] for p in pasos), 4)
    return {"pasos": pasos, "total_llamadas": int(sum(p["llamadas"] for p in pasos)), "total_eur": total,
            "minutos": round(minutos, 1), "supera_tope": total > tope, "tope_eur": tope}


def analysis_estimate(store: ProjectStore, pid: str, steps: list[str] | None = None) -> dict[str, Any]:
    """Estimación del análisis (`Run.estimate`) con los modelos configurados, sobre los datos del proyecto."""
    tope = gs.get_float("MAX_BUDGET_EUR")
    study = store.study_dir(pid)
    if not all(sf.study_file(study, k).exists() for k in sf.REQUIRED):
        return _empty(tope)
    p = store.require(pid)
    provider = effective_provider(store, pid)
    brief = store.inputs_dir(pid) / "brief.txt"
    try:
        with engine.engine_paths(study):
            run = engine.make_run(project_dir=store.project_dir(pid), study_dir=study, modo=p["tipo"], brief_path=brief,
                                  marca_prospecto=p.get("marca") if p["tipo"] == "prospecto" else None, provider=provider)
            run.state["models"] = {"juez_y_revisor": gs.get("LLM_MODEL"), "estrategia_y_redaccion": gs.get("LLM_MODEL_WRITER")}
            est = run.estimate()
    except Exception:
        return _empty(tope)
    pasos = []
    for sid in ANALYSIS_STEPS:
        e = est["pasos"].get(sid)
        if e is None or (steps is not None and sid not in steps):
            continue
        pasos.append({"id": sid, "nombre": STEP_NAMES[sid], "llamadas": int(e.get("llamadas", 0)), "tokens_in": int(e.get("tokens_in", 0)),
                      "tokens_out": int(e.get("tokens_out", 0)), "eur": round(float(e.get("eur", 0.0)), 4)})
    minutos = float(est.get("minutos", 0.0)) if steps is None else float(est.get("minutos", 0.0)) * len(pasos) / max(1, len(ANALYSIS_STEPS))
    return _finish(pasos, minutos)


def study_instances(store: ProjectStore, pid: str) -> list[dict[str, Any]]:
    """Prompts instanciados del estudio (`PromptInstance`). Con ejecuciones cargadas salen de ellas; si no, por código."""
    study = store.study_dir(pid)
    ej, ba = sf.study_file(study, "ejecuciones"), sf.study_file(study, "banco_prompts")
    bank = sf.read_prompts(study)
    ficha = inputs.current_ficha(store, pid)
    ciudades = list(ficha.ciudades) if ficha else []
    if ej.exists() and ba.exists():
        df = sf._canonical(sf.read_csv(ej), "ejecuciones")
        inst = {t["prompt_id"]: t["instanciacion"] for t in bank}
        out = []
        for _, r in df.drop_duplicates(["Prompt_ID", "Prompt ejecutado"]).iterrows():
            ciudad = next((c for c in ciudades if c.lower() in r["Prompt ejecutado"].lower()), None) if inst.get(r["Prompt_ID"]) == "ciudad" else None
            out.append({"prompt_id": r["Prompt_ID"], "prompt": r["Prompt ejecutado"], "instanciacion": inst.get(r["Prompt_ID"], ""),
                        "marcas_a_evaluar": [m.strip() for m in r["Marcas a evaluar"].split("|") if m.strip()], "ciudad": ciudad})
        return out
    marcas = sf.read_brands(study)
    marca_proyecto = ficha.marca if ficha else None
    return sf.instantiate(bank, marcas, ciudades, marca_proyecto)


def study_estimate(store: ProjectStore, pid: str) -> dict[str, Any]:
    """Estimación del estudio en vivo: prompts instanciados × motores × repeticiones."""
    tope = gs.get_float("MAX_BUDGET_EUR")
    study = store.study_dir(pid)
    cfg = sf.read_config(study)
    bank = sf.read_prompts(study)
    if cfg.get("tamano") == "rapido":
        keep = {t["prompt_id"] for t in bank if t.get("prioridad") == "P1"}
        instances = [i for i in study_instances(store, pid) if i["prompt_id"] in keep]
    else:
        instances = study_instances(store, pid)
    motores = [m for m in cfg.get("motores", MOTORES) if m in MOTORES]
    reps = int(cfg.get("repeticiones", 2))
    llamadas = len(instances) * len(motores) * reps
    if llamadas == 0:
        return _empty(tope)
    model_key = {"ChatGPT": "ENGINE_MODEL_CHATGPT", "Gemini": "ENGINE_MODEL_GEMINI", "Perplexity": "ENGINE_MODEL_PERPLEXITY", "Claude": "ENGINE_MODEL_CLAUDE"}
    eur = 0.0
    for m in motores:
        per_call = estimate_cost_for_model(gs.get(model_key[m]), STUDY_TOKENS_IN, STUDY_TOKENS_OUT) + WEB_SEARCH_USD * gs.get_float("USD_EUR")
        eur += per_call * len(instances) * reps
    pasos = [{"id": "queries", "nombre": STEP_NAMES["queries"], "llamadas": llamadas, "tokens_in": llamadas * STUDY_TOKENS_IN,
              "tokens_out": llamadas * STUDY_TOKENS_OUT, "eur": round(eur, 4)}]
    conc = max(1, gs.get_int("LLM_CONCURRENCY"))
    return _finish(pasos, llamadas / conc * SECONDS_PER_STUDY_CALL / 60.0)


def total_estimate(store: ProjectStore, pid: str, *, live: bool) -> dict[str, Any]:
    """Coste previsto de lanzar: estudio en vivo (si aplica) + análisis."""
    a = analysis_estimate(store, pid)
    if not live:
        return a
    s = study_estimate(store, pid)
    return _finish(s["pasos"] + a["pasos"], s["minutos"] + a["minutos"])
