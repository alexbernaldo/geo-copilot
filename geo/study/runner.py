"""WC3 · Runner del estudio en vivo (B2.3): consultas a los motores, estimación y salida en formato del kit."""

from __future__ import annotations

import json
import math
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal

import pandas as pd
from pydantic import BaseModel, Field

from geo import llm as _llm
from geo import openrouter as _openrouter
from geo import reference as _reference
from geo import settings as _settings
from geo.engines import openrouter_engine as _engine
from geo.schemas import FichaMarca, Prompt
from geo.study.common import (
    EJECUCIONES_COLUMNS,
    MOTORES,
    active_provider,
    extract_domain,
    setting_int,
    track_usage,
    write_csv,
)
from geo.study.prompt_bank import PromptInstanciado, instantiate

PASO = "consultas"
MAX_FAIL_RATIO = 0.20

# Tokens medios por llamada con búsqueda web (los resultados de la búsqueda se suman a la entrada).
TOKENS_IN_PER_CALL = 1800
TOKENS_OUT_PER_CALL = 800
TOKENS_IN_PER_CALL_NATIVE = 200  # Perplexity ya integra la búsqueda
# Coste de la búsqueda web por llamada (USD), orden de magnitud 0,005-0,012 $ según el motor.
WEB_SEARCH_USD: dict[str, float] = {"ChatGPT": 0.010, "Gemini": 0.012, "Claude": 0.010, "Perplexity": 0.005}
LATENCY_S_PER_CALL = 25.0
DOMINIOS_NUEVOS_ESTIMADOS = 60
DOMINIOS_POR_LOTE = 30
DEFAULT_PRICE_IN_PER_M = 0.25
DEFAULT_PRICE_OUT_PER_M = 1.25


# ---------------------------------------------------------------- configuración y estimación


class StudyConfig(BaseModel):
    """Tamaño del estudio (mismo contrato que StudyConfig de la API)."""

    tamano: Literal["rapido", "estandar", "completo"] = "estandar"
    motores: list[Literal["ChatGPT", "Gemini", "Perplexity", "Claude"]] = Field(default_factory=lambda: list(MOTORES))  # type: ignore[arg-type]
    repeticiones: int = 2


def preset(tamano: str) -> StudyConfig:
    """«Rápido»: solo P1, 4 motores, 2 repeticiones. «Estándar»: todo, 4, 2. «Completo»: todo, 4, 3."""
    reps = 3 if tamano == "completo" else 2
    return StudyConfig(tamano=tamano, motores=list(MOTORES), repeticiones=reps)  # type: ignore[arg-type]


def select_instances(instances: list[PromptInstanciado], config: StudyConfig) -> list[PromptInstanciado]:
    if config.tamano == "rapido":
        return [i for i in instances if i.prioridad == "P1"]
    return list(instances)


def count_calls(instances: list[PromptInstanciado], config: StudyConfig) -> int:
    return len(select_instances(instances, config)) * len(config.motores) * max(1, config.repeticiones)


class EstimateStep(BaseModel):
    id: str
    nombre: str
    llamadas: int
    tokens_in: int = 0
    tokens_out: int = 0
    eur: float


class Estimate(BaseModel):
    pasos: list[EstimateStep]
    total_llamadas: int
    total_eur: float
    minutos: float
    supera_tope: bool
    tope_eur: float


def _price_per_token(model: str) -> tuple[float, float]:
    try:
        p = _openrouter.model_price(model)
    except Exception:
        p = None
    if p is None:
        return DEFAULT_PRICE_IN_PER_M / 1e6, DEFAULT_PRICE_OUT_PER_M / 1e6
    return p


