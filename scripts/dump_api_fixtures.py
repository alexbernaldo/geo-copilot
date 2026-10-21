"""Ejecuta el pipeline en mock con el kit y vuelca una respuesta JSON por cada GET de la API.

Solo para desarrollo del frontend (MSW). Las fixtures no se sirven en producción.
Uso: python scripts/dump_api_fixtures.py [carpeta_salida]
"""

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from geo.orchestrator import Run  # noqa: E402
from geo.reference import REFERENCE_DIR  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "frontend" / "mocks" / "fixtures"
PROJECT_ID = "p_20261021_153012_ab12cd"
STEP_NAMES = {
    "intake": "Ficha", "market": "Mercado", "detect": "Detección", "judge": "Juez", "metrics": "Métricas",
    "findings": "Hallazgos", "plan": "Plan", "review": "Revisión", "write": "Redacción", "export": "Exportación",
}


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", force_ascii=False))


def _clean(x):
    """NaN → None (JSON válido)."""
    if isinstance(x, float) and x != x:
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def _save(name: str, data) -> None:
    data = _clean(data)
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _trace(run_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run = Run(run_id="fixtures", modo="cliente", brief_path=REFERENCE_DIR / "Brief_de_ejemplo_Clinica_Alborada.md",
                  provider="mock", runs_root=Path(tmp))
        run.run_all(auto_approve=True)
        d = run.run_dir
        state, trace = _read(d / "state.json"), _trace(d)
        ficha, market, plan = _read(d / "ficha.json"), _read(d / "market.json"), _read(d / "plan.json")
        prop, rev, metrics = _read(d / "propuesta.json"), _read(d / "revision.json"), _read(d / "metrics.json")
        findings = _read(d / "findings.json")
        coste = round(sum(t.get("estimated_cost_eur", 0) for t in trace), 4)

        pasos = [{"id": t["step"], "nombre": STEP_NAMES.get(t["step"], t["step"]), "estado": "hecho_automatico" if t.get("degradado") else "hecho",
                  "duracion_s": t.get("duration_s"), "llamadas": t.get("llm_calls", 0), "coste_eur": t.get("estimated_cost_eur", 0.0), "error": t.get("error")}
                 for t in trace if t.get("step") in STEP_NAMES]
        project = {"id": PROJECT_ID, "nombre": "Clínica Alborada Visión", "tipo": "cliente", "marca": ficha["marca"], "sector": ficha["sector"],
                   "origen_datos": "csv", "revision": "pausas", "estado": "completado", "punto_control_pendiente": None,
                   "checkpoints": {"ficha": True, "competencia": True, "hallazgos": True, "plan": True}, "coste_eur": 0.0,
                   "creado": "2026-10-21T15:30:12Z", "actualizado": "2026-10-21T15:42:03Z", "archivado": False}
        _save("projects.json", [project])
        _save("project.json", project)
        _save("progress.json", {"estado": "completado", "paso_actual": None, "pasos": pasos, "contador": None,
                                "llamadas": sum(p["llamadas"] for p in pasos), "coste_eur": 0.0, "coste_real": False,
                                "transcurrido_s": round(sum(p["duracion_s"] or 0 for p in pasos), 2)})
        _save("ficha.json", {"ficha": ficha, "faltantes": _read(d / "faltantes.json"), "origen_campos": {}, "brief_texto": run.brief_path.read_text(encoding="utf-8-sig"), "aprobada": True})
        _save("market.json", market)
        _save("findings.json", findings)
        _save("plan.json", {"plan": plan, "avisos": [], "presupuesto_min_eur": ficha.get("presupuesto_min_eur"), "presupuesto_max_eur": ficha.get("presupuesto_max_eur"),
                            "carga_semanal": [], "aprobado": True})

        tablas: dict[str, pd.DataFrame] = {}
        for f in sorted((d / "tablas").glob("T*.parquet")):
            tablas[f.stem] = pd.read_parquet(f)
        for tid, df in tablas.items():
            _save(f"tables/{tid}.json", {"id": tid, "titulo": tid, "columnas": list(df.columns), "filas": _records(df), "n": int(df["n"].sum()) if "n" in df else None})

        escalares = {k: v for k, v in metrics.items() if not isinstance(v, (dict, list))}
        for ambito, sufijo in (("espontanea", "espontanea"), ("asistida", "asistida")):
            graficos = {tid: _records(df[df["ambito"] == sufijo]) if "ambito" in df and len(df[df["ambito"] == sufijo]) else _records(df)
                        for tid, df in tablas.items() if "_" not in tid}
            _save(f"diagnosis_{ambito}.json", {"ambito": ambito, "marca_proyecto": ficha["marca"], "lider": metrics.get("lider_espontaneo"),
                                               "indicadores": escalares, "graficos": graficos, "no_aplica": {}})

        ejec = pd.read_csv(REFERENCE_DIR / "ejecuciones.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
        inst = dict(zip(*[pd.read_csv(REFERENCE_DIR / "banco_prompts.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)[c] for c in ("Prompt_ID", "Instanciación")]))
        filas = [{"ejecucion_id": r["Ejecucion_ID"], "prompt_id": r["Prompt_ID"], "familia": r["Familia"], "intencion": r["Intención"], "instanciacion": inst.get(r["Prompt_ID"], ""),
                  "ambito": "espontanea" if inst.get(r["Prompt_ID"]) in ("generico", "ciudad") else "asistida", "motor": r["Motor"], "repeticion": int(r["Repetición"]), "ciudad": None, "prompt": r["Prompt ejecutado"],
                  "marcas_a_evaluar": [m.strip() for m in r["Marcas a evaluar"].split("|")], "fecha": r["Fecha/hora"]} for _, r in ejec.head(50).iterrows()]
        _save("executions.json", {"total": int(len(ejec)), "pagina": 1, "tamano": 50, "filas": filas})
        ev = pd.read_parquet(d / "evaluaciones.parquet")
        first = ejec.iloc[0]
        evals = [{"marca": r["marca"], "aparece": bool(r["aparece"]), "posicion": None if pd.isna(r["posicion"]) else int(r["posicion"]), "tipo_mencion": r["tipo_mencion"],
                  "fuerza": int(r["fuerza"]), "sentimiento": r["sentimiento"], "tipo_fuente": r["tipo_fuente"], "calidad_fuente": None if pd.isna(r["calidad_fuente"]) else float(r["calidad_fuente"]),
                  "juez": r["juez"], "confianza": float(r["confianza_juez"]), "discrepancia": bool(r["discrepancia"]), "fragmento": r["fragmento"]}
                 for _, r in ev[ev["ejecucion_id"] == first["Ejecucion_ID"]].iterrows()]
        resp = first["Respuesta completa"]
        resaltados = [{"marca": e["marca"], "inicio": resp.find(e["marca"]), "fin": resp.find(e["marca"]) + len(e["marca"])} for e in evals if e["aparece"] and resp.find(e["marca"]) >= 0]
        _save("execution_detail.json", {"fila": filas[0], "respuesta": resp, "resaltados": resaltados,
                                        "fuentes": [{"dominio": s.strip(), "tipo": "Medio", "calidad": None} for s in first["Fuentes citadas"].split("|") if s.strip()], "evaluaciones": evals})

        secciones = [{"id": f"s{i}", "titulo": t, "markdown": md, "origen": {"origen": "automatico", "modelo": None}} for i, (t, md) in enumerate(prop["secciones"].items(), 1)]
        _save("proposal.json", {"modo": prop["modo"], "marca": prop["marca"], "secciones": secciones,
                                "sello": {"cifras_verificadas": rev["cifras_verificadas"], "cifras_no_trazables": rev["cifras_no_trazables"], "incidencias_normativas": 0,
                                          "entidades_fuera_catalogo": 0, "incidencias": rev["incidencias"], "aprobado": rev["aprobado"]},
                                "correo": None, "exportaciones": ["docx", "md"]})
        _save("quality.json", {"validacion": {"disponible": False, "campos": [], "n": 0}, "discrepancias": [],
                               "aprobaciones": [{"punto_control": i, "nombre": n, "fecha": a["timestamp"], "nota": a.get("note"), "automatica": True}
                                                for i, (n, a) in enumerate(((a["checkpoint"], a) for a in state["human_approvals"]))],
                               "muestra_para_etiquetar": [str(x) for x in ejec["Ejecucion_ID"].head(15)]})
        _save("traces.json", trace)

    _save("settings.json", {"clave_configurada": True, "clave_mascara": "sk-or-…a1b2",
                            "modelos": {"juez": "google/gemini-2.5-flash", "redaccion": "anthropic/claude-sonnet-4.5", "propuesta": "google/gemini-2.5-flash",
                                        "chatgpt": "openai/gpt-4o-mini", "gemini": "google/gemini-2.5-flash", "claude": "anthropic/claude-haiku-4.5", "perplexity": "perplexity/sonar"},
                            "limites": {"concurrencia": 8, "max_llamadas": 3000, "tope_gasto_eur": 15.0, "usd_eur": 0.92},
                            "carpeta_datos": "./data/projects", "modelos_inexistentes": []})
    _save("models.json", [{"id": "google/gemini-2.5-flash", "nombre": "Gemini 2.5 Flash", "precio_in_usd_m": 0.3, "precio_out_usd_m": 2.5, "contexto": 1048576},
                          {"id": "anthropic/claude-sonnet-4.5", "nombre": "Claude Sonnet 4.5", "precio_in_usd_m": 3.0, "precio_out_usd_m": 15.0, "contexto": 200000},
                          {"id": "openai/gpt-4o-mini", "nombre": "GPT-4o mini", "precio_in_usd_m": 0.15, "precio_out_usd_m": 0.6, "contexto": 128000}])
    est = {"pasos": [{"id": "judge", "nombre": "Juez", "llamadas": 624, "tokens_in": 900000, "tokens_out": 90000, "eur": 1.1}], "total_llamadas": 624, "total_eur": 1.1,
           "minutos": 6.5, "supera_tope": False, "tope_eur": 15.0}
    _save("estimates_analysis.json", est)
    _save("estimates_study.json", {**est, "pasos": [{"id": "queries", "nombre": "Ejecutar consultas", "llamadas": 416, "tokens_in": 600000, "tokens_out": 400000, "eur": 4.2}], "total_llamadas": 416, "total_eur": 4.2})
    marcas = pd.read_csv(REFERENCE_DIR / "marcas.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    _save("brands.json", {"marcas": [{"nombre": r.Marca, "nivel": r.Nivel, "rol": r.Rol, "dominio": r.Dominio_propio, "alias": [a.strip() for a in r.Alias.split("|") if a.strip()],
                                     "motivo": None, "fuente_url": None} for r in marcas.itertuples()]})
    banco = pd.read_csv(REFERENCE_DIR / "banco_prompts.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    _save("prompts.json", {"prompts": [{"prompt_id": r["Prompt_ID"], "familia": r["Familia"], "intencion": r["Intención"], "prioridad": r["Prioridad"], "uso": r["Uso"],
                                         "instanciacion": r["Instanciación"], "plantilla": r["Prompt (plantilla)"]} for _, r in banco.iterrows()]})
    _save("instances.json", [{"prompt_id": r["Prompt_ID"], "prompt": r["Prompt ejecutado"], "instanciacion": inst.get(r["Prompt_ID"], ""),
                              "marcas_a_evaluar": [m.strip() for m in r["Marcas a evaluar"].split("|")], "ciudad": None}
                             for _, r in ejec.drop_duplicates("Prompt_ID").iterrows()])
    _save("study_summary.json", {"ejecuciones": int(len(ejec)), "motores": sorted(ejec["Motor"].unique()), "repeticiones": int(ejec["Repetición"].astype(int).max()),
                                 "prompts": int(ejec["Prompt_ID"].nunique()), "marcas": int(len(marcas)), "espontaneas": int(ejec["Prompt_ID"].map(inst).isin(["generico", "ciudad"]).sum()), "asistidas": int((~ejec["Prompt_ID"].map(inst).isin(["generico", "ciudad"])).sum()), "ciudades": []})
    _save("study_config.json", {"tamano": "completo", "motores": ["ChatGPT", "Gemini", "Perplexity", "Claude"], "repeticiones": 3})
    _save("health.json", {"ok": True, "version": "1.0.0"})
    print("fixtures en", OUT)


if __name__ == "__main__":
    main()
