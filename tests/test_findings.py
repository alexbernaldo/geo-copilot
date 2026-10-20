"""Tests del motor de hallazgos (F6)."""

import math
import re

from geo.config import BRIEF_MD
from geo.detection import detect
from geo.findings import generate_findings
from geo.intake import load_brief
from geo.judge_rules import judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas
from geo.market import build_market, discover_uncataloged_brands
from geo.metrics import bundle


def _extract_numbers_from_text(text: str) -> list[float]:
    """Extrae todos los números (enteros o decimales) presentes en un texto."""
    matches = re.findall(r"\b\d+(?:[.,]\d+)?\b", text)
    return [float(m.replace(",", ".")) for m in matches]


def test_generate_findings_alborada_rules_and_traceability() -> None:
    """Comprueba estructura, trazabilidad de cifras y presencia de hallazgos clave para Alborada."""
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    catalogo = load_fuentes()
    df_det = detect(df_ej, marcas)
    evals = judge_rules(df_det, df_ej, marcas, catalogo)
    tablas = bundle(evals, df_ej, marcas)

    valid_ej_ids = set(df_ej["ejecucion_id"].astype(str).unique())

    hallazgos = generate_findings(tablas, ficha=None, contraste_mercado=None)
    assert 3 <= len(hallazgos) <= 7

    for idx, h in enumerate(hallazgos, start=1):
        assert h.id == f"H{idx}"
        assert h.prioridad == idx
        assert len(h.evidencias) >= 1

        allowed_numbers: set[float] = set()
        for ev in h.evidencias:
            assert ev.n > 0
            assert len(ev.ejecucion_ids) >= 1
            for eid in ev.ejecucion_ids:
                assert eid in valid_ej_ids, f"Ejecucion_ID inexistente: {eid}"
            allowed_numbers.add(float(ev.n))
            allowed_numbers.add(round(float(ev.valor), 2))
            allowed_numbers.add(round(float(ev.valor), 1))
            allowed_numbers.add(round(float(ev.valor), 0))

        nums_in_desc = _extract_numbers_from_text(h.descripcion)
        for num in nums_in_desc:
            assert any(
                math.isclose(num, allowed, abs_tol=1e-2) for allowed in allowed_numbers
            ), f"Cifra {num} en descripción de {h.id} no está en sus evidencias: {allowed_numbers}"

    # Comprobar que salen los hallazgos obligatorios de aceptación F6 para Alborada
    tipos = {h.tipo for h in hallazgos}
    assert "geografia" in tipos
    assert "motor" in tipos
    assert "competencia" in tipos
    assert "brief_vs_datos" in tipos

    all_text = " ".join(f"{h.titulo} {h.descripcion}" for h in hallazgos)
    assert "Barcelona" in all_text
    assert "ChatGPT" in all_text and "Claude" in all_text
    assert "Valdecruz" in all_text and "Tramuntana" in all_text
    assert "Vistalia" in all_text


def test_build_market_and_discover_uncataloged_f8() -> None:
    """Comprueba F8: Valdecruz con rol lider, Vistalia en no_declaradas_relevantes, cifras en discrepancias y descubrimiento N3."""
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    catalogo = load_fuentes()
    df_det = detect(df_ej, marcas)
    evals = judge_rules(df_det, df_ej, marcas, catalogo)
    tablas = bundle(evals, df_ej, marcas)
    ficha, _ = load_brief(BRIEF_MD, provider="mock")

    mercado = build_market(ficha, marcas, tablas, df_ej)
    assert len(mercado.marcas) == 10

    roles_by_name = {m.nombre: m.rol for m in mercado.marcas}
    assert roles_by_name["Grupo Hospitalario Valdecruz"] == "lider"
    assert roles_by_name["Clínica Alborada Visión"] == "marca_brief"
    assert roles_by_name["Instituto Oftálmico Tramuntana"] == "referencia"
    assert roles_by_name["Láser Nítida"] == "competidor_directo"
    assert roles_by_name["Vistalia Oftalmología"] == "competidor_directo"

    assert "Vistalia Oftalmología" in mercado.no_declaradas_relevantes
    assert len(mercado.discrepancias_brief) >= 2
    for disc in mercado.discrepancias_brief:
        assert re.search(r"\d", disc), f"La discrepancia no contiene ninguna cifra: {disc}"

    # En el kit no hay marcas no catalogadas
    assert discover_uncataloged_brands(df_ej, marcas) == []
