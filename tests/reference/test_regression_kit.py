"""WB2: el pipeline en mock con los datos y el brief del kit reproduce la instantánea previa."""

import io
import json

import pandas as pd
import pytest

from tests.reference.snapshot_tools import SNAPSHOT_DIR, build_snapshot, run_kit

TOL = 1e-9


def _assert_json_igual(esperado, actual, ruta: str = "") -> None:
    if isinstance(esperado, dict):
        assert isinstance(actual, dict), ruta
        assert set(esperado) == set(actual), f"{ruta}: claves distintas {set(esperado) ^ set(actual)}"
        for k in esperado:
            _assert_json_igual(esperado[k], actual[k], f"{ruta}/{k}")
    elif isinstance(esperado, list):
        assert isinstance(actual, list) and len(esperado) == len(actual), f"{ruta}: longitud"
        for i, (e, a) in enumerate(zip(esperado, actual)):
            _assert_json_igual(e, a, f"{ruta}[{i}]")
    elif isinstance(esperado, float) or isinstance(actual, float):
        assert actual == pytest.approx(esperado, abs=TOL, rel=0), ruta
    else:
        assert esperado == actual, ruta


@pytest.fixture(scope="module")
def snap(tmp_path_factory: pytest.TempPathFactory) -> dict:
    return build_snapshot(run_kit(tmp_path_factory.mktemp("kit")))


@pytest.mark.parametrize(
    "nombre",
    ["metrics.json", "findings.json", "plan.json", "revision.json", "secciones.json"],
)
def test_json_igual_a_la_instantanea(snap: dict, nombre: str) -> None:
    esperado = json.loads((SNAPSHOT_DIR / nombre).read_text(encoding="utf-8"))
    # Ida y vuelta por JSON para normalizar tipos como en el fichero guardado.
    actual = json.loads(json.dumps(snap["json"][nombre], ensure_ascii=False))
    _assert_json_igual(esperado, actual, nombre)


def test_tablas_iguales_a_la_instantanea(snap: dict) -> None:
    esperadas = sorted(p.stem for p in (SNAPSHOT_DIR / "tablas").glob("*.csv"))
    assert esperadas == sorted(snap["tablas"])
    for nombre in esperadas:
        exp = pd.read_csv(SNAPSHOT_DIR / "tablas" / f"{nombre}.csv", encoding="utf-8-sig")
        actual = pd.read_csv(io.StringIO(snap["tablas"][nombre].to_csv(index=False)))
        assert list(exp.columns) == list(actual.columns), nombre
        pd.testing.assert_frame_equal(exp, actual, check_exact=False, rtol=0, atol=TOL, obj=nombre)


def test_cifras_trazables_igual(snap: dict) -> None:
    rev = snap["json"]["revision.json"]
    assert rev["cifras_no_trazables"] == 0
    assert rev["cifras_verificadas"] == json.loads(
        (SNAPSHOT_DIR / "revision.json").read_text(encoding="utf-8")
    )["cifras_verificadas"]
