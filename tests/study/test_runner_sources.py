"""WC3 y WC4 · Runner del estudio, estimación, clasificación de fuentes y motor de OpenRouter."""

from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path

import pandas as pd
import pytest

from geo import llm, loader
from geo.config import SOURCE_QUALITY_BY_TYPE
from geo.engines import openrouter_engine as eng
from geo.schemas import FichaMarca, Prompt
from geo.study import brands as B
from geo.study import prompt_bank as PB
from geo.study import runner as R
from geo.study import sources as S
from geo.study.common import EJECUCIONES_COLUMNS

KIT = Path(__file__).resolve().parents[2] / "geo" / "reference_data"


def _bank() -> list[Prompt]:
    mk = lambda n, t: Prompt(  # noqa: E731
        prompt_id=f"ACA-DG-0{n}", familia="Descubrimiento genérico", intencion="Descubrimiento",
        prioridad="P1", uso="Publicable", instanciacion="generico", plantilla=t,
    )
    return [mk(1, "¿Qué academias de inglés recomiendas en España?"), mk(2, "¿Dónde aprender alemán con buen nivel?")]


@pytest.fixture
def setup(fake: str, ficha: FichaMarca, tmp_path: Path):
    marcas = B.validate_brands(B.mock_proposal(ficha), ficha).marcas
    # los motores falsos citan estas marcas
    req = urllib.request.Request(
        fake + "/_config",
        data=json.dumps({"marcas": [{"nombre": m.nombre, "dominio": m.dominio} for m in marcas]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req).read()
    study = tmp_path / "study"
    study.mkdir()
    return marcas, study


CFG = R.StudyConfig(tamano="estandar", motores=["ChatGPT", "Perplexity"], repeticiones=2)


def test_runner_8_filas_formato_kit(setup, ficha: FichaMarca) -> None:
    marcas, study = setup
    progreso: list[tuple[str, int, int]] = []
    res = R.run_study(_bank(), marcas, ficha, CFG, study, reference=False, on_progress=lambda *a: progreso.append(a))
    df = pd.read_csv(study / "ejecuciones.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    assert list(df.columns) == EJECUCIONES_COLUMNS
    assert len(df) == 8 == res.filas == res.total
    assert df["Ejecucion_ID"].tolist() == [f"EJ-000{i}" for i in range(1, 9)]
    assert set(df["Motor"]) == {"ChatGPT", "Perplexity"} and set(df["Repetición"]) == {"1", "2"}
    assert (df["Fuentes citadas"] != "").all() and df["Respuesta completa"].str.contains("Academia Lingua Turia|Escuela Babel").all()
    assert (study / "study_dummy").exists() is False
    assert (study / "banco_prompts.csv").exists() is False
    assert progreso[0] == ("consultas", 0, 8) and progreso[-1] == ("consultas", 8, 8)
    meta = [json.loads(x) for x in (study / "ejecuciones_meta.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(meta) == 8 and meta[0]["modelo"] and meta[0]["coste_usd"] == 0.0012
    assert res.llamadas_reales == 8 and res.coste_real and res.coste_eur > 0
    # el motor lee el CSV sin errores
    PB.write_banco_csv(study, _bank(), ficha.sector)
    B.write_marcas_csv(study, marcas)
    ej = loader.load_ejecuciones(path=study / "ejecuciones.csv", prompts_path=study / "banco_prompts.csv")
    assert len(ej) == 8 and ej["espontanea"].all()
    assert ej.loc[0, "marcas_a_evaluar"] == [m.nombre for m in marcas]


def test_runner_cache_evita_pagar_dos_veces(setup, ficha: FichaMarca) -> None:
    marcas, study = setup
    R.run_study(_bank(), marcas, ficha, CFG, study, reference=False)
    res2 = R.run_study(_bank(), marcas, ficha, CFG, study, reference=False)
    assert res2.cache_hits == 8 and res2.llamadas_reales == 0 and res2.coste_eur == 0


def test_runner_429_once_termina_bien(setup, ficha: FichaMarca, monkeypatch: pytest.MonkeyPatch) -> None:
    marcas, study = setup
    monkeypatch.setenv("FAKE_OR_FAIL", "429_once")
    res = R.run_study(_bank(), marcas, ficha, CFG, study, reference=False)
    assert res.filas == 8 and not res.fallos


def test_runner_500_always_termina_en_error(setup, ficha: FichaMarca, monkeypatch: pytest.MonkeyPatch) -> None:
    marcas, study = setup
    monkeypatch.setenv("FAKE_OR_FAIL", "500_always")
    with pytest.raises(R.StudyFailedError) as exc:
        R.run_study(_bank(), marcas, ficha, CFG, study, reference=False)
    assert len(exc.value.fallos) > 0.2 * 8
    assert not (study / "ejecuciones.csv").exists()


def test_runner_error_no_recuperable(setup, ficha: FichaMarca, monkeypatch: pytest.MonkeyPatch) -> None:
    marcas, study = setup
    monkeypatch.setenv("FAKE_OR_FAIL", "402")
    with pytest.raises(llm.LLMConfigError):
        R.run_study(_bank(), marcas, ficha, CFG, study, reference=False)


def test_runner_tope_de_gasto(setup, ficha: FichaMarca) -> None:
    marcas, study = setup
    with pytest.raises(llm.LLMCallLimitError):
        R.run_study(_bank(), marcas, ficha, CFG, study, reference=False, max_budget_eur=0.0000001, concurrency=1)
    # lo ya pagado queda en caché: reanudar con presupuesto suficiente no repite llamadas
    res = R.run_study(_bank(), marcas, ficha, CFG, study, reference=False, concurrency=1)
    assert res.filas == 8 and res.cache_hits >= 1


def test_runner_cancelacion(setup, ficha: FichaMarca) -> None:
    marcas, study = setup
    ev = threading.Event()

    def prog(paso: str, hechos: int, total: int) -> None:
        if hechos >= 3:
            ev.set()

    with pytest.raises(R.StudyCancelled):
        R.run_study(_bank(), marcas, ficha, CFG, study, reference=False, on_progress=prog, cancel=ev, concurrency=1)


def test_runner_proveedor_mock_sin_red(mock_env: None, ficha: FichaMarca, tmp_path: Path) -> None:
    marcas = B.validate_brands(B.mock_proposal(ficha), ficha).marcas
    res = R.run_study(_bank(), marcas, ficha, CFG, tmp_path, reference=False)
    assert res.filas == 8 and res.coste_eur == 0 and res.llamadas_reales == 0


def test_runner_referencia_copia_el_kit_sin_red(mock_env: None, tmp_path: Path) -> None:
    f = FichaMarca(marca="Clínica Alborada Visión", sector="Oftalmología", objetivo_principal="x")
    pr: list[tuple[str, int, int]] = []
    res = R.run_study([], [], f, CFG, tmp_path, on_progress=lambda *a: pr.append(a))
    assert res.filas == 624 and res.coste_eur == 0 and pr == [("consultas", 624, 624)]
    assert (tmp_path / "ejecuciones.csv").read_bytes() == (KIT / "ejecuciones.csv").read_bytes()


def test_estimate_study_kit(fake: str) -> None:
    banco = PB.read_banco_csv(KIT / "banco_prompts.csv")
    marcas = B.read_marcas_csv(KIT / "marcas.csv")
    f = FichaMarca(marca="Clínica Alborada Visión", sector="x", objetivo_principal="o", ciudades=["Madrid", "Barcelona"])
    std = R.estimate_study(banco, marcas, f, R.preset("estandar"))
    assert std.pasos[0].llamadas == 416 and std.total_eur > 0 and not std.supera_tope
    comp = R.estimate_study(banco, marcas, f, R.preset("completo"))
    assert comp.pasos[0].llamadas == 624 and comp.total_eur > std.total_eur
    rap = R.estimate_study(banco, marcas, f, R.preset("rapido"))
    assert rap.pasos[0].llamadas < 416
    assert std.minutos > 0 and std.total_llamadas >= 416


def test_estimate_supera_tope(fake: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_BUDGET_EUR", "0.5")
    banco = PB.read_banco_csv(KIT / "banco_prompts.csv")
    marcas = B.read_marcas_csv(KIT / "marcas.csv")
    f = FichaMarca(marca="X", sector="x", objetivo_principal="o", ciudades=["Madrid"])
    est = R.estimate_study(banco, marcas, f, R.preset("completo"))
    assert est.supera_tope and est.tope_eur == 0.5


# ---------------------------------------------------------------- motor


def test_engine_run_citas_y_cache(fake: str) -> None:
    r = eng.run("ChatGPT", "¿Qué academias recomiendas?", 1)
    assert r.texto and r.urls and r.dominios and not r.cached
    assert all(not d.startswith("www.") for d in r.dominios)
    assert eng.run("ChatGPT", "¿Qué academias recomiendas?", 1).cached
    assert not eng.run("ChatGPT", "¿Qué academias recomiendas?", 2).cached
    p = eng.run("Perplexity", "¿Qué academias recomiendas?", 1)
    assert p.dominios and p.model.startswith("perplexity/")


def test_engine_mock_determinista() -> None:
    a = eng.mock_run("Claude", "hola", 1, ["A", "B", "C"])
    assert a == eng.mock_run("Claude", "hola", 1, ["A", "B", "C"]) and a.simulado


# ---------------------------------------------------------------- fuentes


def _write_ej(study: Path, fuentes: list[str]) -> None:
    rows = [
        {c: "" for c in EJECUCIONES_COLUMNS} | {"Ejecucion_ID": f"E{i}", "Fuentes citadas": f}
        for i, f in enumerate(fuentes)
    ]
    pd.DataFrame(rows, columns=EJECUCIONES_COLUMNS).to_csv(study / "ejecuciones.csv", index=False, encoding="utf-8-sig")


def test_clasificar_fuentes(fake: str, ficha: FichaMarca, tmp_path: Path) -> None:
    marcas = B.validate_brands(B.mock_proposal(ficha), ficha).marcas
    _write_ej(
        tmp_path,
        ["linguaturia.example, diario-economia.example", "blog.linguaturia.example, opiniones-clientes.example", ""],
    )
    cache = tmp_path / "dominios.json"
    res = S.classify_sources(tmp_path, marcas, reference=False, cache_path=cache)
    cat = pd.read_csv(tmp_path / "fuentes_catalogo.csv", encoding="utf-8-sig", dtype=str).set_index("Dominio")
    assert cat.loc["linguaturia.example", "Tipo_de_fuente"] == "Web propia"
    assert cat.loc["blog.linguaturia.example", "Tipo_de_fuente"] == "Web propia"
    assert cat.loc["diario-economia.example", "Tipo_de_fuente"] == "Medio"
    assert cat.loc["opiniones-clientes.example", "Tipo_de_fuente"] == "Plataforma de reseñas"
    for d, row in cat.iterrows():
        assert float(row["Calidad_de_fuente_0_1"]) == SOURCE_QUALITY_BY_TYPE[row["Tipo_de_fuente"]]
    assert res.web_propia == 2 and res.clasificados_llm == 2
    # caché global: el segundo proyecto no llama al LLM
    assert set(json.loads(cache.read_text(encoding="utf-8"))) == {"diario-economia.example", "opiniones-clientes.example"}
    t2 = tmp_path / "otro"
    t2.mkdir()
    _write_ej(t2, ["diario-economia.example"])
    llm.reset_llm_stats()
    r2 = S.classify_sources(t2, marcas, reference=False, cache_path=cache)
    assert r2.desde_cache == 1 and llm.get_llm_stats()["calls"] == 0
    # el catálogo del kit se carga con el loader
    assert "diario-economia.example" in loader.load_fuentes(tmp_path / "fuentes_catalogo.csv")


def test_clasificar_fuentes_respeta_catalogo_existente(mock_env: None, ficha: FichaMarca, tmp_path: Path) -> None:
    (tmp_path / "fuentes_catalogo.csv").write_text(
        "Dominio,Tipo_de_fuente,Calidad_de_fuente_0_1\nviejo.example,Medio,0.9\n", encoding="utf-8-sig"
    )
    _write_ej(tmp_path, ["viejo.example, nuevo-foro.example"])
    S.classify_sources(tmp_path, [], reference=False, cache_path=tmp_path / "c.json")
    cat = pd.read_csv(tmp_path / "fuentes_catalogo.csv", encoding="utf-8-sig", dtype=str).set_index("Dominio")
    assert cat.loc["viejo.example", "Tipo_de_fuente"] == "Medio"
    assert cat.loc["nuevo-foro.example", "Tipo_de_fuente"] == "Red social / foro"
    assert not (tmp_path / "c.json").exists()  # lo heurístico del modo mock no contamina la caché global


def test_fuentes_referencia_copia_catalogo(mock_env: None, tmp_path: Path) -> None:
    res = S.classify_sources(tmp_path, [], ficha_marca="Clínica Alborada Visión")
    assert (tmp_path / "fuentes_catalogo.csv").read_bytes() == (KIT / "fuentes_catalogo.csv").read_bytes()
    assert res.total_dominios == 25
