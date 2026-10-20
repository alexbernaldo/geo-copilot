"""Tests de verificación numérica y de entidades sobre toda la documentación y la fortaleza H7 (F10/F16)."""

import json
from pathlib import Path

from geo.config import ROOT_DIR
from geo.metrics import build_brand_summary_metrics
from geo.orchestrator import Run
from geo.reviewer import ALLOWED_ENTITIES_TERMS, verify_entities, verify_numbers
from geo.writer import _ClientNarrativeLLM, _mock_client_narrative, write_client

DOC_FILES: tuple[str, ...] = (
    "README.md",
    "ARQUITECTURA.md",
    "docs/demo_guion.md",
    "RESUMEN_IMPLEMENTACION.md",
)


def _demo_context() -> dict:
    run = Run("demo")
    return {
        "metrics": json.loads((run.run_dir / "metrics.json").read_text(encoding="utf-8")),
        "tablas": run.load_tablas(),
        "hallazgos": run.load_hallazgos(),
        "plan": run.load_plan(),
        "ficha": run.load_ficha(),
        "revision": run.load_revision(),
        "market": run.load_market(),
    }


def test_all_project_docs_pass_verify_numbers_and_verify_entities() -> None:
    """Verifica que README.md, ARQUITECTURA.md, docs/demo_guion.md y RESUMEN_IMPLEMENTACION.md tengan 0 incidencias."""
    ctx = _demo_context()
    ficha = ctx["ficha"]

    for rel_path in DOC_FILES:
        doc_path: Path = ROOT_DIR / rel_path
        assert doc_path.exists(), f"Falta el documento: {rel_path}"
        texto = doc_path.read_text(encoding="utf-8")

        inc_num, verificadas, no_trazables = verify_numbers(texto, ctx)
        assert no_trazables == 0, f"Cifras no trazables en {rel_path}: {inc_num}"
        assert inc_num == [], f"Incidencias numéricas en {rel_path}: {inc_num}"
        assert verificadas > 0

        inc_ent = verify_entities(texto, ficha=ficha, plan=ctx["plan"])
        assert inc_ent == [], f"Incidencias de entidades en {rel_path}: {inc_ent}"


def test_verify_entities_allows_all_required_technical_and_medical_terms() -> None:
    """Un párrafo realista con todas las entidades permitidas por especificación produce 0 incidencias."""
    required_terms = {
        "España",
        "provincias",
        "LASIK",
        "PRK",
        "ICL",
        "GPTBot",
        "ClaudeBot",
        "PerplexityBot",
        "Google-Extended",
        "Schema.org",
        "MedicalClinic",
        "Physician",
        "MedicalProcedure",
        "FAQPage",
        "Wikidata",
        "Wikipedia",
        "Google",
        "ChatGPT",
        "Gemini",
        "Perplexity",
        "Claude",
    }
    assert required_terms.issubset(ALLOWED_ENTITIES_TERMS)

    ctx = _demo_context()
    parrafo_realista = (
        "En España y sus distintas provincias, Clínica Alborada Visión ofrece cirugía refractiva "
        "con técnicas LASIK, PRK e ICL en sus centros de Madrid y Barcelona. Para mejorar su "
        "presencia en ChatGPT, Gemini, Perplexity y Claude, el plan técnico habilita el rastreo de "
        "GPTBot, ClaudeBot, PerplexityBot y Google-Extended, despliega datos estructurados Schema.org "
        "(MedicalClinic, Physician, MedicalProcedure y FAQPage) y refuerza la entidad en Wikidata, "
        "Wikipedia y Google."
    )
    incidencias = verify_entities(parrafo_realista, ficha=ctx["ficha"])
    assert incidencias == []


def test_reputation_finding_is_strength_and_used_in_content_and_pr() -> None:
    """Comprueba que R6 tiene prioridad 2, genera una FORTALEZA para Alborada, no genera acciones de gestión reputacional y aparece siempre en el resumen ejecutivo."""
    ctx = _demo_context()
    hallazgos = ctx["hallazgos"]
    plan = ctx["plan"]
    run = Run("demo")
    prop = run.load_propuesta()

    rep_findings = [h for h in hallazgos if h.tipo == "reputacion"]
    assert len(rep_findings) == 1
    h_rep = rep_findings[0]
    assert h_rep.id == "H2"
    assert h_rep.prioridad == 2
    assert "fortaleza" in h_rep.titulo.lower()
    assert "reputación sólida cuando la nombran; el problema es la visibilidad espontánea" in h_rep.titulo.lower()
    assert "con tan buenas reseñas deberíamos salir recomendados" in h_rep.descripcion.lower()

    # Resumen ejecutivo incluye siempre la respuesta a la hipótesis del cliente sobre reputación vs visibilidad espontánea
    res_ejecutivo = prop.secciones["1. Resumen ejecutivo"].lower()
    assert "con tan buenas reseñas deberíamos salir recomendados" in res_ejecutivo
    assert "reputación sólida" in res_ejecutivo or "reputación es sólida" in res_ejecutivo

    # Ninguna acción del plan es de gestión de crisis reputacional ('reputacion_resenas')
    assert all(a.palanca != "reputacion_resenas" for a in plan.acciones)

    # El hallazgo de fortaleza reputacional se usa como argumento en acciones de contenido y PR (autoridad_terceros)
    linked_palancas = {
        a.palanca for a in plan.acciones if h_rep.id in a.hallazgos_relacionados
    }
    assert "contenido" in linked_palancas
    assert "autoridad_terceros" in linked_palancas


