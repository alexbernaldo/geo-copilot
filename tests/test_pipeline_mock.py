"""Tests de integración del pipeline completo en modo mock (F12)."""

import json
import time

from geo.config import BRIEF_MD
from geo.orchestrator import PIPELINE_STEPS, Run


def test_full_pipeline_mock_under_60s(tmp_path) -> None:
    """Con LLM_PROVIDER=mock, el pipeline completo sobre el brief de ejemplo termina en < 60 s y genera salidas y trazas."""
    t0 = time.perf_counter()
    run = Run(
        run_id="test_mock_run",
        modo="cliente",
        brief_path=BRIEF_MD,
        provider="mock",
        runs_root=tmp_path,
    )
    propuesta = run.run_all(auto_approve=True, force=True)
    elapsed = time.perf_counter() - t0

    assert elapsed < 60.0
    assert propuesta is not None
    assert propuesta.revision.aprobado is True
    assert propuesta.revision.cifras_no_trazables == 0

    # Comprobar propuesta_cliente.docx
    docx_file = run.run_dir / "propuesta_cliente.docx"
    assert docx_file.exists()

    # Comprobar state.json todo en done
    state_data = json.loads(run.state_path.read_text(encoding="utf-8"))
    for step in PIPELINE_STEPS:
        assert state_data["steps"].get(step) == "done", f"Paso {step} no está en done"
    assert all(state_data["checkpoints"].values())

    # Comprobar trace.jsonl con al menos un registro por paso
    traces = run.read_traces()
    traced_steps = {t["step"] for t in traces}
    assert set(PIPELINE_STEPS).issubset(traced_steps)
    for t in traces:
        assert "duration_s" in t
        assert "input_hash" in t
        assert "output_path" in t

    # Comprobar idempotencia en segunda llamada sin force (0 registros nuevos en trace.jsonl)
    n_traces_before = len(run.read_traces())
    run.run_all(auto_approve=True, force=False)
    assert len(run.read_traces()) == n_traces_before
