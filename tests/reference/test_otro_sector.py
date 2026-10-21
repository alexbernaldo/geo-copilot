"""Test de verificación de sector genérico (WB4):

Brief de academia de idiomas en Valencia + dataset de 12 ejecuciones y 2 motores
recorren el pipeline completo en modo mock sin errores y sin menciones a oftalmología en la propuesta.
"""

from pathlib import Path
import pytest
from geo.orchestrator import Run

ROOT = Path(__file__).resolve().parent.parent.parent
BRIEF_ACADEMIA = ROOT / "tests" / "fixtures" / "briefs" / "academia_idiomas.md"
STUDY_DIR = ROOT / "tests" / "fixtures" / "briefs" / "academia_idiomas"


def test_pipeline_sector_academia_idiomas_sin_menciones_oftalmologia(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_academia"
    run = Run(
        run_id="run_academia_test",
        brief_path=BRIEF_ACADEMIA,
        provider="mock",
        run_dir=run_dir,
        study_dir=STUDY_DIR,
    )
    res = run.run_all(auto_approve=True)
    assert res is not None
    assert run.state["steps"]["export"] == "done"

    propuesta_path = run_dir / "propuesta.json"
    assert propuesta_path.exists()
    prop_content = propuesta_path.read_text(encoding="utf-8").lower()

    # Comprobar que no hay restos del sector oftalmológico en la propuesta generada
    terminos_oftalmologia = [
        "oftalm", "catarat", "miop", "refractiv", "alborada", "valdecruz", "tramuntana"
    ]
    for termino in terminos_oftalmologia:
        assert termino not in prop_content, f"Se encontró el término oftalmológico '{termino}' en la propuesta de la academia"


def test_academia_propuesta_aprobada_y_sin_responsable_medico(tmp_path: Path) -> None:
    run = Run(
        modo="cliente",
        brief_path=BRIEF_ACADEMIA,
        provider="mock",
        run_dir=tmp_path / "run",
        study_dir=STUDY_DIR,
    )
    prop = run.run_all(auto_approve=True)
    assert prop is not None
    assert prop.revision.aprobado is True
    assert prop.revision.cifras_no_trazables == 0
    assert all(a.responsable != "cliente_medico" for a in prop.plan.acciones)
