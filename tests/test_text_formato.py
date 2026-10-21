"""Formato es-ES de las cifras de la propuesta (`geo.text.formato_es`)."""

import pytest

from geo.reviewer import verify_numbers
from geo.text import formato_es


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("inversión de **24,300 €** (18,000 € – 27,000 €)", "inversión de **24.300 €** (18.000 € – 27.000 €)"),
        ("score de 27.97 y un 38.8 % de aparición", "score de 27,97 y un 38,8 % de aparición"),
        ("41.2% de las respuestas", "41,2 % de las respuestas"),
        ("| Perplexity | 60 | 65.0 % | 2.44 | 49.08 |", "| Perplexity | 60 | 65,0 % | 2,44 | 49,08 |"),
        ("valor 0.3875 y fuerza -0.33", "valor 0,3875 y fuerza -0,33"),
        ("Fin de frase con 75.02.", "Fin de frase con 75,02."),
    ],
)
def test_convierte_formato_ingles(entrada: str, esperado: str) -> None:
    assert formato_es(entrada) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "4,7 sobre 5 con 1.800 opiniones y 7.500 intervenciones",
        "kappa 0,479 y 1.258.134 tokens",
        "EJ-0001, anthropic/claude-sonnet-4.5, gpt-4.1, 2026-10-21, schema.org",
        "A4 | S4–S5 (2 sem.) | 550 € | H3, H7",
    ],
)
def test_respeta_espanol_e_identificadores(texto: str) -> None:
    assert formato_es(texto) == texto


def test_el_revisor_sigue_trazando_las_cifras() -> None:
    contexto = {"coste": 24300.0, "score": 27.97, "tasa": 0.388}
    _, verificadas, no_trazables = verify_numbers(formato_es("Plan de 24,300 €, score 27.97 y 38.8 %."), contexto)
    assert (verificadas, no_trazables) == (3, 0)
