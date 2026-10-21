"""Tests del simulador what-if del Score de Citación (F14)."""

import pandas as pd

from geo.config import RUNS_DIR
from geo.reference import REFERENCE_DIR
from geo.schemas import Plan
from geo.simulate import (
    DISCLAIMER_SIMULADOR,
    apply_simulation_to_plan_objectives,
    get_brand_baseline_params,
    simulate,
)


def test_simulate_no_changes_equals_actual() -> None:
    """Sin cambios (o con los valores base actuales), el score simulado y el puesto coinciden exactamente con el actual."""
    evals = pd.read_parquet(RUNS_DIR / "demo" / "evaluaciones.parquet")
    marca = "Clínica Alborada Visión"

    res_none = simulate(evals, marca, cambios=None, study_dir=REFERENCE_DIR)
    assert res_none["score_simulado"] == res_none["score_actual"] == 27.97
    assert res_none["puesto_simulado"] == res_none["puesto_actual"] == 7
    assert res_none["delta_score"] == 0.0
    assert res_none["delta_puesto"] == 0
    assert res_none["componentes"]["simulado"] == res_none["componentes"]["actual"]
    assert res_none["aviso"] == DISCLAIMER_SIMULADOR

    base = get_brand_baseline_params(evals, marca, study_dir=REFERENCE_DIR)
    res_same = simulate(
        evals,
        marca,
        cambios={
            "aparicion_por_ciudad": base["aparicion_por_ciudad"],
            "aparicion_por_motor": base["aparicion_por_motor"],
            "fuerza_media_objetivo": base["fuerza_presentes"],
            "pct_fuentes_calidad": base["pct_fuentes_calidad"],
        },
        study_dir=REFERENCE_DIR,
    )
    assert res_same["score_simulado"] == res_same["score_actual"]
    assert res_same["puesto_simulado"] == res_same["puesto_actual"]


def test_simulate_improvements_increase_score_and_rank() -> None:
    """Al mejorar la aparición en Barcelona y motores rezagados, la fuerza y la calidad de fuente, sube el score y el puesto."""
    evals = pd.read_parquet(RUNS_DIR / "demo" / "evaluaciones.parquet")
    marca = "Clínica Alborada Visión"

    res = simulate(
        evals,
        marca,
        cambios={
            "aparicion_por_ciudad": {"Barcelona": 0.50, "Madrid": 0.65},
            "aparicion_por_motor": {"ChatGPT": 0.45, "Claude": 0.40},
            "fuerza_media_objetivo": 2.30,
            "pct_fuentes_calidad": 0.65,
        },
        study_dir=REFERENCE_DIR,
    )
    assert res["score_simulado"] > res["score_actual"]
    assert res["puesto_simulado"] < res["puesto_actual"]
    assert res["componentes"]["simulado"]["aparicion"] > res["componentes"]["actual"]["aparicion"]
    assert res["componentes"]["simulado"]["fuerza"] > res["componentes"]["actual"]["fuerza"]
    assert res["componentes"]["simulado"]["fuente"] > res["componentes"]["actual"]["fuente"]


def test_apply_simulation_to_plan_objectives() -> None:
    """El botón 'Usar como objetivo' vuelca el escenario simulado a plan.objetivos con el aviso hipotético."""
    evals = pd.read_parquet(RUNS_DIR / "demo" / "evaluaciones.parquet")
    plan = Plan.model_validate_json((RUNS_DIR / "demo" / "plan.json").read_text(encoding="utf-8"))
    sim_res = simulate(
        evals,
        "Clínica Alborada Visión",
        cambios={"aparicion_por_ciudad": {"Barcelona": 0.45}, "fuerza_media_objetivo": 2.1},
        study_dir=REFERENCE_DIR,
    )
    updated_plan = apply_simulation_to_plan_objectives(plan, sim_res)
    assert len(updated_plan.objetivos) == len(plan.objetivos) + 1
    last_obj = updated_plan.objetivos[-1]
    assert "escenario hipotético, no una predicción" in last_obj.kpi.lower()
    assert last_obj.valor_objetivo_max == sim_res["score_simulado"]
