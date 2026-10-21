"""B2.2 · Banco de prompts: nueve familias, marcadores por instanciación y prompted sin marcas en Templates.

Cubre: rechazo por código de plantillas con marcadores, instanciación o familias inválidas, plantillas
espontáneas que nombran una marca, plantillas repetidas, `Prompt_ID` con el formato del kit, cobertura de las
nueve familias, instanciación (genérico / ciudad / marca / par) y modo de referencia sin red.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from geo.schemas import Prompt
from geo.study import prompt_bank
from geo.study.brands import MarcaPropuesta
from geo.study.common import norm_name
from geo.study.prompt_bank import (
    FAMILIAS,
    PlantillaLLM,
    PropuestaBancoLLM,
    instantiate,
    marker_problem,
    missing_families,
    strategic_pairs,
    validate_bank,
)

KIT_DIR = Path(__file__).resolve().parents[2] / "geo" / "reference_data"
ID_RX = re.compile(r"^[A-Z]{3}-(DG|DP|LO|CO|CM|VR|FU|DF|PR)-\d{2}$")


def _prompt(prompt_id: str, familia: str, instanciacion: str, plantilla: str) -> Prompt:
    return Prompt(
        prompt_id=prompt_id,
        familia=familia,
        intencion="Descubrimiento",
        prioridad="P1",
        uso="Publicable",
        instanciacion=instanciacion,
        plantilla=plantilla,
    )


def _plantilla(familia: str, instanciacion: str, plantilla: str) -> PlantillaLLM:
    return PlantillaLLM(familia=familia, prioridad="P1", uso="Publicable", instanciacion=instanciacion, plantilla=plantilla)


def _marcas() -> list[MarcaPropuesta]:
    return [
        MarcaPropuesta(
            nombre="Academia Lingua Turia",
            nivel="foco",
            rol="MARCA DEL BRIEF",
            dominio="linguaturia.example",
            alias=["Lingua Turia"],
        ),
        MarcaPropuesta(nombre="Escuela Babel", nivel="foco", rol="competidor declarado", dominio="babel.example"),
        MarcaPropuesta(nombre="Idiomas Costa", nivel="foco", rol="competidor declarado", dominio="costa.example"),
        MarcaPropuesta(nombre="Grupo Torre", nivel="contexto", rol="líder de mercado", dominio="torre.example"),
    ]


# ---------------------------------------------------------------- marcadores y validación por código


def test_los_marcadores_correctos_dependen_de_la_instanciacion() -> None:
    assert marker_problem("generico", "¿Qué academias hay?") == ""
    assert marker_problem("ciudad", "¿Qué academias hay en [CIUDAD]?") == ""
    assert marker_problem("marca", "¿Quéopinión de [MARCA_A]?") == ""
    assert marker_problem("par", "¿[MARCA_A] o [MARCA_B]?") == ""


def test_un_marcador_que_sobra_o_falta_es_un_error() -> None:
    assert "marcadores incorrectos" in marker_problem("ciudad", "¿Qué academias hay?")
    assert "marcadores incorrectos" in marker_problem("generico", "¿Qué academias hay en [CIUDAD]?")
    assert "marcadores incorrectos" in marker_problem("marca", "¿[MARCA_A] frente a [MARCA_B]?")


def test_el_codigo_rechaza_una_plantilla_con_marcadores_incorrectos(ficha) -> None:
    res = validate_bank(PropuestaBancoLLM(plantillas=[_plantilla("LO", "ciudad", "¿Qué academias hay?")]), ficha, _marcas())
    assert res.prompts == []
    assert "marcadores incorrectos" in res.descartados[0]["motivo"]


def test_el_codigo_rechaza_una_familia_que_no_admite_la_instanciacion(ficha) -> None:
    res = validate_bank(PropuestaBancoLLM(plantillas=[_plantilla("DG", "marca", "¿Qué opinas de [MARCA_A]?")]), ficha, _marcas())
    assert res.prompts == []
    assert "no admite la instanciación" in res.descartados[0]["motivo"]


def test_el_codigo_rechaza_una_familia_desconocida(ficha) -> None:
    res = validate_bank(PropuestaBancoLLM(plantillas=[_plantilla("XX", "generico", "¿Qué academias hay?")]), ficha, _marcas())
    assert res.prompts == []
    assert "familia desconocida" in res.descartados[0]["motivo"]


def test_el_codigo_rechaza_una_plantilla_espontanea_que_nombra_una_marca(ficha) -> None:
    res = validate_bank(
        PropuestaBancoLLM(plantillas=[_plantilla("DG", "generico", "¿Es Academia Lingua Turia la mejor academia?")]),
        ficha,
        _marcas(),
    )
    assert res.prompts == []
    assert "nombra a" in res.descartados[0]["motivo"]


def test_una_plantilla_de_marca_o_par_si_puede_nombrar_marcas(ficha) -> None:
    res = validate_bank(
        PropuestaBancoLLM(plantillas=[_plantilla("VR", "marca", "¿Qué opinión de [MARCA_A] y Academia Lingua Turia?")]),
        ficha,
        _marcas(),
    )
    assert len(res.prompts) == 1


def test_el_codigo_rechaza_plantillas_repetidas(ficha) -> None:
    texto = "¿Qué academias de idiomas hay en España?"
    res = validate_bank(
        PropuestaBancoLLM(plantillas=[_plantilla("DG", "generico", texto), _plantilla("DP", "generico", texto)]),
        ficha,
        _marcas(),
    )
    assert len(res.prompts) == 1
    assert res.descartados[0]["motivo"] == "plantilla repetida"


def test_el_prompt_id_usa_el_formato_del_kit(ficha) -> None:
    res = validate_bank(PropuestaBancoLLM(plantillas=[_plantilla("DG", "generico", "¿Qué academias hay en España?")]), ficha, _marcas())
    assert [p.prompt_id for p in res.prompts] == ["ACA-DG-01"]
    assert ID_RX.match(res.prompts[0].prompt_id)


# ---------------------------------------------------------------- con el servidor falso


def test_ningun_prompt_espontaneo_nombra_una_marca(fake, ficha, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FAKE_OR_BANK_BAD", "1")
    marcas = _marcas()
    res = prompt_bank.propose_bank(ficha, marcas, study_dir=tmp_path, provider="openrouter")
    espontaneos = [p for p in res.prompts if p.instanciacion in ("generico", "ciudad")]
    for p in espontaneos:
        assert prompt_bank.names_brand(p.plantilla, marcas) is None
    assert res.descartados
    assert any("nombra a" in d["motivo"] for d in res.descartados)


def test_el_banco_del_servidor_falso_cubre_las_nueve_familias(fake, ficha, tmp_path: Path) -> None:
    res = prompt_bank.propose_bank(ficha, _marcas(), study_dir=tmp_path, provider="openrouter")
    assert missing_families(res.prompts) == []
    assert {p.prompt_id.split("-")[1] for p in res.prompts} == set(FAMILIAS)


def test_el_banco_se_guarda_con_las_columnas_del_kit(fake, ficha, tmp_path: Path) -> None:
    prompt_bank.propose_bank(ficha, _marcas(), study_dir=tmp_path, provider="openrouter")
    csv = tmp_path / "banco_prompts.csv"
    assert csv.exists()
    assert prompt_bank.banco_to_df(prompt_bank.read_banco_csv(csv), ficha.sector).columns.tolist() == prompt_bank.BANCO_COLUMNS


def test_el_modo_mock_cubre_las_nueve_familias(mock_env, ficha, tmp_path: Path) -> None:
    res = prompt_bank.propose_bank(ficha, _marcas(), study_dir=tmp_path, provider="mock")
    assert missing_families(res.prompts) == []
    assert res.descartados == []


# ---------------------------------------------------------------- instanciación


def test_la_instantiacion_generico_da_una_ejecucion_por_plantilla(ficha) -> None:
    bank = [_prompt("ACA-DG-01", "Descubrimiento genérico", "generico", "¿Qué academias hay?")]
    insts = instantiate(bank, _marcas(), ficha)
    assert len(insts) == 1
    assert insts[0].marcas_a_evaluar == [m.nombre for m in _marcas()]


def test_la_instantiacion_ciudad_da_una_ejecucion_por_ciudad(ficha) -> None:
    bank = [_prompt("ACA-LO-01", "Localización", "ciudad", "¿Qué academias hay en [CIUDAD]?")]
    insts = instantiate(bank, _marcas(), ficha)
    assert [i.ciudad for i in insts] == ["Valencia", "Alicante"]
    assert "Valencia" in insts[0].prompt


def test_la_instantiacion_ciudad_usa_como_mucho_tres_ciudades(ficha) -> None:
    ficha4 = ficha.model_copy(update={"ciudades": ["Valencia", "Alicante", "Castellón", "Elche"]})
    bank = [_prompt("ACA-LO-01", "Localización", "ciudad", "¿Qué academias hay en [CIUDAD]?")]
    insts = instantiate(bank, _marcas(), ficha4)
    assert len(insts) == prompt_bank.MAX_CIUDADES == 3


def test_la_instantiacion_marca_da_una_ejecucion_por_marca_foco(ficha) -> None:
    bank = [_prompt("ACA-VR-01", "Validación reputacional", "marca", "¿Qué opinión de [MARCA_A]?")]
    insts = instantiate(bank, _marcas(), ficha)
    assert [i.marcas_a_evaluar for i in insts] == [["Academia Lingua Turia"], ["Escuela Babel"], ["Idiomas Costa"]]
    assert "[MARCA_A]" not in insts[0].prompt


def test_la_instantiacion_par_usa_los_pares_estrategicos(ficha) -> None:
    pares = strategic_pairs(_marcas())
    assert len(pares) == 5
    bank = [_prompt("ACA-CM-01", "Comparación de marcas", "par", "¿[MARCA_A] o [MARCA_B]?")]
    insts = instantiate(bank, _marcas(), ficha)
    assert len(insts) == len(pares)
    assert all(len(i.marcas_a_evaluar) == 2 for i in insts)
    assert all("[MARCA_A]" not in i.prompt and "[MARCA_B]" not in i.prompt for i in insts)


def test_los_pares_estrategicos_no_superan_el_tope(ficha) -> None:
    muchas = _marcas() + [
        MarcaPropuesta(nombre=f"Extra {i}", nivel="foco", rol="competidor detectado") for i in range(8)
    ]
    assert len(strategic_pairs(muchas)) <= prompt_bank.MAX_PARES


def test_con_dos_ciudades_y_tres_foco_el_numero_de_ejecuciones_es_el_esperado(ficha) -> None:
    bank = [
        _prompt("ACA-DG-01", "Descubrimiento genérico", "generico", "¿Qué academias hay?"),
        _prompt("ACA-LO-01", "Localización", "ciudad", "¿Qué academias hay en [CIUDAD]?"),
        _prompt("ACA-VR-01", "Validación reputacional", "marca", "¿Qué opinión de [MARCA_A]?"),
        _prompt("ACA-CM-01", "Comparación de marcas", "par", "¿[MARCA_A] o [MARCA_B]?"),
    ]
    insts = instantiate(bank, _marcas(), ficha)
    assert len(insts) == 1 + 2 + 3 + 5
    assert len(insts) == 11


# ---------------------------------------------------------------- modo de referencia


def test_el_modo_referencia_devuelve_el_banco_del_kit_sin_red(kit_ficha, monkeypatch, tmp_path: Path) -> None:
    import requests

    def _no_red(*a, **kw):  # pragma: no cover - solo se llama si el modo referencia saliera a la red
        raise AssertionError("El modo de referencia no puede llamar a la red")

    monkeypatch.setattr(requests.sessions.Session, "request", _no_red)
    res = prompt_bank.propose_bank(kit_ficha, _marcas(), study_dir=tmp_path, reference=True)
    kit = prompt_bank.read_banco_csv(KIT_DIR / "banco_prompts.csv")
    assert len(res.prompts) == len(kit) == 25
    assert [p.plantilla for p in res.prompts] == [p.plantilla for p in kit]
    assert (tmp_path / "banco_prompts.csv").read_bytes() == (KIT_DIR / "banco_prompts.csv").read_bytes()


def test_el_banco_del_kit_tiene_una_prompt_por_prompt_id(kit_ficha) -> None:
    kit = prompt_bank.read_banco_csv(KIT_DIR / "banco_prompts.csv")
    ids = [p.prompt_id for p in kit]
    assert len(set(ids)) == len(ids)
    assert missing_families(kit) == []
    assert all(norm_name(p.instanciacion) == p.instanciacion for p in kit)
