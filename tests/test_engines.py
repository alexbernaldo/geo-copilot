"""Tests de los conectores de motores conversacionales con búsqueda web y mini-estudio (F15)."""

from geo.engines import (
    estimate_mini_study_cost,
    extract_domain,
    run_engine,
    run_mini_study,
)


def test_extract_domain_normalizes_urls() -> None:
    """Verifica que extract_domain limpie esquema, www., puerto y ruta."""
    assert extract_domain("https://www.cuidateplus.marca.com/salud/2025/articulo.html") == "cuidateplus.marca.com"
    assert extract_domain("http://oftalmologia.org.es:8080/guia") == "oftalmologia.org.es"
    assert extract_domain("topdoctors.es/madrid") == "topdoctors.es"
    assert extract_domain("") == ""


def test_all_four_engines_run_and_degrade_cleanly_in_mock() -> None:
    """Los 4 motores (ChatGPT, Gemini, Perplexity, Claude) responden con texto, dominios y degradado=True sin red."""
    prompt = "¿Qué clínicas oftalmológicas destacan en España?"
    for motor in ("ChatGPT", "Gemini", "Perplexity", "Claude"):
        resp, doms, deg = run_engine(motor, prompt, repeticion=1, use_cache=False)
        assert isinstance(resp, str) and len(resp) > 20
        assert isinstance(doms, list) and len(doms) >= 1
        assert deg is True


def test_mini_study_24_calls_and_cost_estimation() -> None:
    """El mini-estudio de 6 prompts × 2 motores × 2 repeticiones produce 24 filas con las columnas de ejecuciones.csv."""
    est = estimate_mini_study_cost(n_prompts=6, n_motors=2, repeticiones=2)
    assert est["total_calls"] == 24
    assert est["estimated_cost_eur"] > 0
    assert est["within_budget"] is True

    df_out, meta = run_mini_study(
        motores=("ChatGPT", "Perplexity"),
        repeticiones=2,
        use_cache=False,
    )
    assert len(df_out) == 24
    expected_cols = {
        "ejecucion_id",
        "prompt_id",
        "familia",
        "intencion",
        "instanciacion",
        "prompt_ejecutado",
        "motor",
        "repeticion",
        "respuesta",
        "fuentes",
        "ciudad",
        "espontanea",
    }
    assert expected_cols.issubset(set(df_out.columns))
    assert meta["aislado_del_kit"] is True
    assert meta["degradado"] is True
