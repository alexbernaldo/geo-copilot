"""Tests del verificador de cifras y guardia normativa (F10)."""

from geo.config import BRIEF_MD
from geo.detection import detect
from geo.findings import generate_findings
from geo.intake import load_brief
from geo.judge_rules import judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas
from geo.metrics import build_brand_summary_metrics, bundle
from geo.reviewer import compliance, verify_numbers
from geo.strategy import build_plan


def _sample_context() -> tuple[dict, object, object]:
    """Construye un contexto real de cifras (metrics + hallazgos + plan + ficha) para los tests de F10."""
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    catalogo = load_fuentes()
    df_det = detect(df_ej, marcas)
    evals = judge_rules(df_det, df_ej, marcas, catalogo)
    tablas = bundle(evals, df_ej, marcas)
    ficha, _ = load_brief(BRIEF_MD, provider="mock")
    hallazgos = generate_findings(tablas, ficha=ficha)
    plan = build_plan(ficha, hallazgos, tablas, provider="mock")
    metrics_summary = build_brand_summary_metrics(tablas, marca_brief=ficha.marca)
    ctx = {
        "metrics": metrics_summary,
        "hallazgos": hallazgos,
        "plan": plan,
        "ficha": ficha,
    }
    return ctx, plan, ficha


def test_verify_numbers_traceable_39_passes_and_invented_57_fails() -> None:
    """Un texto con '39 %' (redondeo de 0.388 en métricas) pasa; uno con '57 %' inventado falla."""
    ctx, plan, ficha = _sample_context()

    # '39 %' (de 0.3875 -> 38.8% / 39%) y '4,2 %' (Barcelona) están en métricas -> pasa
    ok_text = (
        "Clínica Alborada Visión alcanza una aparición espontánea del 39 % (38,8 % exacto, n=240), "
        "con un 4,2 % en Barcelona y un 54,2 % en Madrid."
    )
    inc_ok, ver_ok, no_traz_ok = verify_numbers(ok_text, ctx)
    assert no_traz_ok == 0
    assert ver_ok >= 4
    assert inc_ok == []

    # '57 %' inventado -> falla con incidencia bloqueante cifra_no_trazable
    bad_text = "Clínica Alborada Visión alcanza una cuota espontánea del 57 % en Barcelona."
    inc_bad, _, no_traz_bad = verify_numbers(bad_text, ctx)
    assert no_traz_bad >= 1
    assert any(i.tipo == "cifra_no_trazable" and i.bloqueante for i in inc_bad)


def test_compliance_promise_and_denigratory_comparison() -> None:
    """'garantizamos resultados' produce promesa_resultado bloqueante; 'mejor que Láser Nítida' produce comparativa_denigratoria."""
    ctx, plan, ficha = _sample_context()

    # 1. 'garantizamos resultados' -> promesa_resultado bloqueante
    rev_promise = compliance(
        "Con este plan garantizamos resultados en cirugía refractiva en 12 meses.",
        plan=plan,
        ficha=ficha,
        contexto_cifras=ctx,
        provider="mock",
    )
    assert rev_promise.aprobado is False
    assert any(
        i.tipo == "promesa_resultado" and i.bloqueante for i in rev_promise.incidencias
    )

    # 2. 'mejor que Láser Nítida' -> comparativa_denigratoria bloqueante
    rev_denig = compliance(
        "El seguimiento de Alborada es mucho mejor que Láser Nítida en el postoperatorio.",
        plan=plan,
        ficha=ficha,
        contexto_cifras=ctx,
        provider="mock",
    )
    assert rev_denig.aprobado is False
    assert any(
        i.tipo == "comparativa_denigratoria" and i.bloqueante
        for i in rev_denig.incidencias
    )

    # 3. Texto limpio y trazable + plan válido -> aprobado=True
    clean_text = (
        "Clínica Alborada Visión registra un 38,8 % de aparición espontánea (n=240) "
        "y propone un plan de 12 meses con presupuesto dentro del rango de 18.000 € a 27.000 €."
    )
    rev_clean = compliance(
        clean_text,
        plan=plan,
        ficha=ficha,
        contexto_cifras=ctx,
        provider="mock",
    )
    assert rev_clean.aprobado is True
    assert rev_clean.cifras_no_trazables == 0
