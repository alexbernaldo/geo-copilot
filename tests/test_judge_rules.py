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
