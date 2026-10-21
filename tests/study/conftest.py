"""Fixtures de los tests del estudio en vivo: servidor falso de OpenRouter en un puerto libre y bloqueo de red."""

from __future__ import annotations

import importlib.util
import threading
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import pytest
import requests

from geo.schemas import FichaMarca

ROOT = Path(__file__).resolve().parents[2]
KIT_DIR = ROOT / "geo" / "reference_data"


def _load_fake_module():
    spec = importlib.util.spec_from_file_location("fake_openrouter", ROOT / "scripts" / "fake_openrouter.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _no_external_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ningún test del estudio puede salir a Internet: solo se permite 127.0.0.1."""
    orig = requests.sessions.Session.request

    def guarded(self, method, url, *a, **kw):
        host = urlparse(str(url)).hostname
        if host not in ("127.0.0.1", "localhost"):
            raise AssertionError(f"Llamada de red no permitida en tests: {url}")
        return orig(self, method, url, *a, **kw)

    monkeypatch.setattr(requests.sessions.Session, "request", guarded)


@pytest.fixture(scope="session")
def fake_module():
    return _load_fake_module()


@pytest.fixture(scope="session")
def fake_server(fake_module) -> Iterator[str]:
    httpd = fake_module.make_server(0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def fake(fake_server: str, fake_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    """Apunta el cliente de OpenRouter al servidor falso, con cachés en carpetas temporales y sin esperas."""
    import time

    import geo.engines.openrouter_engine as eng
    import geo.llm as llm
    import geo.openrouter as orc
    import geo.study.sources as sources

    fake_module.reset_state()
    monkeypatch.delenv("FAKE_OR_FAIL", raising=False)
    monkeypatch.delenv("FAKE_OR_BANK_BAD", raising=False)
    monkeypatch.setenv("OPENROUTER_BASE_URL", fake_server)
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-falsa-de-test")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("MAX_BUDGET_EUR", "50")
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "cache_llm")
    monkeypatch.setattr(eng, "CACHE_DIR", tmp_path / "cache_engines")
    monkeypatch.setattr(sources, "global_cache_path", lambda: tmp_path / "cache_dominios" / "dominios.json")
    monkeypatch.setenv("GEO_DATA_DIR", "")
    monkeypatch.setitem(orc._models_cache, "data", None)
    monkeypatch.setitem(orc._models_cache, "ts", 0.0)
    monkeypatch.setattr(time, "sleep", lambda *_a, **_k: None)
    llm.reset_llm_stats()
    return fake_server


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import geo.llm as llm

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "cache_llm")
    llm.reset_llm_stats()


@pytest.fixture
def ficha() -> FichaMarca:
    """Ficha de una academia de idiomas de Valencia (sector distinto al del kit)."""
    return FichaMarca(
        marca="Academia Lingua Turia",
        web="https://www.linguaturia.example/",
        sector="Academia de idiomas",
        servicios=["inglés", "alemán", "preparación de exámenes"],
        servicios_prioritarios=["clases de inglés"],
        publicos=["adultos", "familias"],
        ciudades=["Valencia", "Alicante"],
        ciudad_principal="Valencia",
        competidores_declarados=["Escuela Babel", "Idiomas Costa", "Centro Polilingüe"],
        objetivo_principal="Ser la academia más recomendada de Valencia",
    )


@pytest.fixture
def kit_ficha() -> FichaMarca:
    """Ficha de la marca del kit, que dispara el modo referencia."""
    return FichaMarca(
        marca="Clínica Alborada Visión",
        web="https://alboradavision.example/",
        sector="Clínicas privadas (oftalmología)",
        servicios=["cirugía refractiva", "cataratas", "retina"],
        servicios_prioritarios=["cirugía refractiva"],
        publicos=["adultos", "deportistas"],
        ciudades=["Valencia", "Madrid", "Barcelona"],
        ciudad_principal="Valencia",
        competidores_declarados=["Instituto Oftálmico Tramuntana"],
        objetivo_principal="Ser la clínica oftalmológica de referencia en Valencia",
    )


@pytest.fixture
def kit_files() -> dict[str, Path]:
    return {
        "ejecuciones": KIT_DIR / "ejecuciones.csv",
        "marcas": KIT_DIR / "marcas.csv",
        "banco_prompts": KIT_DIR / "banco_prompts.csv",
        "fuentes_catalogo": KIT_DIR / "fuentes_catalogo.csv",
        "muestra_evaluada": KIT_DIR / "muestra_evaluada.csv",
    }
