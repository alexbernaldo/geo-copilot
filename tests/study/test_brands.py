"""B2.1 · Propuesta de marcas: la validación es del código, no del modelo.

Cubre: marca del brief siempre presente y en foco, competidores declarados presentes, máximo de foco y de
total, sin duplicados por nombre normalizado ni por dominio, dominio normalizado, alias y motivo acotados,
nivel inválido rechazado y modo de referencia sin red.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from geo.study import brands
from geo.study.brands import MarcaPropuesta, PropuestaMarcas
from geo.study.common import norm_name

KIT_DIR = Path(__file__).resolve().parents[2] / "geo" / "reference_data"


def _marca(nombre: str, **kw) -> MarcaPropuesta:
    datos: dict = {
        "nombre": nombre,
        "nivel": "contexto",
        "rol": "competidor detectado",
        "dominio": "",
        "alias": [],
        "motivo": "",
    }
    datos.update(kw)
    return MarcaPropuesta(**datos)


def _nombres(marcas: list[MarcaPropuesta]) -> set[str]:
    return {norm_name(m.nombre) for m in marcas}


# ---------------------------------------------------------------- con el servidor falso


def test_la_propuesta_incluye_la_marca_del_brief(fake, ficha, tmp_path: Path) -> None:
    prop = brands.propose_brands(ficha, study_dir=tmp_path, provider="openrouter")
    assert norm_name(ficha.marca) in _nombres(prop.marcas)


def test_la_marca_del_brief_queda_en_foco_con_el_rol_del_brief(fake, ficha, tmp_path: Path) -> None:
    prop = brands.propose_brands(ficha, study_dir=tmp_path, provider="openrouter")
    marca = next(m for m in prop.marcas if norm_name(m.nombre) == norm_name(ficha.marca))
    assert marca.nivel == "foco"
    assert marca.rol == brands.ROL_MARCA


def test_los_competidores_declarados_siempre_estan(fake, ficha, tmp_path: Path) -> None:
    prop = brands.propose_brands(ficha, study_dir=tmp_path, provider="openrouter")
    nombres = _nombres(prop.marcas)
    for declarado in ficha.competidores_declarados:
        assert norm_name(declarado) in nombres


def test_hay_como_maximo_cuatro_marcas_en_foco(fake, ficha, tmp_path: Path) -> None:
    prop = brands.propose_brands(ficha, study_dir=tmp_path, provider="openrouter")
    assert sum(1 for m in prop.marcas if m.nivel == "foco") <= brands.DEFAULT_MAX_FOCO


def test_la_propuesta_se_guarda_en_marcas_csv_con_las_columnas_del_kit(fake, ficha, tmp_path: Path) -> None:
    brands.propose_brands(ficha, study_dir=tmp_path, provider="openrouter")
    csv = tmp_path / "marcas.csv"
    assert csv.exists()
    assert brands.marcas_to_df(brands.read_marcas_csv(csv)).columns.tolist() == brands.MARCAS_COLUMNS


# ---------------------------------------------------------------- validaciones por código (sin red)


def test_el_codigo_repone_la_marca_del_brief_si_el_modelo_no_la_propone(ficha) -> None:
    prop = brands.validate_brands(PropuestaMarcas(marcas=[_marca("Otra Marca")]), ficha)
    nombres = _nombres(prop.marcas)
    assert norm_name(ficha.marca) in nombres
    marca = prop.marcas[0]
    assert marca.nivel == "foco" and marca.rol == brands.ROL_MARCA


def test_el_codigo_repone_los_competidores_declarados_si_faltan(ficha) -> None:
    prop = brands.validate_brands(PropuestaMarcas(marcas=[]), ficha)
    nombres = _nombres(prop.marcas)
    for declarado in ficha.competidores_declarados:
        assert norm_name(declarado) in nombres
    declarados = [m for m in prop.marcas if m.rol == brands.ROL_DECLARADO]
    assert len(declarados) == len(ficha.competidores_declarados)


def test_no_hay_duplicados_por_nombre_normalizado(ficha) -> None:
    prop = brands.validate_brands(
        PropuestaMarcas(marcas=[_marca("Acme Idiomas"), _marca("ACME  IDIOMAS"), _marca("Otra")]), ficha
    )
    assert len(_nombres(prop.marcas)) == len(prop.marcas)


def test_no_hay_duplicados_por_dominio(ficha) -> None:
    prop = brands.validate_brands(
        PropuestaMarcas(
            marcas=[
                _marca("Marca Norte", dominio="norte.example"),
                _marca("Marca Sur", dominio="norte.example"),
            ]
        ),
        ficha,
    )
    dominios = [m.dominio for m in prop.marcas if m.dominio]
    assert len(dominios) == len(set(dominios))


def test_el_dominio_se_normaliza_sin_www_ni_ruta(ficha) -> None:
    prop = brands.validate_brands(
        PropuestaMarcas(marcas=[_marca("Marca Ruido", dominio="https://WWW.Ejemplo.COM/ruta?x=1")]), ficha
    )
    ruido = next(m for m in prop.marcas if m.nombre == "Marca Ruido")
    assert ruido.dominio == "ejemplo.com"


def test_el_alias_se_acota_a_cuatro_y_no_repite_el_nombre(ficha) -> None:
    prop = brands.validate_brands(
        PropuestaMarcas(
            marcas=[
                _marca(
                    "Marca Ruido",
                    alias=["Alias Uno", "Alias Dos", "Alias Tres", "Alias Cuatro", "Alias Cinco", "Marca Ruido"],
                )
            ]
        ),
        ficha,
    )
    ruido = next(m for m in prop.marcas if m.nombre == "Marca Ruido")
    assert len(ruido.alias) == brands.MAX_ALIAS
    assert "Marca Ruido" not in ruido.alias


def test_el_motivo_se_acota_a_doscientos_caracteres(ficha) -> None:
    prop = brands.validate_brands(PropuestaMarcas(marcas=[_marca("Marca Ruido", motivo="x" * 400)]), ficha)
    ruido = next(m for m in prop.marcas if m.nombre == "Marca Ruido")
    assert len(ruido.motivo) == 200


def test_se_respetan_los_maximos_de_foco_y_de_total(ficha) -> None:
    marcas = [_marca(f"Marca {i}", nivel="foco") for i in range(10)]
    prop = brands.validate_brands(PropuestaMarcas(marcas=marcas), ficha, max_foco=2, max_total=3)
    obligatorias = 1 + len(ficha.competidores_declarados)
    assert sum(1 for m in prop.marcas if m.nivel == "foco") <= 2
    # La marca del brief y sus competidores declarados nunca se descartan: el total no baja de esa marca.
    assert len(prop.marcas) == max(3, obligatorias)


def test_un_nivel_distinto_de_foco_o_contexto_se_rechaza() -> None:
    with pytest.raises(ValidationError):
        _marca("Marca Ruido", nivel="primario")


# ---------------------------------------------------------------- modo de referencia


def test_el_modo_referencia_devuelve_el_kit_sin_ninguna_llamada_de_red(kit_ficha, monkeypatch, tmp_path: Path) -> None:
    import requests

    def _no_red(*a, **kw):  # pragma: no cover - solo se llama si el modo referencia saliera a la red
        raise AssertionError("El modo de referencia no puede llamar a la red")

    monkeypatch.setattr(requests.sessions.Session, "request", _no_red)
    prop = brands.propose_brands(kit_ficha, study_dir=tmp_path, reference=True)
    kit = brands.read_marcas_csv(KIT_DIR / "marcas.csv")
    assert [m.nombre for m in prop.marcas] == [m.nombre for m in kit]
    assert (tmp_path / "marcas.csv").read_bytes() == (KIT_DIR / "marcas.csv").read_bytes()