def estimate_study(
    bank: list[Prompt],
    marcas: list[Any],
    ficha: FichaMarca,
    config: StudyConfig,
    *,
    dominios_nuevos: int | None = None,
) -> Estimate:
    """Estima llamadas, tokens, coste en € (precios del catálogo de OpenRouter + búsqueda web) y minutos."""
    insts = select_instances(instantiate(bank, marcas, ficha), config)
    reps = max(1, config.repeticiones)
    usd_eur = _settings.get_float("USD_EUR")
    total_consultas = 0
    tok_in_total = tok_out_total = 0
    eur_consultas = 0.0
    for motor in config.motores:
        n = len(insts) * reps
        tin = TOKENS_IN_PER_CALL_NATIVE if motor == "Perplexity" else TOKENS_IN_PER_CALL
        pin, pout = _price_per_token(_engine.engine_model(motor))
        eur_consultas += n * ((tin * pin + TOKENS_OUT_PER_CALL * pout) + WEB_SEARCH_USD[motor]) * usd_eur
        total_consultas += n
        tok_in_total += n * tin
        tok_out_total += n * TOKENS_OUT_PER_CALL

    nd = DOMINIOS_NUEVOS_ESTIMADOS if dominios_nuevos is None else dominios_nuevos
    lotes = math.ceil(nd / DOMINIOS_POR_LOTE) if nd > 0 else 0
    modelo_cls = _settings.get("LLM_MODEL").strip() or "mock"
    pin, pout = _price_per_token(modelo_cls)
    eur_fuentes = lotes * (900 * pin + 700 * pout) * usd_eur

    pasos = [
        EstimateStep(
            id="consultas",
            nombre="Consultas a los motores de IA",
            llamadas=total_consultas,
            tokens_in=tok_in_total,
            tokens_out=tok_out_total,
            eur=round(eur_consultas, 4),
        ),
        EstimateStep(
            id="fuentes",
            nombre="Clasificación de fuentes",
            llamadas=lotes,
            tokens_in=lotes * 900,
            tokens_out=lotes * 700,
            eur=round(eur_fuentes, 4),
        ),
    ]
    total_eur = round(sum(p.eur for p in pasos), 4)
    conc = max(1, setting_int("LLM_CONCURRENCY", 8))
    minutos = round(total_consultas / conc * LATENCY_S_PER_CALL / 60.0 + lotes * 10 / 60.0, 1)
    tope = _settings.get_float("MAX_BUDGET_EUR")
    return Estimate(
        pasos=pasos,
        total_llamadas=total_consultas + lotes,
        total_eur=total_eur,
        minutos=minutos,
        supera_tope=bool(tope > 0 and total_eur > tope),
        tope_eur=tope,
    )


# ---------------------------------------------------------------- errores y resultado


class StudyCancelled(RuntimeError):
    """El consultor canceló el estudio; las respuestas ya pagadas quedan en la caché."""


class StudyFailedError(RuntimeError):
    """Fallaron más del 20 % de las llamadas."""

    def __init__(self, message: str, fallos: list[dict[str, Any]]):
        super().__init__(message)
        self.fallos = fallos


@dataclass
class StudyRunResult:
    filas: int
    total: int
    llamadas_reales: int
    cache_hits: int
    coste_eur: float
    coste_real: bool
    tokens_in: int
    tokens_out: int
    ejecuciones_csv: Path
    meta_jsonl: Path | None
    fallos: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------- ejecución


def _tracked() -> tuple[int, float]:
    tr = _llm._TRACKER
    with tr.lock:
        return tr.calls, tr.cost_eur


