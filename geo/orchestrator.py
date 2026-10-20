"""Orquestador del pipeline GEO, gestión de estado, checkpoints humanos y trazas (F12)."""

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Literal

import pandas as pd

from geo.budget import validate_and_adjust_plan
from geo.config import BRIEF_MD, LLM_MODEL, LLM_PROVIDER, RUNS_DIR
from geo.detection import detect
from geo.export import export_docx, export_md
from geo.findings import generate_findings
from geo.intake import load_brief
from geo.judge import judge_ensemble
from geo.judge_rules import judge_rules
from geo.llm import get_llm_stats
from geo.loader import load_ejecuciones, load_fuentes, load_marcas
from geo.market import build_market
from geo.metrics import build_brand_summary_metrics, bundle
from geo.reviewer import compliance
from geo.schemas import (
    ContrasteMercado,
    FichaMarca,
    Hallazgo,
    InformeRevision,
    Plan,
    Propuesta,
)
from geo.strategy import build_plan
from geo.writer import build_default_prospect_ficha as _prospect_ficha, write_client, write_prospect

StepStatus = Literal["pending", "done", "error", "awaiting_human"]

PIPELINE_STEPS: tuple[str, ...] = (
    "intake",
    "market",
    "detect",
    "judge",
    "metrics",
    "findings",
    "plan",
    "review",
    "write",
    "export",
)

CHECKPOINT_AFTER_STEP: dict[str, str] = {
    "intake": "checkpoint_0_brief",
    "market": "checkpoint_1_competidores",
    "findings": "checkpoint_2_hallazgos",
    "plan": "checkpoint_3_plan",
}


def _hash_obj(obj: Any) -> str:
    """Calcula un hash corto SHA-256 sobre cualquier estructura serializable."""
    raw = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


