"""WC2 · Propuesta de marcas y banco de prompts."""

from __future__ import annotations

from pathlib import Path

import pytest

from geo import loader
from geo.schemas import FichaMarca
from geo.study import brands as B
from geo.study import prompt_bank as PB
from geo.study.brands import MarcaPropuesta, PropuestaMarcas

KIT = Path(__file__).resolve().parents[2] / "geo" / "reference_data"


# ---------------------------------------------------------------- marcas


def test_marcas_con_servidor_falso(fake: str, ficha: FichaMarca, tmp_path: Path) -> None:
    prop = B.propose_brands(ficha, study_dir=tmp_path, reference=False)
    nombres = [m.nombre for m in prop.marcas]
    assert nombres[0] == ficha.marca
    assert prop.marcas[0].nivel == "foco" and prop.marcas[0].rol == "MARCA DEL BRIEF"
    for c in ficha.competidores_declarados:
        assert c in nombres
    assert sum(m.nivel == "foco" for m in prop.marcas) <= 4
    assert len(prop.marcas) <= 12
    assert len({m.nombre for m in prop.marcas}) == len(prop.marcas)
    assert prop.marcas[0].dominio == "linguaturia.example"  # sin www
    assert (tmp_path / "marcas.csv").exists() and (tmp_path / "propuesta_marcas.json").exists()
    leidas = loader.load_marcas(tmp_path / "marcas.csv")
    assert [m.nombre for m in leidas] == nombres
    assert leidas[0].es_marca_brief


def test_validate_brands_reglas(ficha: FichaMarca) -> None:
    crudo = PropuestaMarcas(
        marcas=[
            MarcaPropuesta(nombre="Otra", nivel="foco", rol="competidor detectado", dominio="https://www.otra.com/x"),
            MarcaPropuesta(nombre="otra", nivel="foco", rol="x", dominio="otra2.com"),  # duplicada por nombre
            MarcaPropuesta(nombre="Clon", nivel="foco", rol="x", dominio="otra.com"),  # duplicada por dominio
            MarcaPropuesta(nombre="Escuela Babel", nivel="contexto", rol="x", dominio="babel.es", alias=list("abcdefg")),
            *[MarcaPropuesta(nombre=f"F{i}", nivel="foco", rol="x", dominio=f"f{i}.com") for i in range(10)],
        ]
    )
    out = B.validate_brands(crudo, ficha)
    nombres = [m.nombre for m in out.marcas]
    assert nombres[0] == ficha.marca and out.marcas[0].nivel == "foco"  # se añade la marca del brief
    assert out.marcas[0].dominio == "linguaturia.example"
    assert {"Escuela Babel", "Idiomas Costa", "Centro Polilingüe"} <= set(nombres)
    assert nombres.count("Otra") == 1 and "Clon" not in nombres
    assert next(m for m in out.marcas if m.nombre == "Otra").dominio == "otra.com"
    assert sum(m.nivel == "foco" for m in out.marcas) == 4
    assert len(out.marcas) == 12
    assert len(next(m for m in out.marcas if m.nombre == "Escuela Babel").alias) <= 4


def test_marcas_proveedor_mock(mock_env: None, ficha: FichaMarca) -> None:
    prop = B.propose_brands(ficha, reference=False)
    assert [m.nombre for m in prop.marcas][:2] == [ficha.marca, "Escuela Babel"]


def test_marcas_referencia_sin_red(mock_env: None, tmp_path: Path) -> None:
    f = FichaMarca(marca="Clínica Alborada Visión", sector="Oftalmología", objetivo_principal="x")
    prop = B.propose_brands(f, study_dir=tmp_path)  # detección automática; el guardián de red falla si se llama
    assert len(prop.marcas) == 10
    assert (tmp_path / "marcas.csv").read_bytes() == (KIT / "marcas.csv").read_bytes()


# ---------------------------------------------------------------- banco


def _marcas(ficha: FichaMarca) -> list[MarcaPropuesta]:
    return B.validate_brands(B.mock_proposal(ficha), ficha).marcas


def test_banco_con_servidor_falso(fake: str, ficha: FichaMarca, tmp_path: Path) -> None:
    marcas = _marcas(ficha)
    res = PB.propose_bank(ficha, marcas, study_dir=tmp_path, reference=False)
    assert PB.missing_families(res.prompts) == []
    assert 20 <= len(res.prompts) <= 28
    ids = [p.prompt_id for p in res.prompts]
    assert len(set(ids)) == len(ids) and all(i.startswith("ACA-") for i in ids)
    for p in res.prompts:
        assert PB.marker_problem(p.instanciacion, p.plantilla) == ""
        if p.instanciacion in ("generico", "ciudad"):
            assert PB.names_brand(p.plantilla, marcas) is None
    assert (tmp_path / "banco_prompts.csv").exists()
    leidos = loader.load_prompts(tmp_path / "banco_prompts.csv")
    assert [p.prompt_id for p in leidos] == ids


