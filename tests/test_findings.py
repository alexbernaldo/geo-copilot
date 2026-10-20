"""Tests del motor de hallazgos (F6)."""

import math
import re

from geo.detection import detect
from geo.findings import generate_findings
from geo.judge_rules import judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas
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
