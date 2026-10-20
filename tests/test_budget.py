"""Tests de validación de plan y presupuesto (F9)."""

import math

from geo.budget import effort_impact_matrix, has_dependency_cycles
from geo.config import ACTION_LIBRARY, BRIEF_MD
from geo.detection import detect
from geo.findings import generate_findings
from geo.intake import load_brief
from geo.judge_rules import judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas
from geo.metrics import bundle
from geo.strategy import _allowed_metric_values, build_plan


def test_action_library_has_at_least_20_templates() -> None:
    """Comprueba que ACTION_LIBRARY tiene al menos 20 plantillas completas."""
    assert len(ACTION_LIBRARY) >= 20
    required_keys = {
        "template_id",
        "titulo",
        "descripcion",
        "palanca",
        "tipos_hallazgo",
        "fase_embudo",
        "esfuerzo",
        "impacto",
        "responsable",
        "coste_rango_eur",
        "horas_cliente_semana",
        "plazo_semanas",
        "fase_plan",
        "dependencias_tpl",
        "kpi_tipo",
        "entregables_tipo",
    }
    for tpl in ACTION_LIBRARY:
        assert required_keys.issubset(set(tpl.keys()))


def test_build_plan_and_budget_constraints_f9() -> None:
    """Comprueba F9: coste <= 27000 €, hallazgos válidos, KPI, responsable, entregables, sin ciclos y valor_actual real."""
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    catalogo = load_fuentes()
    df_det = detect(df_ej, marcas)
    evals = judge_rules(df_det, df_ej, marcas, catalogo)
    tablas = bundle(evals, df_ej, marcas)
    ficha, _ = load_brief(BRIEF_MD, provider="mock")
    hallazgos = generate_findings(tablas, ficha=ficha)

    plan = build_plan(ficha, hallazgos, tablas, provider="mock")

    # Presupuesto dentro del rango del brief (18.000 - 27.000 €)
    assert 18000.0 <= plan.coste_total_eur <= 27000.0
    assert math.isclose(
        plan.coste_total_eur,
        sum(a.coste_estimado_eur for a in plan.acciones),
        abs_tol=1e-2,
    )

    valid_h_ids = {h.id for h in hallazgos}
    action_by_id = {a.id: a for a in plan.acciones}
    assert 10 <= len(plan.acciones) <= 16

    for a in plan.acciones:
        assert len(a.hallazgos_relacionados) >= 1
        assert set(a.hallazgos_relacionados).issubset(valid_h_ids)
        assert a.kpi.strip() != ""
        assert a.responsable != ""
        assert len(a.entregables) >= 1
        assert a.plazo_semanas >= 1
        assert 1 <= a.semana_inicio <= 52
        for dep_id in a.dependencias:
            dep_act = action_by_id[dep_id]
            assert a.semana_inicio >= dep_act.semana_inicio + dep_act.plazo_semanas

    assert has_dependency_cycles(plan.acciones) is False

    # Comprobar que los valor_actual de los objetivos coinciden con las métricas reales
    allowed_vals = _allowed_metric_values(hallazgos, tablas, ficha.marca)
    assert 3 <= len(plan.objetivos) <= 5
    for obj in plan.objetivos:
        assert any(
            math.isclose(obj.valor_actual, v, abs_tol=1e-2) for v in allowed_vals
        ), f"valor_actual {obj.valor_actual} de '{obj.kpi}' no coincide con las métricas"
        assert obj.valor_objetivo_max > obj.valor_objetivo_min

    # Matriz esfuerzo / impacto
    df_mat = effort_impact_matrix(plan)
    assert len(df_mat) == len(plan.acciones)