class Run:
    """Gestiona una ejecución del pipeline GEO con estado persistente en `runs/<run_id>/`."""

    def __init__(
        self,
        run_id: str | None = None,
        *,
        modo: Literal["cliente", "prospecto"] = "cliente",
        brief_path: str | Path | None = None,
        marca_prospecto: str | None = None,
        provider: str | None = None,
        runs_root: Path = RUNS_DIR,
    ) -> None:
        self.modo: Literal["cliente", "prospecto"] = modo
        self.brief_path: Path = Path(brief_path) if brief_path else BRIEF_MD
        self.marca_prospecto: str | None = marca_prospecto
        self.provider: str = (
            provider or os.getenv("LLM_PROVIDER", LLM_PROVIDER) or "mock"
        ).strip().lower()

        if run_id is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            seed = f"{ts}|{self.modo}|{self.brief_path}|{self.marca_prospecto}"
            h = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:6]
            run_id = f"{ts}_{h}"

        self.run_id: str = run_id
        self.run_dir: Path = runs_root / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.state_path: Path = self.run_dir / "state.json"
        self.trace_path: Path = self.run_dir / "trace.jsonl"

        self.state: dict[str, Any] = self._load_or_init_state()

    def _load_or_init_state(self) -> dict[str, Any]:
        """Carga `state.json` si existe o inicializa todos los pasos en `pending`."""
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        initial = {
            "run_id": self.run_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "modo": self.modo,
            "provider": self.provider,
            "brief_path": str(self.brief_path),
            "marca_prospecto": self.marca_prospecto,
            "steps": {s: "pending" for s in PIPELINE_STEPS},
            "checkpoints": {
                "checkpoint_0_brief": False,
                "checkpoint_1_competidores": False,
                "checkpoint_2_hallazgos": False,
                "checkpoint_3_plan": False,
            },
            "human_approvals": [],
        }
        self._save_state(initial)
        return initial

    def _save_state(self, state: dict[str, Any] | None = None) -> None:
        """Persiste `state.json` en disco."""
        target = state if state is not None else self.state
        self.state_path.write_text(
            json.dumps(target, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set_step_status(self, step: str, status: StepStatus) -> None:
        """Actualiza y guarda el estado de un paso."""
        self.state["steps"][step] = status
        self._save_state()

    def approve_checkpoint(self, checkpoint_name: str, note: str = "Aprobado") -> None:
        """Marca un checkpoint humano como aprobado y deja registro en `human_approvals`."""
        self.state.setdefault("checkpoints", {})[checkpoint_name] = True
        self.state.setdefault("human_approvals", []).append(
            {
                "checkpoint": checkpoint_name,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "note": note,
            }
        )
        for step, ck in CHECKPOINT_AFTER_STEP.items():
            if ck == checkpoint_name and self.state["steps"].get(step) == "awaiting_human":
                self.state["steps"][step] = "done"
        self._save_state()

    def _append_trace(self, entry: dict[str, Any]) -> None:
        """Añade una línea JSON al archivo `trace.jsonl`."""
        with self.trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_traces(self) -> list[dict[str, Any]]:
        """Lee todos los registros de `trace.jsonl`."""
        if not self.trace_path.exists():
            return []
        lines = [
            ln.strip()
            for ln in self.trace_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        return [json.loads(ln) for ln in lines]

    # ---------- Lectores y escritores de artefactos intermedios ----------
    def load_ficha(self) -> FichaMarca:
        return FichaMarca.model_validate_json(
            (self.run_dir / "ficha.json").read_text(encoding="utf-8")
        )

    def save_ficha(self, ficha: FichaMarca) -> Path:
        p = self.run_dir / "ficha.json"
        p.write_text(ficha.model_dump_json(indent=2), encoding="utf-8")
        return p

    def load_market(self) -> ContrasteMercado:
        return ContrasteMercado.model_validate_json(
            (self.run_dir / "market.json").read_text(encoding="utf-8")
        )

    def save_market(self, market: ContrasteMercado) -> Path:
        p = self.run_dir / "market.json"
        p.write_text(market.model_dump_json(indent=2), encoding="utf-8")
        return p

    def load_hallazgos(self) -> list[Hallazgo]:
        raw = json.loads((self.run_dir / "findings.json").read_text(encoding="utf-8"))
        return [Hallazgo.model_validate(item) for item in raw]

    def save_hallazgos(self, hallazgos: list[Hallazgo]) -> Path:
        p = self.run_dir / "findings.json"
        p.write_text(
            json.dumps([h.model_dump(mode="json") for h in hallazgos], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return p

    def load_plan(self) -> Plan:
        return Plan.model_validate_json(
            (self.run_dir / "plan.json").read_text(encoding="utf-8")
        )

    def save_plan(self, plan: Plan) -> Path:
        p = self.run_dir / "plan.json"
        p.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        return p

    def load_revision(self) -> InformeRevision:
        return InformeRevision.model_validate_json(
            (self.run_dir / "revision.json").read_text(encoding="utf-8")
        )

    def load_propuesta(self) -> Propuesta:
        return Propuesta.model_validate_json(
            (self.run_dir / "propuesta.json").read_text(encoding="utf-8")
        )

    def load_tablas(self) -> dict[str, pd.DataFrame]:
        tablas_dir = self.run_dir / "tablas"
        tablas: dict[str, pd.DataFrame] = {}
        if tablas_dir.exists():
            for pq in sorted(tablas_dir.glob("*.parquet")):
                df_t = pd.read_parquet(pq)
                if "evidencia_ids" in df_t.columns:
                    df_t["evidencia_ids"] = df_t["evidencia_ids"].apply(
                        lambda x: list(x) if hasattr(x, "__iter__") and not isinstance(x, str) else []
                    )
                tablas[pq.stem] = df_t
        return tablas

    # ---------- Ejecución de pasos ----------
    def _run_tracked_step(
        self,
        step: str,
        output_file: Path,
        prompt_version: str,
        input_hash: str,
        fn,
        fallback_fn=None,
        *,
        force: bool = False,
    ) -> None:
        """Ejecuta un paso de forma idempotente, registrando tiempos, tokens, degradación y estado."""
        if (
            not force
            and self.state["steps"].get(step) == "done"
            and output_file.exists()
        ):
            return

        before_stats = get_llm_stats()
        t0 = time.perf_counter()
        started_at = datetime.now().isoformat(timespec="seconds")
        degradado = False
        err_msg: str | None = None

        try:
            fn()
        except Exception as exc:
            if fallback_fn is not None:
                degradado = True
                err_msg = f"Degradado a reglas/mock por error: {exc}"
                fallback_fn()
            else:
                self.set_step_status(step, "error")
                after_stats = get_llm_stats()
                self._append_trace(
                    {
                        "step": step,
                        "started_at": started_at,
                        "finished_at": datetime.now().isoformat(timespec="seconds"),
                        "duration_s": round(time.perf_counter() - t0, 4),
                        "input_hash": input_hash,
                        "output_path": str(output_file.relative_to(self.run_dir)),
                        "llm_calls": after_stats["calls"] - before_stats["calls"],
                        "cache_hits": after_stats["cache_hits"] - before_stats["cache_hits"],
                        "tokens_in": after_stats["tokens_in"] - before_stats["tokens_in"],
                        "tokens_out": after_stats["tokens_out"] - before_stats["tokens_out"],
                        "estimated_cost_eur": round(
                            after_stats["estimated_cost_eur"] - before_stats["estimated_cost_eur"],
                            6,
                        ),
                        "prompt_version": prompt_version,
                        "model": os.getenv("LLM_MODEL", LLM_MODEL) or self.provider,
                        "degradado": degradado,
                        "error": str(exc),
                    }
                )
                raise

        after_stats = get_llm_stats()
        self.set_step_status(step, "done")
        self._append_trace(
            {
                "step": step,
                "started_at": started_at,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "duration_s": round(time.perf_counter() - t0, 4),
                "input_hash": input_hash,
                "output_path": str(output_file.relative_to(self.run_dir)),
                "llm_calls": after_stats["calls"] - before_stats["calls"],
                "cache_hits": after_stats["cache_hits"] - before_stats["cache_hits"],
                "tokens_in": after_stats["tokens_in"] - before_stats["tokens_in"],
                "tokens_out": after_stats["tokens_out"] - before_stats["tokens_out"],
                "estimated_cost_eur": round(
                    after_stats["estimated_cost_eur"] - before_stats["estimated_cost_eur"],
                    6,
                ),
                "prompt_version": prompt_version,
                "model": os.getenv("LLM_MODEL", LLM_MODEL) or self.provider,
                "degradado": degradado,
                "error": err_msg,
            }
        )

    def run_all(
        self,
        *,
        auto_approve: bool = True,
        force: bool = False,
        stop_at_checkpoint: bool = False,
    ) -> Propuesta | None:
        """Ejecuta el pipeline desde el primer paso pendiente hasta terminar o detenerse en un checkpoint humano."""
        marcas = load_marcas()
        df_ej = load_ejecuciones()
        catalogo = load_fuentes()

        # 1. intake
        ficha_file = self.run_dir / "ficha.json"

        def _do_intake(prov: str) -> None:
            if self.modo == "prospecto" and self.marca_prospecto:
                ficha = _prospect_ficha(self.marca_prospecto, marcas)
                faltantes: list[str] = []
            else:
                ficha, faltantes = load_brief(self.brief_path, provider=prov)
            self.save_ficha(ficha)
            (self.run_dir / "faltantes.json").write_text(
                json.dumps(faltantes, ensure_ascii=False), encoding="utf-8"
            )

        self._run_tracked_step(
            "intake",
            ficha_file,
            "intake_v1",
            _hash_obj({"brief": str(self.brief_path), "modo": self.modo, "marca": self.marca_prospecto}),
            lambda: _do_intake(self.provider),
            fallback_fn=lambda: _do_intake("mock"),
            force=force,
        )
        if auto_approve and not self.state["checkpoints"].get("checkpoint_0_brief"):
            self.approve_checkpoint("checkpoint_0_brief", "Auto-approve CLI")
        elif not self.state["checkpoints"].get("checkpoint_0_brief") and stop_at_checkpoint:
            self.set_step_status("intake", "awaiting_human")
            return None

        ficha = self.load_ficha()

        # 2. detect (necesario para metrics y market)
        det_file = self.run_dir / "detection.parquet"
        self._run_tracked_step(
            "detect",
            det_file,
            "deterministic_f2",
            _hash_obj({"n_ej": len(df_ej), "n_marcas": len(marcas)}),
            lambda: detect(df_ej, marcas).to_parquet(det_file, index=False),
            force=force,
        )
        df_det = pd.read_parquet(det_file)

        # 3. judge
        evals_file = self.run_dir / "evaluaciones.parquet"
        self._run_tracked_step(
            "judge",
            evals_file,
            "judge_v1",
            _hash_obj({"det_rows": len(df_det), "provider": self.provider}),
            lambda: judge_ensemble(
                df_det,
                df_ej,
                marcas,
                catalogo,
                provider=self.provider,
                persist_path=evals_file,
            ),
            fallback_fn=lambda: judge_rules(df_det, df_ej, marcas, catalogo).to_parquet(
                evals_file, index=False
            ),
            force=force,
        )
        evals = pd.read_parquet(evals_file)

        # 4. metrics
        metrics_file = self.run_dir / "metrics.json"
        self._run_tracked_step(
            "metrics",
            metrics_file,
            "deterministic_f5",
            _hash_obj({"eval_rows": len(evals), "marca": ficha.marca}),
            lambda: bundle(evals, df_ej, marcas, persist_dir=self.run_dir),
            force=force,
        )
        tablas = self.load_tablas()

        # 5. market
        market_file = self.run_dir / "market.json"
        self._run_tracked_step(
            "market",
            market_file,
            "deterministic_f8",
            _hash_obj({"marca": ficha.marca, "comp": ficha.competidores_declarados}),
            lambda: self.save_market(build_market(ficha, marcas, tablas, df_ej)),
            force=force,
        )
        if auto_approve and not self.state["checkpoints"].get("checkpoint_1_competidores"):
            market_obj = self.load_market()
            market_obj.aprobado_por_humano = True
            self.save_market(market_obj)
            self.approve_checkpoint("checkpoint_1_competidores", "Auto-approve CLI")
        elif not self.state["checkpoints"].get("checkpoint_1_competidores") and stop_at_checkpoint:
            self.set_step_status("market", "awaiting_human")
            return None

        market_obj = self.load_market()

        # 6. findings
        findings_file = self.run_dir / "findings.json"
        self._run_tracked_step(
            "findings",
            findings_file,
            "deterministic_f6",
            _hash_obj({"marca": ficha.marca, "market": market_obj.no_declaradas_relevantes}),
            lambda: self.save_hallazgos(
                generate_findings(tablas, ficha=ficha, contraste_mercado=market_obj)
            ),
            force=force,
        )
        if auto_approve and not self.state["checkpoints"].get("checkpoint_2_hallazgos"):
            self.approve_checkpoint("checkpoint_2_hallazgos", "Auto-approve CLI")
        elif not self.state["checkpoints"].get("checkpoint_2_hallazgos") and stop_at_checkpoint:
            self.set_step_status("findings", "awaiting_human")
            return None

        hallazgos = self.load_hallazgos()

        # 7. plan
        plan_file = self.run_dir / "plan.json"
        self._run_tracked_step(
            "plan",
            plan_file,
            "strategy_v1",
            _hash_obj({"ficha": ficha.marca, "h": [h.id for h in hallazgos if h.aprobado]}),
            lambda: self.save_plan(
                build_plan(ficha, hallazgos, tablas, provider=self.provider)
            ),
            fallback_fn=lambda: self.save_plan(
                build_plan(ficha, hallazgos, tablas, provider="mock")
            ),
            force=force,
        )
        if auto_approve and not self.state["checkpoints"].get("checkpoint_3_plan"):
            self.approve_checkpoint("checkpoint_3_plan", "Auto-approve CLI")
        elif not self.state["checkpoints"].get("checkpoint_3_plan") and stop_at_checkpoint:
            self.set_step_status("plan", "awaiting_human")
            return None

        plan = validate_and_adjust_plan(self.load_plan(), ficha=ficha, hallazgos=hallazgos)
        self.save_plan(plan)

        # 8. write
        propuesta_file = self.run_dir / "propuesta.json"

        def _do_write(prov: str) -> None:
            if self.modo == "prospecto":
                target_brand = self.marca_prospecto or ficha.marca
                prop = write_prospect(
                    target_brand,
                    tablas,
                    marcas_catalogo=marcas,
                    run_id=self.run_id,
                    provider=prov,
                )
            else:
                prop = write_client(
                    ficha,
                    tablas,
                    hallazgos,
                    plan,
                    run_id=self.run_id,
                    provider=prov,
                )
            propuesta_file.write_text(prop.model_dump_json(indent=2), encoding="utf-8")

        self._run_tracked_step(
            "write",
            propuesta_file,
            "writer_client_v1" if self.modo == "cliente" else "writer_prospect_v1",
            _hash_obj({"modo": self.modo, "marca": ficha.marca, "coste": plan.coste_total_eur}),
            lambda: _do_write(self.provider),
            fallback_fn=lambda: _do_write("mock"),
            force=force,
        )
        propuesta = self.load_propuesta()

        # 9. review
        revision_file = self.run_dir / "revision.json"

        def _do_review(prov: str) -> None:
            ctx = {
                "metrics": build_brand_summary_metrics(tablas, marca_brief=propuesta.marca),
                "tablas": tablas,
                "hallazgos": hallazgos,
                "plan": plan,
                "ficha": ficha,
            }
            rev = compliance(
                "\n\n".join(propuesta.secciones.values()),
                plan=plan,
                ficha=ficha,
                contexto_cifras=ctx,
                provider=prov,
            )
            revision_file.write_text(rev.model_dump_json(indent=2), encoding="utf-8")
            propuesta.revision = rev
            propuesta_file.write_text(propuesta.model_dump_json(indent=2), encoding="utf-8")

        self._run_tracked_step(
            "review",
            revision_file,
            "compliance_v1",
            _hash_obj({"secciones": list(propuesta.secciones.keys())}),
            lambda: _do_review(self.provider),
            fallback_fn=lambda: _do_review("mock"),
            force=force,
        )
        propuesta = self.load_propuesta()

        # 10. export
        slug = (
            propuesta.marca.lower()
            .replace(" ", "_")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )
        if self.modo == "cliente":
            docx_out = self.run_dir / "propuesta_cliente.docx"
            md_out = self.run_dir / "propuesta_cliente.md"
        else:
            docx_out = self.run_dir / f"propuesta_prospecto_{slug}.docx"
            md_out = self.run_dir / f"propuesta_prospecto_{slug}.md"

        def _do_export() -> None:
            export_md(propuesta, md_out)
            export_docx(propuesta, docx_out)

        self._run_tracked_step(
            "export",
            docx_out,
            "deterministic_f11",
            _hash_obj({"modo": self.modo, "marca": propuesta.marca}),
            _do_export,
            force=force,
        )

        return propuesta
