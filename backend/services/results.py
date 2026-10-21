"""Lectura y edición de los resultados del análisis (ficha, competencia, hallazgos, plan, diagnóstico, ejecuciones,
propuesta, calidad). Todo sale de los artefactos de `run/` y `study/`; el cliente no calcula cifras."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from geo.schemas import ContrasteMercado, FichaMarca, Hallazgo, MarcaMercado, Plan

from backend.errors import api_error, conflict, not_found, unprocessable
from backend.services import inputs, study_files as sf
from backend.services.pipeline import CHECKPOINTS, STEP_NAMES
from backend.services.store import ProjectStore, atomic_write_json, read_json

TABLE_TITLES = {
    "T1": "Ranking de marcas por score", "T2": "Marca por motor", "T3": "Embudo por intención", "T4": "Marca por ciudad",
    "T5": "Marca por familia de prompt", "T6": "Perfil de fuentes por marca", "T7": "Dominios más citados", "T8": "Duelos 1 a 1",
    "T9": "Calidad de la mención asistida", "T10": "Consistencia entre repeticiones", "T11": "Brecha frente al líder por intención",
    "T12": "Ejecuciones sin búsqueda por motor",
}
NO_APLICA = {
    "T4": "El estudio no tiene prompts de ciudad.", "T8": "Los duelos 1 a 1 solo aplican a la visibilidad asistida.",
    "T9": "La calidad de la mención solo aplica a la visibilidad asistida.",
}
CAPACIDAD_SEMANAL_H = 18.0


def _clean(x: Any) -> Any:
    """NaN → None y tipos numpy → Python, para que la respuesta sea JSON válido."""
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if hasattr(x, "tolist"):
        return _clean(x.tolist())
    if isinstance(x, float) and x != x:
        return None
    return x


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return _clean(json.loads(df.to_json(orient="records", force_ascii=False)))


def pending(step: str) -> Exception:
    return conflict("paso_pendiente", f"Disponible cuando termine el paso «{STEP_NAMES.get(step, step)}».", {"paso": step})


def run_file(store: ProjectStore, pid: str, name: str, step: str) -> Path:
    store.require(pid)
    p = store.run_dir(pid) / name
    if not p.exists():
        raise pending(step)
    return p


def _checkpoint_ok(store: ProjectStore, pid: str, n: int) -> bool:
    return bool((store.read_state(pid).get("checkpoints") or {}).get(CHECKPOINTS[n][0], False))


# ---------------------------------------------------------------- ficha
def get_ficha(store: ProjectStore, pid: str) -> dict[str, Any]:
    store.require(pid)
    run = store.run_dir(pid)
    ficha = read_json(run / "ficha.json")
    if ficha is not None:
        faltantes = read_json(run / "faltantes.json", []) or []
    else:
        prev = read_json(store.inputs_dir(pid) / "ficha_preview.json")
        if not prev:
            raise pending("intake")
        ficha, faltantes = prev["ficha"], prev.get("faltantes", [])
    return {"ficha": FichaMarca.model_validate(ficha).model_dump(mode="json"), "faltantes": faltantes, "origen_campos": {},
            "brief_texto": inputs.read_brief(store, pid), "aprobada": _checkpoint_ok(store, pid, 0)}


def put_ficha(store: ProjectStore, pid: str, ficha: FichaMarca) -> dict[str, Any]:
    from geo.intake import find_missing_fields

    store.require(pid)
    run = store.run_dir(pid)
    run.mkdir(parents=True, exist_ok=True)
    atomic_write_json(run / "ficha.json", ficha.model_dump(mode="json"))
    atomic_write_json(run / "faltantes.json", find_missing_fields(ficha))
    st = store.read_state(pid)
    if not st or (st.get("steps") or {}).get("intake") != "done":
        # la ficha editada antes de lanzar sustituye a la extracción del brief
        steps = (st.get("steps") if st else None) or {}
        steps["intake"] = "done"
        store.patch_state(pid, steps=steps, ficha_editada=True)
    store.update(pid, marca=ficha.marca, sector=ficha.sector)
    return get_ficha(store, pid)


# ---------------------------------------------------------------- competencia
def _extra(store: ProjectStore, pid: str) -> dict[str, Any]:
    return read_json(store.run_dir(pid) / "market_extra.json", {}) or {}


def get_market(store: ProjectStore, pid: str) -> dict[str, Any]:
    data = read_json(run_file(store, pid, "market.json", "market"))
    excl = set(_extra(store, pid).get("excluidas", []))
    mc = ContrasteMercado.model_validate(data)
    out = mc.model_dump(mode="json")
    for m in out["marcas"]:
        m["excluida"] = m["nombre"] in excl
    out["candidatas_no_catalogadas"] = _candidatas(store, pid)
    return out


def _candidatas(store: ProjectStore, pid: str) -> list[str]:
    cached = _extra(store, pid).get("candidatas")
    if cached is not None:
        return cached
    try:
        from geo.loader import load_ejecuciones, load_marcas
        from geo.market import discover_uncataloged_brands

        d = store.study_dir(pid)
        ej = load_ejecuciones(sf.study_file(d, "ejecuciones"), sf.study_file(d, "banco_prompts"))
        return list(discover_uncataloged_brands(ej, load_marcas(sf.study_file(d, "marcas"))))
    except Exception:
        return []


def put_market(store: ProjectStore, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    run_file(store, pid, "market.json", "market")
    marcas = [{k: m.get(k) for k in ("nombre", "rol", "declarada_en_brief", "detectada_en_datos", "tasa_aparicion_espontanea", "nota") if k in m}
              for m in payload["marcas"]]
    try:
        mc = ContrasteMercado(marcas=[MarcaMercado(**m) for m in marcas], no_declaradas_relevantes=payload.get("no_declaradas_relevantes", []),
                              discrepancias_brief=payload.get("discrepancias_brief", []),
                              aprobado_por_humano=bool(payload.get("aprobado_por_humano", False)))
    except Exception as exc:
        raise unprocessable("competencia_no_valida", f"La competencia no es válida: {exc}") from exc
    atomic_write_json(store.run_dir(pid) / "market.json", mc.model_dump(mode="json"))
    atomic_write_json(store.run_dir(pid) / "market_extra.json",
                      {"excluidas": [m["nombre"] for m in payload["marcas"] if m.get("excluida")], "candidatas": payload.get("candidatas_no_catalogadas")})
    return get_market(store, pid)


# ---------------------------------------------------------------- hallazgos
def _review(store: ProjectStore, pid: str) -> dict[str, Any]:
    return read_json(store.run_dir(pid) / "findings_review.json", {}) or {}


def _finding_view(h: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    r = review.get(h["id"], {})
    out = Hallazgo.model_validate(h).model_dump(mode="json")
    out["descartado_motivo"] = r.get("descartado_motivo") if not out["aprobado"] else None
    out["nota"] = r.get("nota")
    out["origen"] = {"origen": "editado" if r.get("titulo_original") else "calculado", "modelo": None}
    return out


def get_findings(store: ProjectStore, pid: str) -> list[dict[str, Any]]:
    raw = read_json(run_file(store, pid, "findings.json", "findings"), [])
    rev = _review(store, pid)
    return sorted((_finding_view(h, rev) for h in raw), key=lambda h: h["prioridad"])


def patch_finding(store: ProjectStore, pid: str, hid: str, patch: dict[str, Any]) -> dict[str, Any]:
    path = run_file(store, pid, "findings.json", "findings")
    raw = read_json(path, [])
    target = next((h for h in raw if h["id"] == hid), None)
    if target is None:
        raise not_found("El hallazgo")
    rev = _review(store, pid)
    r = rev.setdefault(hid, {})
    if patch.get("titulo") is not None:
        titulo = patch["titulo"].strip()
        if not titulo:
            raise unprocessable("titulo_vacio", "El título no puede estar vacío.")
        r.setdefault("titulo_original", target["titulo"])
        target["titulo"] = titulo
    if patch.get("nota") is not None:
        r["nota"] = patch["nota"]
    if patch.get("aprobado") is not None:
        if patch["aprobado"] is False:
            motivo = (patch.get("descartado_motivo") or r.get("descartado_motivo") or "").strip()
            if not motivo:
                raise unprocessable("motivo_obligatorio", "Para descartar un hallazgo indica el motivo.")
            r["descartado_motivo"] = motivo
        target["aprobado"] = bool(patch["aprobado"])
    elif patch.get("descartado_motivo") is not None:
        r["descartado_motivo"] = patch["descartado_motivo"]
    atomic_write_json(path, raw)
    atomic_write_json(store.run_dir(pid) / "findings_review.json", rev)
    return _finding_view(target, rev)


# ---------------------------------------------------------------- plan
def _plan_inputs(store: ProjectStore, pid: str) -> tuple[Plan, FichaMarca, list[Hallazgo]]:
    plan = Plan.model_validate(read_json(run_file(store, pid, "plan.json", "plan")))
    ficha = FichaMarca.model_validate(read_json(run_file(store, pid, "ficha.json", "intake")))
    hall = [Hallazgo.model_validate(h) for h in (read_json(store.run_dir(pid) / "findings.json", []) or [])]
    return plan, ficha, hall


def plan_warnings(plan: Plan, ficha: FichaMarca, hallazgos: list[Hallazgo]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from geo.budget import compute_weekly_client_hours, has_dependency_cycles

    avisos: list[dict[str, Any]] = []
    ids = {a.id for a in plan.acciones}
    hids = {h.id for h in hallazgos}
    for a in plan.acciones:
        if not a.hallazgos_relacionados:
            avisos.append({"nivel": "error", "texto": f"La acción {a.id} no está vinculada a ningún hallazgo.", "accion_id": a.id})
        elif hids and not set(a.hallazgos_relacionados) <= hids:
            avisos.append({"nivel": "aviso", "texto": f"La acción {a.id} cita hallazgos que no existen: {', '.join(sorted(set(a.hallazgos_relacionados) - hids))}.", "accion_id": a.id})
        for d in a.dependencias:
            if d not in ids:
                avisos.append({"nivel": "error", "texto": f"La acción {a.id} depende de {d}, que no existe.", "accion_id": a.id})
    if has_dependency_cycles(plan.acciones):
        avisos.append({"nivel": "error", "texto": "Las dependencias entre acciones forman un ciclo.", "accion_id": None})
    total = round(sum(a.coste_estimado_eur for a in plan.acciones), 2)
    if ficha.presupuesto_max_eur is not None and total > ficha.presupuesto_max_eur:
        avisos.append({"nivel": "error", "texto": f"El coste total ({total:,.0f} €) supera el presupuesto máximo del brief ({ficha.presupuesto_max_eur:,.0f} €).".replace(",", "."), "accion_id": None})
    elif ficha.presupuesto_min_eur is not None and total < ficha.presupuesto_min_eur:
        avisos.append({"nivel": "info", "texto": f"El coste total ({total:,.0f} €) queda por debajo del presupuesto mínimo del brief ({ficha.presupuesto_min_eur:,.0f} €).".replace(",", "."), "accion_id": None})
    carga = compute_weekly_client_hours(plan.acciones)
    for semana, horas in sorted(carga.items()):
        if horas > CAPACIDAD_SEMANAL_H:
            avisos.append({"nivel": "aviso", "texto": f"La semana {semana} exige {horas:g} h al equipo del cliente (capacidad {CAPACIDAD_SEMANAL_H:g} h).", "accion_id": None})
    return avisos, [{"semana": int(s), "horas": float(h), "capacidad": CAPACIDAD_SEMANAL_H} for s, h in sorted(carga.items())]


def _plan_response(store: ProjectStore, pid: str, plan: Plan, ficha: FichaMarca, hall: list[Hallazgo], extra: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    avisos, carga = plan_warnings(plan, ficha, hall)
    return {"plan": plan.model_dump(mode="json"), "avisos": (extra or []) + avisos, "presupuesto_min_eur": ficha.presupuesto_min_eur,
            "presupuesto_max_eur": ficha.presupuesto_max_eur, "carga_semanal": carga, "aprobado": _checkpoint_ok(store, pid, 3)}


def get_plan(store: ProjectStore, pid: str) -> dict[str, Any]:
    plan, ficha, hall = _plan_inputs(store, pid)
    return _plan_response(store, pid, plan, ficha, hall)


def put_plan(store: ProjectStore, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    from geo.budget import validate_and_adjust_plan

    _, ficha, hall = _plan_inputs(store, pid)
    try:
        sent = Plan.model_validate(payload)
    except Exception as exc:
        raise unprocessable("plan_no_valido", f"El plan no es válido: {exc}") from exc
    extra: list[dict[str, Any]] = []
    avisos_enviado, _ = plan_warnings(sent, ficha, hall)
    adjusted = validate_and_adjust_plan(sent, ficha=ficha, hallazgos=hall)
    if adjusted.model_dump() != sent.model_dump():
        extra.append({"nivel": "info", "texto": "Se han reajustado semanas, fases o costes para respetar dependencias, presupuesto y capacidad del equipo.", "accion_id": None})
    atomic_write_json(store.run_dir(pid) / "plan.json", adjusted.model_dump(mode="json"))
    resp = _plan_response(store, pid, adjusted, ficha, hall, extra)
    resp["avisos"] = extra + [a for a in avisos_enviado if a["nivel"] == "error"] + [a for a in resp["avisos"] if a not in extra and a["nivel"] != "error"]
    return resp


def simulate_plan(store: ProjectStore, pid: str, cambios: dict[str, Any]) -> dict[str, Any]:
    from geo.loader import load_ejecuciones
    from geo.simulate import simulate

    ev_path = run_file(store, pid, "evaluaciones.parquet", "judge")
    ficha = FichaMarca.model_validate(read_json(run_file(store, pid, "ficha.json", "intake")))
    d = store.study_dir(pid)
    try:
        ej = load_ejecuciones(sf.study_file(d, "ejecuciones"), sf.study_file(d, "banco_prompts"))
        res = simulate(pd.read_parquet(ev_path), ficha.marca, cambios, ejecuciones=ej)
    except HTTPExceptionTypes:
        raise
    except Exception as exc:
        raise unprocessable("simulacion_no_valida", f"No se pudo simular el escenario: {exc}") from exc
    detalle = {k: (_records(v) if isinstance(v, pd.DataFrame) else _clean(v)) for k, v in res.items()
               if k not in ("score_actual", "score_simulado", "puesto_actual", "puesto_simulado", "aviso")}
    return {"score_actual": float(res["score_actual"]), "score_simulado": float(res["score_simulado"]), "puesto_actual": int(res["puesto_actual"]),
            "puesto_simulado": int(res["puesto_simulado"]), "etiqueta": "Escenario hipotético, no una predicción", "detalle": detalle}


from fastapi import HTTPException as HTTPExceptionTypes  # noqa: E402


# ---------------------------------------------------------------- diagnóstico y tablas
def _load_tablas(store: ProjectStore, pid: str) -> dict[str, pd.DataFrame]:
    d = store.run_dir(pid) / "tablas"
    if not d.is_dir():
        raise pending("metrics")
    out = {}
    for f in sorted(d.glob("*.parquet")):
        df = pd.read_parquet(f)
        if "evidencia_ids" in df.columns:
            df["evidencia_ids"] = df["evidencia_ids"].apply(lambda x: list(x) if hasattr(x, "__iter__") and not isinstance(x, str) else [])
        out[f.stem] = df
    return out


def get_diagnosis(store: ProjectStore, pid: str, ambito: str) -> dict[str, Any]:
    if ambito not in ("espontanea", "asistida"):
        raise unprocessable("ambito_no_valido", "El ámbito debe ser «espontanea» o «asistida».")
    metrics = read_json(run_file(store, pid, "metrics.json", "metrics"), {}) or {}
    tablas = _load_tablas(store, pid)
    otro = "asistid" if ambito == "espontanea" else "espontane"
    indicadores = {k: v for k, v in metrics.items() if not isinstance(v, (dict, list)) and otro not in k}
    graficos: dict[str, Any] = {}
    no_aplica: dict[str, str] = {}
    for tid in TABLE_TITLES:
        df = tablas.get(tid)
        if df is None:
            no_aplica[tid] = NO_APLICA.get(tid, "No hay datos para este gráfico.")
            continue
        if "ambito" in df.columns:
            df = df[df["ambito"] == ambito]
        if df.empty:
            no_aplica[tid] = NO_APLICA.get(tid, "No hay datos para este ámbito.")
            continue
        graficos[tid] = _records(df)
    return {"ambito": ambito, "marca_proyecto": metrics.get("marca_brief") or "", "lider": metrics.get("lider_espontaneo"),
            "indicadores": _clean(indicadores), "graficos": graficos, "no_aplica": no_aplica}


def get_table(store: ProjectStore, pid: str, tid: str) -> dict[str, Any]:
    store.require(pid)
    if not re.fullmatch(r"T\d{1,2}(_[a-z]+)?", tid):
        raise not_found("La tabla")
    p = store.run_dir(pid) / "tablas" / f"{tid}.parquet"
    if not (store.run_dir(pid) / "tablas").is_dir():
        raise pending("metrics")
    if not p.exists():
        raise not_found("La tabla")
    df = pd.read_parquet(p)
    if "evidencia_ids" in df.columns:
        df["evidencia_ids"] = df["evidencia_ids"].apply(lambda x: list(x) if hasattr(x, "__iter__") and not isinstance(x, str) else [])
    base = tid.split("_")[0]
    return {"id": tid, "titulo": TABLE_TITLES.get(base, tid), "columnas": list(df.columns), "filas": _records(df),
            "n": int(df["n"].sum()) if "n" in df.columns else None}


# ---------------------------------------------------------------- ejecuciones
_EXEC_CACHE: dict[str, tuple[tuple[float, float, float], pd.DataFrame]] = {}


def _executions_df(store: ProjectStore, pid: str) -> pd.DataFrame:
    d = store.study_dir(pid)
    ej, ba = sf.study_file(d, "ejecuciones"), sf.study_file(d, "banco_prompts")
    if not ej.exists():
        return pd.DataFrame()
    sig = (ej.stat().st_mtime, ba.stat().st_mtime if ba.exists() else 0.0, ej.stat().st_size)
    key = str(ej)
    if key in _EXEC_CACHE and _EXEC_CACHE[key][0] == sig:
        return _EXEC_CACHE[key][1]
    df = sf._canonical(sf.read_csv(ej), "ejecuciones")
    inst = {}
    if ba.exists():
        bank = sf._canonical(sf.read_csv(ba), "banco_prompts")
        inst = dict(zip(bank["Prompt_ID"], bank["Instanciación"]))
    df["instanciacion"] = df["Prompt_ID"].map(inst).fillna("")
    df["ambito"] = df["instanciacion"].map(lambda v: "espontanea" if v in sf.ESPONTANEAS else "asistida")
    ficha = inputs.current_ficha(store, pid)
    ciudades = list(ficha.ciudades) if ficha else []

    def _ciudad(row: pd.Series) -> str | None:
        if row["instanciacion"] != "ciudad":
            return None
        return next((c for c in ciudades if c.lower() in row["Prompt ejecutado"].lower()), None)

    df["ciudad"] = df.apply(_ciudad, axis=1)
    _EXEC_CACHE[key] = (sig, df)
    return df


def _exec_row(r: pd.Series) -> dict[str, Any]:
    return {"ejecucion_id": r["Ejecucion_ID"], "prompt_id": r["Prompt_ID"], "familia": r.get("Familia", ""), "intencion": r.get("Intención", ""),
            "instanciacion": r["instanciacion"], "ambito": r["ambito"], "motor": r["Motor"], "repeticion": int(r["Repetición"] or 0),
            "ciudad": r["ciudad"], "prompt": r["Prompt ejecutado"],
            "marcas_a_evaluar": [m.strip() for m in r["Marcas a evaluar"].split("|") if m.strip()], "fecha": r.get("Fecha/hora", "")}


def list_executions(store: ProjectStore, pid: str, *, motor: str | None, familia: str | None, intencion: str | None, ambito: str | None,
                    ciudad: str | None, ids: str | None, q: str | None, pagina: int, tamano: int) -> dict[str, Any]:
    store.require(pid)
    pagina, tamano = max(1, pagina), min(max(1, tamano), 200)
    df = _executions_df(store, pid)
    if df.empty:
        return {"total": 0, "pagina": pagina, "tamano": tamano, "filas": []}
    if motor:
        df = df[df["Motor"] == motor]
    if familia:
        df = df[df["Familia"] == familia]
    if intencion:
        df = df[df["Intención"] == intencion]
    if ambito:
        df = df[df["ambito"] == ambito]
    if ciudad:
        df = df[df["ciudad"] == ciudad]
    if ids:
        wanted = {i.strip() for i in ids.split(",") if i.strip()}
        df = df[df["Ejecucion_ID"].isin(wanted)]
    if q:
        needle = q.strip().lower()
        df = df[df["Prompt ejecutado"].str.lower().str.contains(needle, regex=False) | df["Respuesta completa"].str.lower().str.contains(needle, regex=False)]
    page = df.iloc[(pagina - 1) * tamano: pagina * tamano]
    return {"total": int(len(df)), "pagina": pagina, "tamano": tamano, "filas": [_exec_row(r) for _, r in page.iterrows()]}


def get_execution(store: ProjectStore, pid: str, eid: str) -> dict[str, Any]:
    store.require(pid)
    df = _executions_df(store, pid)
    row = df[df["Ejecucion_ID"] == eid] if not df.empty else df
    if row.empty:
        raise not_found("La ejecución")
    r = row.iloc[0]
    d = store.study_dir(pid)
    brands = sf.read_brands(d)
    resp = r["Respuesta completa"]
    resaltados: list[dict[str, Any]] = []
    for b in brands:
        for term in sorted({b["nombre"], *b["alias"]}, key=len, reverse=True):
            for m in re.finditer(re.escape(term), resp, flags=re.IGNORECASE):
                if not any(m.start() < x["fin"] and m.end() > x["inicio"] for x in resaltados):
                    resaltados.append({"marca": b["nombre"], "inicio": m.start(), "fin": m.end()})
    resaltados.sort(key=lambda x: x["inicio"])
    cat: dict[str, tuple[str, float]] = {}
    fu = sf.study_file(d, "fuentes_catalogo")
    if fu.exists():
        c = sf._canonical(sf.read_csv(fu), "fuentes_catalogo")
        for _, x in c.iterrows():
            try:
                cat[x["Dominio"].lower()] = (x["Tipo_de_fuente"], float(x.get("Calidad_de_fuente_0_1") or "nan"))
            except ValueError:
                cat[x["Dominio"].lower()] = (x["Tipo_de_fuente"], float("nan"))
    fuentes = []
    for dom in [s.strip() for s in r.get("Fuentes citadas", "").split("|") if s.strip()]:
        tipo, cal = cat.get(dom.lower(), (None, float("nan")))
        fuentes.append({"dominio": dom, "tipo": tipo, "calidad": None if cal != cal else cal})
    evals: list[dict[str, Any]] = []
    evp = store.run_dir(pid) / "evaluaciones.parquet"
    if evp.exists():
        ev = pd.read_parquet(evp)
        for _, e in ev[ev["ejecucion_id"] == eid].iterrows():
            evals.append(_clean({
                "marca": e["marca"], "aparece": bool(e["aparece"]), "posicion": None if pd.isna(e.get("posicion")) else int(e["posicion"]),
                "tipo_mencion": e.get("tipo_mencion"), "fuerza": int(e["fuerza"]), "sentimiento": e.get("sentimiento"), "tipo_fuente": e.get("tipo_fuente"),
                "calidad_fuente": None if pd.isna(e.get("calidad_fuente")) else float(e["calidad_fuente"]), "juez": str(e.get("juez", "")),
                "confianza": float(e.get("confianza_juez", 0.0) or 0.0), "discrepancia": bool(e.get("discrepancia", False)), "fragmento": e.get("fragmento")}))
    return {"fila": _exec_row(r), "respuesta": resp, "resaltados": resaltados, "fuentes": fuentes, "evaluaciones": evals}


# ---------------------------------------------------------------- propuesta
def _step_origin(store: ProjectStore, pid: str, step: str) -> dict[str, Any]:
    """Etiqueta de origen según la traza del paso (regla 0.1): `ia` solo si lo hizo un LLM real y no se degradó."""
    st = store.read_state(pid)
    entries = [json.loads(line) for line in (store.run_dir(pid) / "trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()] \
        if (store.run_dir(pid) / "trace.jsonl").exists() else []
    t = next((e for e in reversed(entries) if e.get("step") == step), {})
    provider = t.get("provider") or st.get("provider") or "mock"
    if provider == "openrouter" and not t.get("degradado") and step not in (st.get("degradados") or {}):
        key = "estrategia_y_redaccion" if step == "write" else "juez_y_revisor"
        modelo = t.get("model") if t.get("provider") and t.get("model") not in (None, "", "mock") else (st.get("models") or {}).get(key) or t.get("model")
        return {"origen": "ia", "modelo": modelo or None}
    return {"origen": "automatico", "modelo": None}


def get_proposal(store: ProjectStore, pid: str) -> dict[str, Any]:
    prop = read_json(run_file(store, pid, "propuesta.json", "write"))
    rev = read_json(store.run_dir(pid) / "revision.json", {}) or {}
    origen = _step_origin(store, pid, "write")
    editadas = set(read_json(store.run_dir(pid) / "propuesta_editada.json", []) or [])
    secciones = [{"id": f"s{i}", "titulo": t, "markdown": md,
                  "origen": {"origen": "editado", "modelo": None} if t in editadas else origen}
                 for i, (t, md) in enumerate(prop["secciones"].items(), 1)]
    inc = rev.get("incidencias", [])
    sello = {"cifras_verificadas": int(rev.get("cifras_verificadas", 0)), "cifras_no_trazables": int(rev.get("cifras_no_trazables", 0)),
             "incidencias_normativas": sum(1 for i in inc if i.get("tipo") in ("promesa_resultado", "comparativa_denigratoria", "claim_sanitario", "normativa")),
             "entidades_fuera_catalogo": sum(1 for i in inc if "entidad" in str(i.get("tipo", ""))),
             "incidencias": [{"tipo": i.get("tipo", ""), "texto": i.get("texto", ""), "sugerencia": i.get("sugerencia") or None, "bloqueante": bool(i.get("bloqueante"))} for i in inc],
             "aprobado": bool(rev.get("aprobado", False))}
    correo = None
    if prop["modo"] == "prospecto":
        txt = next((md for t, md in prop["secciones"].items() if "correo" in t.lower()), "")
        m = re.search(r"\*{0,2}Asunto:?\*{0,2}:?\s*(.+)", txt)
        if m:
            correo = {"asunto": m.group(1).strip(), "cuerpo": txt[m.end():].strip()}
    exports = [f for f in ("docx", "md") if any(store.exports_dir(pid).glob(f"propuesta_*.{f}"))]
    return {"modo": prop["modo"], "marca": prop["marca"], "secciones": secciones, "sello": sello, "correo": correo, "exportaciones": exports}


def export_path(store: ProjectStore, pid: str, fmt: str) -> Path:
    store.require(pid)
    if fmt not in ("docx", "md"):
        raise not_found("El formato de exportación")
    files = sorted(store.exports_dir(pid).glob(f"propuesta_*.{fmt}"))
    if not files:
        raise pending("export")
    return files[0]


# ---------------------------------------------------------------- calidad
def _validation(store: ProjectStore, pid: str) -> dict[str, Any]:
    from geo.loader import load_muestra
    from geo.validation import compare

    mp = sf.study_file(store.study_dir(pid), "muestra_evaluada")
    ev = store.run_dir(pid) / "evaluaciones.parquet"
    if not mp.exists() or not ev.exists():
        return {"disponible": False, "campos": [], "n": 0}
    try:
        res = compare(pd.read_parquet(ev), load_muestra(mp))
    except Exception:
        return {"disponible": False, "campos": [], "n": 0}
    campos = []
    for campo, r in res.items():
        campos.append({"campo": campo, "exactitud": float(r.get("accuracy", 0.0)), "kappa": float(r.get("kappa", 0.0)),
                       "matriz": _clean({"etiquetas": r.get("labels", []), "valores": r.get("confusion_matrix", [])})})
    return {"disponible": True, "campos": campos, "n": int(max((r.get("n", 0) for r in res.values()), default=0))}


def get_quality(store: ProjectStore, pid: str) -> dict[str, Any]:
    store.require(pid)
    run = store.run_dir(pid)
    if not (run / "evaluaciones.parquet").exists():
        raise pending("judge")
    st = store.read_state(pid)
    nombres = {name: CHECKPOINTS[n][2] for n, (name, _, _) in CHECKPOINTS.items()}
    titles = {"checkpoint_0_brief": (0, "Ficha"), "checkpoint_1_competidores": (1, "Competencia"), "checkpoint_2_hallazgos": (2, "Hallazgos"), "checkpoint_3_plan": (3, "Plan")}
    aprob = []
    for a in st.get("human_approvals", []):
        n, nombre = titles.get(a["checkpoint"], (0, a["checkpoint"]))
        auto = str(a.get("note", "")).startswith("Auto-approve")
        aprob.append({"punto_control": n, "nombre": nombre, "fecha": a.get("timestamp", ""),
                      "nota": "Aprobación automática (modo continuo)" if auto else a.get("note"), "automatica": auto})
    ev = pd.read_parquet(run / "evaluaciones.parquet")
    disc = []
    resolved = read_json(run / "discrepancias.json", {}) or {}
    if "discrepancia" in ev.columns:
        df = _executions_df(store, pid)
        resp = dict(zip(df["Ejecucion_ID"], df["Respuesta completa"])) if not df.empty else {}
        for _, e in ev[ev["discrepancia"] == True].head(200).iterrows():  # noqa: E712
            if f"{e['ejecucion_id']}|{e['marca']}" in resolved:
                continue
            disc.append(_clean({"ejecucion_id": e["ejecucion_id"], "marca": e["marca"],
                                "reglas": {"aparece": bool(e["aparece"]), "tipo_mencion": e.get("tipo_mencion"), "fuerza": int(e["fuerza"])},
                                "llm": {"aparece": bool(e["aparece"]), "tipo_mencion": e.get("tipo_mencion"), "fuerza": int(e["fuerza"]), "confianza": float(e.get("confianza_juez", 0) or 0)},
                                "respuesta": resp.get(e["ejecucion_id"], ""), "fragmento": e.get("fragmento")}))
    ids = list(dict.fromkeys(ev["ejecucion_id"]))
    muestra = [ids[i] for i in range(0, len(ids), max(1, len(ids) // 15))][:15] if ids else []
    return {"validacion": _validation(store, pid), "discrepancias": disc, "aprobaciones": aprob, "muestra_para_etiquetar": muestra}


def add_labels(store: ProjectStore, pid: str, etiquetas: list[dict[str, Any]]) -> dict[str, Any]:
    """Guarda las etiquetas humanas como `muestra_evaluada.csv` del proyecto (formato del kit)."""
    store.require(pid)
    df = _executions_df(store, pid)
    if df.empty:
        raise pending("detect")
    by_id = {r["Ejecucion_ID"]: r for _, r in df.iterrows()}
    rows = []
    for e in etiquetas:
        r = by_id.get(e["ejecucion_id"])
        if r is None:
            raise unprocessable("ejecucion_desconocida", f"La ejecución {e['ejecucion_id']} no existe.")
        rows.append({"Sector": r.get("Sector", ""), "Marca": e["marca"], "Prompt_ID": r["Prompt_ID"], "Intención": r.get("Intención", ""),
                     "Prompt ejecutado": r["Prompt ejecutado"], "Motor": r["Motor"], "Repetición": r["Repetición"], "Aparece (1/0)": "1" if e["aparece"] else "0",
                     "Posición": "" if e.get("posicion") is None else str(e["posicion"]), "Peso posición": "", "Tipo de mención": e.get("tipo_mencion") or "",
                     "Fuente citada": "", "Respuesta completa": r["Respuesta completa"], "Fecha/hora": r.get("Fecha/hora", ""), "Notas": "Etiqueta humana (web)",
                     "Fuerza recomendación (-1 a 3)": str(e["fuerza"]), "Sentimiento": e.get("sentimiento") or "", "Tipo de fuente": e.get("tipo_fuente") or "",
                     "Fuera de territorio": "0", "Ejecucion_ID": e["ejecucion_id"]})
    path = sf.study_file(store.study_dir(pid), "muestra_evaluada")
    new = pd.DataFrame(rows, columns=list(sf._COLUMNS["muestra_evaluada"]))
    if path.exists() and not (store.study_dir(pid) / inputs.KIT_MARKER).exists():
        old = sf.read_csv(path)
        key = lambda d: d["Ejecucion_ID"] + "|" + d["Marca"]  # noqa: E731
        old = old[~key(old).isin(set(key(new)))]
        new = pd.concat([old, new], ignore_index=True)
    sf.write_csv(new, path)
    return get_quality(store, pid)


def resolve_discrepancy(store: ProjectStore, pid: str, eid: str, marca: str, valor: dict[str, Any]) -> dict[str, Any]:
    path = run_file(store, pid, "evaluaciones.parquet", "judge")
    ev = pd.read_parquet(path)
    mask = (ev["ejecucion_id"] == eid) & (ev["marca"] == marca)
    if not mask.any():
        raise not_found("La evaluación")
    allowed = {"aparece", "posicion", "tipo_mencion", "fuerza", "sentimiento", "tipo_fuente"}
    unknown = set(valor) - allowed
    if unknown:
        raise unprocessable("campo_no_valido", f"Campos no editables: {', '.join(sorted(unknown))}.")
    for k, v in valor.items():
        ev.loc[mask, k] = v
    ev.loc[mask, "juez"] = "humano"
    ev.loc[mask, "discrepancia"] = False
    ev.to_parquet(path, index=False)
    res = read_json(store.run_dir(pid) / "discrepancias.json", {}) or {}
    res[f"{eid}|{marca}"] = valor
    atomic_write_json(store.run_dir(pid) / "discrepancias.json", res)
    return get_quality(store, pid)
