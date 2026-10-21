"""Tests de la detección del modo de referencia (B1.4 que no dependen de la API)."""

from pathlib import Path

import pytest

from geo.intake import read_brief_text
from geo.reference import (
    REFERENCE_DIR,
    REFERENCE_FINGERPRINTS,
    compute_reference_fingerprints,
    detect_reference,
)

BRIEF_MD = REFERENCE_DIR / "Brief_de_ejemplo_Clinica_Alborada.md"
BRIEF_DOCX = REFERENCE_DIR / "Brief_de_ejemplo_Clinica_Alborada.docx"
EJEC = REFERENCE_DIR / "ejecuciones.csv"


def _detect(brief=None, csv=None, brand=None, domain=None):
    return detect_reference(brief_text=brief, csv_paths=csv, prospect_brand=brand, prospect_domain=domain)


def test_huellas_coinciden_con_la_constante() -> None:
    assert compute_reference_fingerprints() == REFERENCE_FINGERPRINTS


def test_brief_md_es_referencia() -> None:
    assert _detect(brief=read_brief_text(BRIEF_MD)) == (True, "huella_brief")


def test_brief_docx_es_referencia() -> None:
    assert _detect(brief=read_brief_text(BRIEF_DOCX)) == (True, "huella_brief")


def test_brief_con_frase_cambiada_cae_a_marca() -> None:
    texto = read_brief_text(BRIEF_MD) + "\nFrase añadida por el consultor."
    assert _detect(brief=texto) == (True, "marca")


def test_brief_de_otra_marca_no_es_referencia() -> None:
    texto = "# Brief\nAcademia Lingua, enseñanza de idiomas en Valencia. Web: lingua-valencia.example"
    assert _detect(brief=texto) == (False, "")


def test_csv_del_kit_con_brief_distinto_es_referencia() -> None:
    assert _detect(brief="Academia Lingua en Valencia", csv={"ejecuciones": EJEC}) == (True, "huella_datos")


def test_prospecto_del_kit_sin_datos_es_referencia() -> None:
    assert _detect(brand="Vistalia Oftalmología")[0] is True
    assert _detect(domain="vistalia-oftalmologia.example")[0] is True


def test_prospecto_del_kit_con_datos_ajenos_no_es_referencia(tmp_path: Path) -> None:
    ajeno = tmp_path / "ejecuciones.csv"
    ajeno.write_text("Ejecucion_ID,Motor\nE1,ChatGPT\n", encoding="utf-8-sig")
    assert _detect(brand="Vistalia Oftalmología", csv={"ejecuciones": ajeno}) == (False, "")


@pytest.mark.parametrize("brand", ["Academia Lingua", ""])
def test_prospecto_ajeno_no_es_referencia(brand: str) -> None:
    assert _detect(brand=brand) == (False, "")