def test_verify_entities_blocks_saludaldia_and_revistaoftalmologica_in_text_and_plan() -> None:
    """Comprueba que verify_entities bloquea slugs de medios no catalogados sin extensión ('saludaldia', 'revistaoftalmologica') tanto en texto como en plan.json."""
    ctx = _demo_context()
    ficha = ctx["ficha"]
    plan = ctx["plan"]

    # 1. En texto libre sin extensión .example
    inc_txt = verify_entities(
        "Plan de PR digital en prensa de salud citada (diariosalud, saludaldia, revistaoftalmologica).",
        ficha=ficha,
    )
    assert len(inc_txt) >= 2
    joined_txt = " | ".join(i.texto.lower() for i in inc_txt)
    assert "saludaldia" in joined_txt
    assert "revistaoftalmologica" in joined_txt

    # 2. En plan.json (descripción, entregables y KPI de una acción)
    bad_action = plan.acciones[0].model_copy(
        update={
            "descripcion": "Publicar notas médicas en saludaldia y revistaoftalmologica.",
            "entregables": ["6 artículos en saludaldia"],
            "kpi": ">= 6 menciones en revistaoftalmologica",
        }
    )
    bad_plan = plan.model_copy(update={"acciones": [bad_action, *plan.acciones[1:]]})
    inc_plan = verify_entities("Texto limpio de prueba.", ficha=ficha, plan=bad_plan)
    assert len(inc_plan) >= 2
    joined_plan = " | ".join(i.texto.lower() for i in inc_plan)
    assert "saludaldia" in joined_plan
    assert "revistaoftalmologica" in joined_plan


def test_writer_rewrite_loop_fixes_numbers_entities_and_compliance_with_provider(monkeypatch) -> None:
    """Comprueba que el bucle de reescritura de write_client corrige cifras no trazables, entidades inventadas y promesas."""
    ctx = _demo_context()
    ficha = ctx["ficha"]
    tablas = ctx["tablas"]
    hallazgos = ctx["hallazgos"]
    plan = ctx["plan"]

    metrics_summary = build_brand_summary_metrics(tablas, marca_brief=ficha.marca)
    clean_narr = _mock_client_narrative(ficha, metrics_summary, plan)

    bad_narr = clean_narr.model_copy(
        update={
            "resumen_ejecutivo": (
                "Clínica Alborada Visión alcanza un 57,3 % de aparición frente a Instituto Oftalmológico Mirasierra "
                "en sevilla y garantizamos el primer puesto con 100% éxito."
            )
        }
    )

    call_count = {"n": 0}

    def fake_complete_json(*, schema, mock_builder=None, **kwargs):
        if schema is _ClientNarrativeLLM:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return bad_narr
            return clean_narr
        return mock_builder() if mock_builder is not None else None

    monkeypatch.setattr("geo.writer.complete_json", fake_complete_json)
    monkeypatch.setattr("geo.reviewer.complete_json", fake_complete_json)

    prop = write_client(
        ficha=ficha,
        tablas=tablas,
        hallazgos=hallazgos,
        plan=plan,
        run_id="test_rewrite",
        provider="anthropic",
        use_cache=False,
    )

    before_rev = prop.metadatos["revision_antes_reescritura"]
    after_narr_rev = prop.metadatos["revision_narrativa_despues_reescritura"]
    assert before_rev is not None
    assert after_narr_rev is not None
    assert before_rev["aprobado"] is False
    assert before_rev["cifras_verificadas"] == 55
    assert before_rev["cifras_no_trazables"] == 1
    before_types = {inc["tipo"] for inc in before_rev["incidencias"]}
    before_texts = " | ".join(inc["texto"].lower() for inc in before_rev["incidencias"])
    assert "cifra_no_trazable" in before_types
    assert "promesa_resultado" in before_types
    assert "mirasierra" in before_texts
    assert "sevilla" in before_texts

    assert prop.metadatos["iteraciones_reescritura"] == 1
    assert after_narr_rev["aprobado"] is True
    assert after_narr_rev["cifras_verificadas"] == 91
    assert after_narr_rev["cifras_no_trazables"] == 0
    assert after_narr_rev["incidencias"] == []

    assert prop.revision.aprobado is True
    assert prop.revision.cifras_no_trazables == 0
    assert prop.revision.cifras_verificadas == 578
    assert prop.revision.incidencias == []
