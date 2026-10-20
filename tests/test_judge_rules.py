"""Tests del juez por reglas y su validación contra muestra_evaluada.csv (F3)."""

import pandas as pd

from geo.detection import detect
from geo.judge_rules import judge_brand_mention, judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas, load_muestra
from geo.validation import compare


def test_judge_rules_unit_patterns() -> None:
    """Comprueba cada rama de las reglas léxicas en judge_brand_mention."""
    marcas = {m.nombre: m for m in load_marcas()}
    alborada = marcas["Clínica Alborada Visión"]
    catalogo = load_fuentes()

    # 1. No aparece -> fuerza 0, resto None
    res_ausente = judge_brand_mention(0, None, None, alborada, ["wikipedia.org"], catalogo)
    assert res_ausente == (None, 0, None, None, None, None, False)

    # 2. Desconocimiento -> Pasiva, 1, neutro, Sin fuente, desconocimiento=True
    res_desc = judge_brand_mention(
        1,
        1,
        "No dispongo de información suficiente y verificada sobre Clínica Alborada Visión.",
        alborada,
        ["wikipedia.org"],
        catalogo,
    )
    assert res_desc == ("Pasiva", 1, "neutro", "Sin fuente", None, 0.2, True)

    # 3. Negativo -> Comparación neutra, -1, negativo
    res_neg = judge_brand_mention(
        1,
        2,
        "Clínica Alborada Visión ofrece cirugía láser. Eso sí, se reportan quejas puntuales.",
        alborada,
        ["alboradavision.example"],
        catalogo,
    )
    assert res_neg[:4] == ("Comparación neutra", -1, "negativo", "Web propia")

    # 4. Fuerza 3 -> Recomendación activa, 3, positivo
    res_f3 = judge_brand_mention(
        1,
        1,
        "1. **Clínica Alborada Visión** — seguimiento personalizado. Es la que más recomendaría.",
        alborada,
        ["colegiooftalmologos.example"],
        catalogo,
    )
    assert res_f3[:4] == ("Recomendación activa", 3, "positivo", "Ranking / institución")

    # 5. Fuerza 2 -> Comparación neutra, 2, positivo
    res_f2 = judge_brand_mention(
        1,
        2,
        "2. **Clínica Alborada Visión** — trato cercano. Es una alternativa muy bien valorada.",
        alborada,
        ["saludactual.example"],
        catalogo,
    )
    assert res_f2[:4] == ("Comparación neutra", 2, "positivo", "Medio")

    # 6. Fuerza 1 en posición >= 4 -> Pasiva, 1, neutro
    res_pas = judge_brand_mention(
        1,
        4,
        "4. **Clínica Alborada Visión** — ofrece una valoración preoperatoria completa y un trato cercano.",
        alborada,
        [],
        catalogo,
    )
    assert res_pas[:4] == ("Pasiva", 1, "neutro", "Sin fuente")


def test_judge_rules_validation_thresholds_against_muestra() -> None:
    """Comprueba que el juez por reglas supera ampliamente los umbrales de F3 (fuerza>=85%, sentimiento>=85%, tipo_mencion>=75%)."""
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    muestra = load_muestra()
    catalogo = load_fuentes()

    ej_ids_muestra = set(muestra["ejecucion_id"].unique())
    df_ej_muestra = df_ej[df_ej["ejecucion_id"].isin(ej_ids_muestra)].copy()
    df_det = detect(df_ej_muestra, marcas)
    df_pred = judge_rules(df_det, df_ej_muestra, marcas, catalogo)

    assert len(df_pred) == 133

    # Validación sobre filas con aparición (n=67) y sobre el total (n=133)
    for only_present in (True, False):
        report = compare(df_pred, muestra, only_present=only_present)
        assert report["fuerza"]["accuracy"] >= 0.85
        assert report["sentimiento"]["accuracy"] >= 0.85
        assert report["tipo_mencion"]["accuracy"] >= 0.75
        assert report["fuerza"]["kappa"] > 0.80
        assert report["sentimiento"]["kappa"] > 0.80
        assert report["tipo_mencion"]["kappa"] > 0.70


def test_judge_llm_cache_and_ensemble(tmp_path) -> None:
    """Comprueba F4: caché de complete_json (0 llamadas en 2ª ejecución), validaciones y ensemble."""
    from geo.judge import combine_rules_and_llm, judge_ensemble
    from geo.judge_llm import FEW_SHOT_EJECUCION_IDS, judge_llm
    from geo.llm import get_llm_stats, reset_llm_stats

    marcas = load_marcas()
    df_ej = load_ejecuciones()
    muestra = load_muestra()
    catalogo = load_fuentes()

    ej_ids_muestra = set(muestra["ejecucion_id"].unique())
    df_ej_muestra = df_ej[df_ej["ejecucion_id"].isin(ej_ids_muestra)].copy()
    df_det = detect(df_ej_muestra, marcas)

    # 1ª ejecución poblando caché
    reset_llm_stats()
    df_ens_1 = judge_ensemble(
        df_det,
        df_ej_muestra,
        marcas,
        catalogo,
        provider="mock",
        use_cache=True,
        persist_path=tmp_path / "evaluaciones.parquet",
    )
    assert (tmp_path / "evaluaciones.parquet").exists()
    assert len(df_ens_1) == 133

    # 2ª ejecución: todas las llamadas deben salir de caché (0 llamadas nuevas)
    reset_llm_stats()
    df_llm_2 = judge_llm(
        df_det,
        df_ej_muestra,
        marcas,
        catalogo,
        provider="mock",
        use_cache=True,
    )
    stats_2 = get_llm_stats()
    assert stats_2["calls"] == 0
    assert stats_2["cache_hits"] == 15

    # Comprobar detección de discrepancia en combine_rules_and_llm cuando LLM discrepa de reglas
    df_rules = judge_rules(df_det, df_ej_muestra, marcas, catalogo)
    df_llm_mod = df_llm_2.copy()
    first_present_idx = df_llm_mod.index[df_llm_mod["aparece"] == 1][0]
    df_llm_mod.loc[first_present_idx, "fuerza"] = -1
    df_llm_mod.loc[first_present_idx, "sentimiento"] = "negativo"

    df_comb = combine_rules_and_llm(df_rules, df_llm_mod, df_ej_muestra, marcas, catalogo)
    row_disc = df_comb.loc[first_present_idx]
    assert bool(row_disc["discrepancia"]) is True
    assert float(row_disc["confianza_juez"]) == 0.6
    assert int(row_disc["fuerza"]) == -1

    # Validación excluyendo las 3 ejecuciones few-shot
    rep = compare(
        df_ens_1,
        muestra,
        only_present=True,
        exclude_ejecucion_ids=FEW_SHOT_EJECUCION_IDS,
    )
    assert rep["fuerza"]["accuracy"] >= 0.85
    assert rep["tipo_mencion"]["accuracy"] >= 0.75