def run_study(
    bank: list[Prompt],
    marcas: list[Any],
    ficha: FichaMarca,
    config: StudyConfig,
    study_dir: Path,
    *,
    on_progress: Callable[[str, int, int], None] | None = None,
    cancel: threading.Event | Callable[[], bool] | None = None,
    reference: bool | None = None,
    brief_text: str | None = None,
    provider: str | None = None,
    use_cache: bool = True,
    cache_dir: Path | None = None,
    max_budget_eur: float | None = None,
    concurrency: int | None = None,
    call_retries: int = 1,
    now: Callable[[], datetime] = datetime.now,
) -> StudyRunResult:
    """Ejecuta prompts instanciados × motores × repeticiones y escribe `study/ejecuciones.csv` (+ `ejecuciones_meta.jsonl`).

    - `on_progress(paso, hechos, total)` se llama desde el hilo que invoca, una vez por llamada terminada.
    - `cancel`: `threading.Event` o función; al activarse no se lanzan más llamadas y se lanza `StudyCancelled`.
    - Tope de gasto (`MAX_BUDGET_EUR`) y de llamadas (`MAX_LLM_CALLS`): se comprueban antes de cada llamada y,
      si se superan, se lanza `geo.llm.LLMCallLimitError`. La caché evita pagar dos veces al reanudar.
    - Una llamada fallida se reintenta una vez; si sigue fallando se registra y se excluye. Si fallan más del
      20 % se lanza `StudyFailedError`. Un error no recuperable (clave, saldo, modelo) lanza `geo.llm.LLMConfigError`.
    - Modo de referencia: copia `ejecuciones.csv` del kit; sin red ni coste.
    """
    study_dir = Path(study_dir)
    study_dir.mkdir(parents=True, exist_ok=True)

    if reference is None:
        reference, _ = _reference.detect_reference(
            brief_text=brief_text,
            csv_paths=None,
            prospect_brand=ficha.marca,
            prospect_domain=extract_domain(ficha.web) if ficha.web else None,
        )
    if reference:
        return _run_reference(study_dir, on_progress)

    insts = select_instances(instantiate(bank, marcas, ficha), config)
    reps = max(1, config.repeticiones)
    tareas: list[tuple[int, str, PromptInstanciado, str, int]] = []
    n = 0
    for inst in insts:
        for motor in config.motores:
            for rep in range(1, reps + 1):
                n += 1
                tareas.append((n, f"EJ-{n:04d}", inst, motor, rep))
    total = len(tareas)
    prov = active_provider(provider)
    is_mock = prov == "mock"
    budget = _settings.get_float("MAX_BUDGET_EUR") if max_budget_eur is None else max_budget_eur
    max_calls = _settings.get_int("MAX_LLM_CALLS") or 0
    workers = max(1, concurrency or setting_int("LLM_CONCURRENCY", 8))

    stop = threading.Event()
    lock = threading.Lock()
    estado: dict[str, Any] = {"reales": 0, "cache": 0, "eur": 0.0, "real_cost": False, "tin": 0, "tout": 0, "fatal": None, "limite": None}

    def _cancelled() -> bool:
        if cancel is None:
            return False
        return bool(cancel.is_set()) if isinstance(cancel, threading.Event) else bool(cancel())

    def _limit_reached() -> str | None:
        calls, cost = _tracked()
        if not is_mock and budget > 0 and cost >= budget:
            return f"Se alcanzó el tope de gasto del proyecto ({budget:g} €)."
        if not is_mock and max_calls > 0 and calls >= max_calls:
            return f"Se alcanzó el tope de llamadas ({max_calls})."
        return None

    def _tarea(t: tuple[int, str, PromptInstanciado, str, int]) -> dict[str, Any] | None:
        idx, eid, inst, motor, rep = t
        if stop.is_set() or _cancelled():
            stop.set()
            return None
        if not is_mock:
            with lock:
                msg = _limit_reached()
                if msg:
                    estado["limite"] = msg
                    stop.set()
                    return None
        ultimo: Exception | None = None
        for _ in range(2):  # llamada + un reintento
            try:
                if is_mock:
                    res = _engine.mock_run(motor, inst.prompt, rep, inst.marcas_a_evaluar)
                else:
                    res = _engine.run(
                        motor,
                        inst.prompt,
                        rep,
                        use_cache=use_cache,
                        cache_dir=cache_dir,
                        retries=call_retries,
                    )
                ultimo = None
                break
            except _openrouter.OpenRouterError as exc:
                ultimo = exc
                if not getattr(exc, "retryable", False):
                    with lock:
                        estado["fatal"] = _llm.LLMConfigError(str(exc))
                    stop.set()
                    return {"idx": idx, "error": str(exc), "eid": eid, "motor": motor, "fatal": True}
            except Exception as exc:  # noqa: BLE001 - cualquier fallo de una llamada se registra y se excluye
                ultimo = exc
        if ultimo is not None:
            return {"idx": idx, "error": str(ultimo), "eid": eid, "motor": motor}
        eur = 0.0
        if not res.cached and not res.simulado:
            eur = track_usage(res.model, res.tokens_in, res.tokens_out, res.cost_usd, "engine")
        with lock:
            if res.cached:
                estado["cache"] += 1
            elif not res.simulado:
                estado["reales"] += 1
            estado["eur"] += eur
            estado["tin"] += res.tokens_in
            estado["tout"] += res.tokens_out
            if res.cost_usd is not None and not res.cached and not res.simulado:
                estado["real_cost"] = True
        return {
            "idx": idx,
            "eid": eid,
            "inst": inst,
            "motor": motor,
            "rep": rep,
            "res": res,
            "fecha": now().strftime("%Y-%m-%d %H:%M"),
        }

    resultados: list[dict[str, Any]] = []
    fallos: list[dict[str, Any]] = []
    hechos = 0
    if on_progress:
        on_progress(PASO, 0, total)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_tarea, t) for t in tareas]
        for fut in as_completed(futs):
            out = fut.result()
            if out is None:
                continue
            hechos += 1
            if "error" in out:
                fallos.append({"ejecucion_id": out["eid"], "motor": out["motor"], "error": out["error"]})
                if len(fallos) > MAX_FAIL_RATIO * total:
                    stop.set()
            else:
                resultados.append(out)
            if on_progress:
                on_progress(PASO, hechos, total)

    if estado["fatal"] is not None:
        raise estado["fatal"]
    if _cancelled():
        raise StudyCancelled("Estudio cancelado por el usuario.")
    if estado["limite"]:
        raise _llm.LLMCallLimitError(estado["limite"])
    if len(fallos) > MAX_FAIL_RATIO * total:
        raise StudyFailedError(
            f"Fallaron {len(fallos)} de {total} llamadas ({100 * len(fallos) / max(1, total):.0f} %), "
            "más del 20 % permitido. Revisa la conexión y los modelos en Ajustes.",
            fallos,
        )

    resultados.sort(key=lambda r: r["idx"])
    sector = ficha.sector
    rows = [
        {
            "Ejecucion_ID": r["eid"],
            "Sector": sector,
            "Prompt_ID": r["inst"].prompt_id,
            "Familia": r["inst"].familia,
            "Intención": r["inst"].intencion,
            "Prompt ejecutado": r["inst"].prompt,
            "Motor": r["motor"],
            "Repetición": r["rep"],
            "Marcas a evaluar": " | ".join(r["inst"].marcas_a_evaluar),
            "Respuesta completa": r["res"].texto.strip(),
            "Fuentes citadas": ", ".join(r["res"].dominios),
            "Fecha/hora": r["fecha"],
        }
        for r in resultados
    ]
    csv_path = study_dir / "ejecuciones.csv"
    write_csv(pd.DataFrame(rows, columns=EJECUCIONES_COLUMNS), csv_path)

    usd_eur = _settings.get_float("USD_EUR")
    meta_path = study_dir / "ejecuciones_meta.jsonl"
    with meta_path.open("w", encoding="utf-8") as fh:
        for r in resultados:
            res = r["res"]
            fh.write(
                json.dumps(
                    {
                        "ejecucion_id": r["eid"],
                        "motor": r["motor"],
                        "modelo": res.model,
                        "tokens_in": res.tokens_in,
                        "tokens_out": res.tokens_out,
                        "coste_usd": res.cost_usd,
                        "coste_eur": None if res.cost_usd is None else round(res.cost_usd * usd_eur, 6),
                        "cache": res.cached,
                        "simulado": res.simulado,
                        "urls": res.urls,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return StudyRunResult(
        filas=len(rows),
        total=total,
        llamadas_reales=estado["reales"],
        cache_hits=estado["cache"],
        coste_eur=round(estado["eur"], 6),
        coste_real=bool(estado["real_cost"]),
        tokens_in=estado["tin"],
        tokens_out=estado["tout"],
        ejecuciones_csv=csv_path,
        meta_jsonl=meta_path,
        fallos=fallos,
    )


def _run_reference(study_dir: Path, on_progress: Callable[[str, int, int], None] | None) -> StudyRunResult:
    """Modo de referencia: copia `ejecuciones.csv` del kit. Instantáneo, sin red y sin coste."""
    dst = study_dir / "ejecuciones.csv"
    shutil.copyfile(_reference.REFERENCE_DIR / "ejecuciones.csv", dst)
    filas = len(pd.read_csv(dst, encoding="utf-8-sig", dtype=str))
    if on_progress:
        on_progress(PASO, filas, filas)
    return StudyRunResult(
        filas=filas,
        total=filas,
        llamadas_reales=0,
        cache_hits=0,
        coste_eur=0.0,
        coste_real=False,
        tokens_in=0,
        tokens_out=0,
        ejecuciones_csv=dst,
        meta_jsonl=None,
    )
