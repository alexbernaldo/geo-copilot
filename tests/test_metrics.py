"""Tests de cálculo del Score de Citación y tablas T1-T12 (F5)."""

import math
import pandas as pd

from geo.detection import detect
from geo.judge_rules import judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas
from geo.metrics import bundle, score


def test_a_score_synthetic_hand_calculated() -> None:
    """(a) Score de un DataFrame sintético pequeño calculado a mano."""
    # 2 filas:
    # Fila 1: aparece=1, peso_posicion=3 (pos 1), fuerza=3, calidad_fuente=1.0
    # Fila 2: aparece=0, peso_posicion=0, fuerza=0, calidad_fuente=None
    # tasa_aparicion = 0.5
    # aparicion = 30 * 0.5 = 15.0
    # posicion  = 20 * (1.5 / 3) = 10.0
    # fuerza    = 30 * (1.5 / 3) = 15.0
    # fuente    = 20 * 0.5 * 1.0 = 10.0
    # score     = 50.0
    df = pd.DataFrame(
        [
            {"aparece": 1, "peso_posicion": 3, "fuerza": 3, "calidad_fuente": 1.0},
            {"aparece": 0, "peso_posicion": 0, "fuerza": 0, "calidad_fuente": None},
        ]
    )
    res = score(df)
    assert res["n"] == 2
    assert math.isclose(float(res["tasa_aparicion"]), 0.5)
    assert math.isclose(float(res["aparicion"]), 15.0)
    assert math.isclose(float(res["posicion"]), 10.0)
    assert math.isclose(float(res["fuerza"]), 15.0)
    assert math.isclose(float(res["fuente"]), 10.0)
    assert math.isclose(float(res["score"]), 50.0)


def test_b_group_without_appearances_gives_zero() -> None:
    """(b) Un grupo sin apariciones da 0 en todos los componentes y en el score total."""
    df = pd.DataFrame(
        [
            {"aparece": 0, "peso_posicion": 0, "fuerza": 0, "calidad_fuente": None},
            {"aparece": 0, "peso_posicion": 0, "fuerza": 0, "calidad_fuente": None},
        ]
    )
    res = score(df)
    assert res["n"] == 2
    assert res["aparicion"] == 0.0
    assert res["posicion"] == 0.0
    assert res["fuerza"] == 0.0
    assert res["fuente"] == 0.0
    assert res["score"] == 0.0


def test_c_negative_mean_fuerza_truncated_to_zero() -> None:
    """(c) La fuerza negativa media se trunca a 0 en el componente de fuerza."""
    df = pd.DataFrame(
        [
            {"aparece": 1, "peso_posicion": 3, "fuerza": -1, "calidad_fuente": 0.6},
            {"aparece": 1, "peso_posicion": 2, "fuerza": -1, "calidad_fuente": 0.6},
        ]
    )
    res = score(df)
    assert res["fuerza"] == 0.0
    assert res["score"] > 0.0


def test_d_sum_of_components_equals_score_and_e_t1_disjoint(tmp_path) -> None:
    """(d) La suma de los 4 componentes es igual al score; (e) T1 espontánea y asistida no comparten filas/ejecuciones."""
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    catalogo = load_fuentes()
    df_det = detect(df_ej, marcas)
    evals = judge_rules(df_det, df_ej, marcas, catalogo)

    tablas = bundle(evals, df_ej, marcas, persist_dir=tmp_path)
    for t_id in (f"T{i}" for i in range(1, 13)):
        assert t_id in tablas, f"Falta tabla {t_id}"
        assert "ambito" in tablas[t_id].columns, f"Falta columna ambito en {t_id}"
        assert "evidencia_ids" in tablas[t_id].columns, f"Falta columna evidencia_ids en {t_id}"

    assert (tmp_path / "metrics.json").exists()

    t1_esp = tablas["T1_espontanea"]
    t1_asis = tablas["T1_asistida"]

    # (d) Suma de componentes = score en cada fila de T1, T2, T3, T4, T5
    for name in ("T1_espontanea", "T1_asistida", "T2", "T3", "T4", "T5"):
        df_t = tablas[name]
        for _, row in df_t.iterrows():
            comp_sum = (
                float(row["aparicion"])
                + float(row["posicion"])
                + float(row["fuerza"])
                + float(row["fuente"])
            )
            assert math.isclose(comp_sum, float(row["score"]), abs_tol=1e-9)

    # (e) T1 espontánea y asistida no comparten filas ni ejecuciones subyacentes
    assert len(t1_esp) == 10
    assert len(t1_asis) == 5  # las 4 marcas foco + Valdecruz (líder en duelos) -> comprobar ids disjuntos
    ids_esp = {eid for lst in t1_esp["evidencia_ids"] for eid in lst}
    ids_asis = {eid for lst in t1_asis["evidencia_ids"] for eid in lst}
    assert ids_esp.isdisjoint(ids_asis)

    # Comprobar valores orientativos de F5
    ap_by_brand = t1_esp.set_index("marca")["tasa_aparicion"].to_dict()
    assert math.isclose(ap_by_brand["Grupo Hospitalario Valdecruz"], 218 / 240, abs_tol=0.02)
    assert math.isclose(ap_by_brand["Instituto Oftálmico Tramuntana"], 165 / 240, abs_tol=0.02)
    assert math.isclose(ap_by_brand["Clínica Alborada Visión"], 93 / 240, abs_tol=0.02)
