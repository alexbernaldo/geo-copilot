"""Tests de carga y validación de datos (F1)."""

import pandas as pd

from geo.config import (
    BANCO_PROMPTS_CSV,
    EJECUCIONES_CSV,
    FUENTES_CATALOGO_CSV,
    MARCAS_CSV,
    MOTORES,
    MUESTRA_EVALUADA_CSV,
)
from geo.loader import (
    as_ejecuciones,
    dominios_desconocidos,
    load_ejecuciones,
    load_fuentes,
    load_marcas,
    load_muestra,
    load_prompts,
)


def test_no_bom_in_raw_csv_columns() -> None:
    """Comprueba que ningún CSV tiene caracteres BOM en los nombres de columna."""
    for path in (
        MARCAS_CSV,
        BANCO_PROMPTS_CSV,
        EJECUCIONES_CSV,
        FUENTES_CATALOGO_CSV,
        MUESTRA_EVALUADA_CSV,
    ):
        df = pd.read_csv(path, encoding="utf-8-sig")
        for col in df.columns:
            assert "\ufeff" not in col, f"BOM detectado en columna '{col}' de {path.name}"


def test_load_marcas() -> None:
    """Comprueba las 10 marcas, alias separados y la marca del brief identificada."""
    marcas = load_marcas()
    assert len(marcas) == 10

    marcas_brief = [m for m in marcas if m.es_marca_brief]
    assert len(marcas_brief) == 1
    alborada = marcas_brief[0]
    assert alborada.nombre == "Clínica Alborada Visión"
    assert alborada.alias == ["Alborada Visión", "Alborada"]


def test_load_prompts() -> None:
    """Comprueba los 25 prompts y sus tipos de instanciación."""
    prompts = load_prompts()
    assert len(prompts) == 25
    counts: dict[str, int] = {}
    for p in prompts:
        counts[p.instanciacion] = counts.get(p.instanciacion, 0) + 1
    assert counts == {"generico": 16, "ciudad": 2, "marca": 5, "par": 2}


def test_load_fuentes_and_dominios_desconocidos() -> None:
    """Comprueba las 25 fuentes del catálogo y que no hay dominios desconocidos en el kit."""
    fuentes = load_fuentes()
    assert len(fuentes) == 25
    assert fuentes["wikipedia.org"] == ("Ranking / institución", 1.0)
    assert dominios_desconocidos() == []


def test_load_ejecuciones_and_as_ejecuciones() -> None:
    """Comprueba las 624 ejecuciones, reparto por motor, espontáneas/asistidas y ciudades."""
    df = load_ejecuciones()
    assert len(df) == 624
    for col in df.columns:
        assert "\ufeff" not in col

    # 156 por motor
    por_motor = df["motor"].value_counts().to_dict()
    for motor in MOTORES:
        assert por_motor.get(motor) == 156

    # 240 espontáneas y 384 asistidas
    n_espontaneas = int(df["espontanea"].sum())
    n_asistidas = int((~df["espontanea"]).sum())
    assert n_espontaneas == 240
    assert n_asistidas == 384

    # 24 con ciudad=Madrid y 24 con ciudad=Barcelona
    ciudades = df["ciudad"].value_counts(dropna=True).to_dict()
    assert ciudades == {"Madrid": 24, "Barcelona": 24}
    assert int(df["ciudad"].isna().sum()) == 624 - 48

    # Validación Pydantic completa con as_ejecuciones()
    objs = as_ejecuciones()
    assert len(objs) == 624
    total_marcas_evaluar = sum(len(e.marcas_a_evaluar) for e in objs)
    assert total_marcas_evaluar == 2928


def test_load_muestra() -> None:
    """Comprueba las 133 filas y 15 Ejecucion_ID únicos en muestra_evaluada.csv."""
    df = load_muestra()
    assert len(df) == 133
    assert df["ejecucion_id"].nunique() == 15
    for col in df.columns:
        assert "\ufeff" not in col
    expected_cols = {
        "ejecucion_id",
        "marca",
        "aparece",
        "posicion",
        "peso_posicion",
        "tipo_mencion",
        "fuerza",
        "sentimiento",
        "tipo_fuente",
    }
    assert expected_cols.issubset(set(df.columns))