def test_banco_rechaza_espontaneo_con_marca(fake: str, monkeypatch: pytest.MonkeyPatch, ficha: FichaMarca) -> None:
    monkeypatch.setenv("FAKE_OR_BANK_BAD", "1")
    res = PB.propose_bank(ficha, _marcas(ficha), reference=False)
    assert any("nombra" in d["motivo"] and ficha.marca in d["plantilla"] for d in res.descartados)
    assert all(ficha.marca not in p.plantilla for p in res.prompts)


def test_validate_bank_reglas(ficha: FichaMarca) -> None:
    marcas = _marcas(ficha)
    P = PB.PlantillaLLM
    prop = PB.PropuestaBancoLLM(
        plantillas=[
            P(familia="DG", instanciacion="generico", plantilla="¿Qué academias de inglés recomiendas en España?"),
            P(familia="DG", instanciacion="generico", plantilla="¿Es Escuela Babel una buena academia de inglés?"),
            P(familia="LO", instanciacion="ciudad", plantilla="¿Qué academia hay en España para aprender inglés?"),  # falta [CIUDAD]
            P(familia="VR", instanciacion="marca", plantilla="¿Qué opinan de [MARCA_A] y de [MARCA_B]?"),  # sobra B
            P(familia="CM", instanciacion="par", plantilla="¿[MARCA_A] o [MARCA_B]?, dime cuál elegir"),
            P(familia="ZZ", instanciacion="generico", plantilla="¿Qué academia de inglés es la mejor?"),
            P(familia="PR", instanciacion="marca", plantilla="¿Cuánto cuesta [MARCA_A] al mes?"),  # PR no admite marca
        ]
    )
    res = PB.validate_bank(prop, ficha, marcas)
    assert [p.prompt_id for p in res.prompts] == ["ACA-DG-01", "ACA-CM-01"]
    assert len(res.descartados) == 5
    assert all(PB._ID_RX.match(p.prompt_id) for p in res.prompts)


def test_banco_referencia_25_plantillas(mock_env: None, tmp_path: Path) -> None:
    f = FichaMarca(marca="Vistalia Oftalmología", sector="Oftalmología", objetivo_principal="x")
    res = PB.propose_bank(f, [], study_dir=tmp_path)
    assert len(res.prompts) == 25
    assert (tmp_path / "banco_prompts.csv").read_bytes() == (KIT / "banco_prompts.csv").read_bytes()


def test_instanciacion_2_ciudades_3_foco(ficha: FichaMarca) -> None:
    marcas = _marcas(ficha)  # marca + 3 declarados = 4 foco
    marcas = [m for m in marcas if m.nombre != "Centro Polilingüe"]  # 3 foco
    assert sum(m.nivel == "foco" for m in marcas) == 3
    mk = lambda i, inst, t: PB.Prompt(  # noqa: E731
        prompt_id=f"ACA-DG-0{i}", familia="f", intencion="Descubrimiento", prioridad="P1", uso="Publicable",
        instanciacion=inst, plantilla=t,
    )
    banco = [
        mk(1, "generico", "¿Qué academia?"),
        mk(2, "ciudad", "¿Qué academia en [CIUDAD]?"),
        mk(3, "marca", "¿Opinión de [MARCA_A]?"),
        mk(4, "par", "[MARCA_A] contra [MARCA_B]"),
    ]
    ins = PB.instantiate(banco, marcas, ficha)
    por = {k: [i for i in ins if i.instanciacion == k] for k in ("generico", "ciudad", "marca", "par")}
    assert len(por["generico"]) == 1 and len(por["generico"][0].marcas_a_evaluar) == len(marcas)
    assert [i.ciudad for i in por["ciudad"]] == ["Valencia", "Alicante"]
    assert len(por["marca"]) == 3 and all(len(i.marcas_a_evaluar) == 1 for i in por["marca"])
    assert len(por["par"]) == 2 and all(len(i.marcas_a_evaluar) == 2 for i in por["par"])
    assert len(ins) == 1 + 2 + 3 + 2
    assert all("[" not in i.prompt for i in ins)


def test_instanciacion_reproduce_el_kit() -> None:
    import pandas as pd

    banco = PB.read_banco_csv(KIT / "banco_prompts.csv")
    marcas = B.read_marcas_csv(KIT / "marcas.csv")
    f = FichaMarca(marca="Clínica Alborada Visión", sector="x", objetivo_principal="o", ciudades=["Madrid", "Barcelona"])
    ins = PB.instantiate(banco, marcas, f)
    e = pd.read_csv(KIT / "ejecuciones.csv", encoding="utf-8-sig")
    kit = set(zip(e["Prompt_ID"], e["Prompt ejecutado"], e["Marcas a evaluar"]))
    mine = {(i.prompt_id, i.prompt, " | ".join(i.marcas_a_evaluar)) for i in ins}
    assert len(ins) == 52 and kit == mine
