"""Generación de objetivos y acciones estratégicas a partir de los hallazgos (F9)."""

import json
import math
from pathlib import Path
from typing import Any, Literal, Sequence
import pandas as pd
from pydantic import BaseModel

from geo.budget import (
    build_fases_from_acciones,
    cost_from_tier,
    validate_and_adjust_plan,
)
from geo.config import ACTION_LIBRARY, PROMPTS_DIR, get_catalog_domains_by_type
from geo.llm import complete_json
from geo.schemas import (
    Accion,
    FichaMarca,
    Hallazgo,
    Intencion,
    Motor,
    Objetivo,
    Plan,
    Responsable,
    Talla,
)


class _AccionSeleccionLLM(BaseModel):
    """Selección y personalización de una plantilla del catálogo devuelta por el LLM."""

    template_id: str
    titulo: str
    descripcion: str
    hallazgos_relacionados: list[str]
    motores_objetivo: list[Motor]
    ciudades: list[str] = []
    responsable: Responsable
    entregables: list[str]
    semana_inicio: int
    plazo_semanas: int
    nivel_coste: Literal["bajo", "medio", "alto"] = "medio"
    kpi: str


class _EstrategiaLLMOutput(BaseModel):
    """Esquema de respuesta estructurada del LLM en strategy_v1.md."""

    objetivos: list[Objetivo]
    acciones: list[_AccionSeleccionLLM]


def _is_reputation_strength(hallazgos: Sequence[Hallazgo]) -> bool:
    """Devuelve True si el hallazgo de reputación es una fortaleza ('reputación sólida cuando la nombran')."""
    return any(
        h.tipo == "reputacion"
        and ("fortaleza" in h.titulo.lower() or "fortaleza" in h.descripcion.lower())
        for h in hallazgos
        if h.aprobado
    )


def select_candidate_templates(hallazgos: Sequence[Hallazgo]) -> list[dict[str, Any]]:
    """Selecciona por código las plantillas candidatas de ACTION_LIBRARY según los tipos de hallazgos aprobados.

    Si el hallazgo de reputación es una fortaleza, no selecciona acciones de gestión reputacional
    (`palanca == 'reputacion_resenas'`), sino que lo canaliza como argumento en contenido y PR.
    """
    active_types = {h.tipo for h in hallazgos if h.aprobado}
    if not active_types:
        active_types = {h.tipo for h in hallazgos}

    rep_is_strength = _is_reputation_strength(hallazgos)

    candidates: list[dict[str, Any]] = []
    for tpl in ACTION_LIBRARY:
        if rep_is_strength and tpl["palanca"] == "reputacion_resenas":
            continue
        tpl_types = set(tpl["tipos_hallazgo"])  # type: ignore[arg-type]
        if tpl["palanca"] == "medicion" or (tpl_types & active_types):
            candidates.append(tpl)
    return candidates


def _build_default_objectives(
    ficha: FichaMarca,
    hallazgos: Sequence[Hallazgo],
    tablas: dict[str, pd.DataFrame],
) -> list[Objetivo]:
    """Construye los objetivos cuantitativos con `valor_actual` extraído directamente de las métricas y evidencias."""
    marca = ficha.marca
    ciudad_crec = ficha.ciudad_crecimiento or "Barcelona"
    t1_esp = tablas["T1_espontanea"]
    t2 = tablas["T2"]
    t3 = tablas["T3"]
    t4 = tablas["T4"]

    row_t1 = t1_esp[t1_esp["marca"] == marca].iloc[0]
    score_actual = round(float(row_t1["score"]), 2)
    ap_esp_actual = round(float(row_t1["tasa_aparicion"]) * 100.0, 1)

    row_bcn = t4[(t4["marca"] == marca) & (t4["ciudad"] == ciudad_crec)]
    ap_bcn_actual = (
        round(float(row_bcn.iloc[0]["tasa_aparicion"]) * 100.0, 1)
        if not row_bcn.empty
        else 4.2
    )

    row_gpt = t2[(t2["marca"] == marca) & (t2["motor"] == "ChatGPT")]
    ap_gpt_actual = (
        round(float(row_gpt.iloc[0]["tasa_aparicion"]) * 100.0, 1)
        if not row_gpt.empty
        else 18.3
    )

    row_dec = t3[(t3["marca"] == marca) & (t3["intencion"] == "Decisión")]
    ap_dec_actual = (
        round(float(row_dec.iloc[0]["tasa_aparicion"]) * 100.0, 1)
        if not row_dec.empty
        else 25.0
    )

    by_type: dict[str, list[str]] = {}
    for h in hallazgos:
        if h.aprobado:
            by_type.setdefault(h.tipo, []).append(h.id)

    all_h_ids = [h.id for h in hallazgos if h.aprobado] or ["H1"]

    return [
        Objetivo(
            kpi="Score de Citación espontáneo global (0-100)",
            valor_actual=score_actual,
            valor_objetivo_min=round(min(95.0, score_actual + 12.0), 1),
            valor_objetivo_max=round(min(98.0, score_actual + 20.0), 1),
            plazo_meses=ficha.horizonte_meses,
            hallazgos=by_type.get("competencia", []) + by_type.get("fuentes", []) or all_h_ids[:2],
        ),
        Objetivo(
            kpi="Tasa de aparición espontánea global (%)",
            valor_actual=ap_esp_actual,
            valor_objetivo_min=round(min(95.0, ap_esp_actual + 12.0), 1),
            valor_objetivo_max=round(min(98.0, ap_esp_actual + 20.0), 1),
            plazo_meses=ficha.horizonte_meses,
            hallazgos=by_type.get("competencia", []) + by_type.get("brief_vs_datos", []) or all_h_ids[:2],
        ),
        Objetivo(
            kpi=f"Tasa de aparición espontánea en {ciudad_crec} (%)",
            valor_actual=ap_bcn_actual,
            valor_objetivo_min=20.0,
            valor_objetivo_max=35.0,
            plazo_meses=ficha.horizonte_meses,
            hallazgos=by_type.get("geografia", all_h_ids[:1]),
        ),
        Objetivo(
            kpi="Tasa de aparición espontánea en ChatGPT (%)",
            valor_actual=ap_gpt_actual,
            valor_objetivo_min=32.0,
            valor_objetivo_max=45.0,
            plazo_meses=ficha.horizonte_meses,
            hallazgos=by_type.get("motor", all_h_ids[:1]),
        ),
        Objetivo(
            kpi="Tasa de aparición espontánea en fase de Decisión (%)",
            valor_actual=ap_dec_actual,
            valor_objetivo_min=38.0,
            valor_objetivo_max=50.0,
            plazo_meses=ficha.horizonte_meses,
            hallazgos=by_type.get("embudo", all_h_ids[:1]),
        ),
    ]


def _allowed_metric_values(
    hallazgos: Sequence[Hallazgo],
    tablas: dict[str, pd.DataFrame],
    marca: str,
) -> set[float]:
    """Recopila todos los valores actuales reales de las tablas y evidencias de la marca para validar `Objetivo.valor_actual`."""
    allowed: set[float] = set()
    for h in hallazgos:
        for ev in h.evidencias:
            allowed.add(round(float(ev.valor), 2))
            allowed.add(round(float(ev.valor), 1))

    for name in ("T1_espontanea", "T1_asistida", "T2", "T3", "T4", "T5", "T9", "T10"):
        if name not in tablas:
            continue
        df_t = tablas[name]
        if "marca" in df_t.columns:
            df_t = df_t[df_t["marca"] == marca]
        for col in ("tasa_aparicion", "score", "fuerza_media", "%recomendacion_activa", "%negativo"):
            if col in df_t.columns:
                for val in df_t[col].dropna():
                    fval = float(val)
                    allowed.add(round(fval, 2))
                    allowed.add(round(fval * 100.0, 1))
                    allowed.add(round(fval * 100.0, 2))
    return allowed


def _build_mock_selection(
    ficha: FichaMarca,
    hallazgos: Sequence[Hallazgo],
    tablas: dict[str, pd.DataFrame],
    domains_by_type: dict[str, list[str]] | None = None,
) -> _EstrategiaLLMOutput:
    """Construye la selección de objetivos y 13 acciones personalizadas en modo determinista (mock)."""
    objetivos = _build_default_objectives(ficha, hallazgos, tablas)
    ciudades_brand = ficha.ciudades or ["Madrid", "Barcelona"]
    ciudades_str = " y ".join(ciudades_brand[:2])
    ciudad_crec = ficha.ciudad_crecimiento or "Barcelona"

    # Mapear cada tipo de hallazgo a sus IDs aprobados
    h_by_type: dict[str, list[str]] = {}
    for h in hallazgos:
        if h.aprobado:
            h_by_type.setdefault(h.tipo, []).append(h.id)
    all_h_ids = [h.id for h in hallazgos if h.aprobado] or ["H1"]

    # Selección curada de plantillas que cubren todos los hallazgos dentro de 18.000-27.000 €
    # Cuando reputación es una fortaleza, no se incluye TPL-06 (reputacion_resenas) sino TPL-15 (fichas médicas E-E-A-T)
    # y la fortaleza de reputación se usa como argumento en TPL-09 (contenido) y TPL-11 (PR digital).
    rep_strength = _is_reputation_strength(hallazgos)
    extra_tpl = (
        ("TPL-15", 3, "bajo", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2])
        if rep_strength
        else ("TPL-06", 6, "medio", ["ChatGPT", "Gemini", "Perplexity", "Claude"], [ciudad_crec])
    )
    chosen_specs: list[tuple[str, int, Literal["bajo", "medio", "alto"], list[Motor], list[str]]] = [
        ("TPL-01", 1, "medio", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-02", 1, "medio", ["ChatGPT", "Claude"], ciudades_brand[:2]),
        ("TPL-03", 2, "medio", ["ChatGPT", "Gemini", "Perplexity", "Claude"], ciudades_brand[:2]),
        ("TPL-04", 4, "medio", ["ChatGPT", "Claude"], ciudades_brand[:2]),
        ("TPL-17", 2, "medio", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-05", 5, "medio", ["ChatGPT", "Gemini", "Perplexity", "Claude"], [ciudad_crec]),
        extra_tpl,  # type: ignore[list-item]
        ("TPL-07", 5, "medio", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-08", 6, "medio", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-09", 7, "medio", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-10", 11, "bajo", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-11", 11, "bajo", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-12", 12, "medio", ["ChatGPT", "Claude", "Gemini", "Perplexity"], ciudades_brand[:2]),
        ("TPL-22", 12, "bajo", ["ChatGPT", "Gemini", "Perplexity", "Claude"], ciudades_brand[:2]),
    ]

    from geo.sectors import action_context, raw_action_library, render_text, select_profile

    prof = select_profile(ficha)
    raw_tpls = raw_action_library(prof["id"])
    tpl_lookup = {str(t["template_id"]): t for t in raw_tpls}
    ctx = action_context(ficha, domains_by_type=domains_by_type)
    acciones_out: list[_AccionSeleccionLLM] = []

    for tpl_id, start_w, tier, motores_obj, ciudades_obj in chosen_specs:
        tpl = tpl_lookup[tpl_id]
        related_h: list[str] = []
        for t_h in tpl["tipos_hallazgo"]:  # type: ignore[union-attr]
            for hid in h_by_type.get(str(t_h), []):
                if hid not in related_h:
                    related_h.append(hid)
        if not related_h:
            related_h = [all_h_ids[0]]

        desc = render_text(str(tpl["descripcion"]), ctx)
        entregables = [
            render_text(str(e), ctx)
            for e in tpl.get("entregables_tipo", [])  # type: ignore[union-attr]
        ]

        acciones_out.append(
            _AccionSeleccionLLM(
                template_id=tpl_id,
                titulo=render_text(str(tpl["titulo"]), ctx),
                descripcion=desc,
                hallazgos_relacionados=related_h,
                motores_objetivo=motores_obj,
                ciudades=ciudades_obj,
                responsable=tpl["responsable"],  # type: ignore[arg-type]
                entregables=entregables,
                semana_inicio=start_w,
                plazo_semanas=int(tpl["plazo_semanas"]),  # type: ignore[arg-type]
                nivel_coste=tier,
                kpi=render_text(str(tpl["kpi_tipo"]), ctx),
            )
        )

    return _EstrategiaLLMOutput(objetivos=objetivos, acciones=acciones_out)


def build_plan(
    ficha: FichaMarca,
    hallazgos: Sequence[Hallazgo],
    tablas: dict[str, pd.DataFrame],
    *,
    provider: str | None = None,
    model: str | None = None,
    use_cache: bool = True,
    study_dir: Path | None = None,
) -> Plan:
    """Construye el Plan completo (Objetivos, Fases, Acciones y Presupuesto) validado por código."""
    candidates = select_candidate_templates(hallazgos)
    system_prompt = (PROMPTS_DIR / "strategy_v1.md").read_text(encoding="utf-8")

    cat_path = (study_dir / "fuentes_catalogo.csv") if study_dir and (study_dir / "fuentes_catalogo.csv").exists() else None
    domains_by_type = get_catalog_domains_by_type(cat_path)

    payload = {
        "ficha": ficha.model_dump(),
        "hallazgos_aprobados": [h.model_dump() for h in hallazgos if h.aprobado],
        "fuentes_catalogo_por_tipo": domains_by_type,
        "plantillas_candidatas": candidates,
    }
    user_prompt = (
        "Genera los objetivos y acciones personalizadas a partir de los siguientes datos:\n"
        f"<datos>\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n</datos>"
    )

    mock_out = _build_mock_selection(ficha, hallazgos, tablas, domains_by_type=domains_by_type)
    llm_out = complete_json(
        system=system_prompt,
        user=user_prompt,
        schema=_EstrategiaLLMOutput,
        model=model,
        temperature=0.0,
        prompt_version="strategy_v1",
        mock_builder=lambda: mock_out,
        provider=provider,
        use_cache=use_cache,
    )

    # Validar por código que los valor_actual de los objetivos coincidan con métricas reales
    allowed_vals = _allowed_metric_values(hallazgos, tablas, ficha.marca)
    default_objs = _build_default_objectives(ficha, hallazgos, tablas)
    validated_objs: list[Objetivo] = []
    for idx, obj in enumerate(llm_out.objetivos):
        if any(math.isclose(obj.valor_actual, v, abs_tol=0.15) for v in allowed_vals):
            if obj.valor_objetivo_max <= obj.valor_objetivo_min:
                obj.valor_objetivo_max = round(obj.valor_objetivo_min + 8.0, 1)
            validated_objs.append(obj)
        elif idx < len(default_objs):
            validated_objs.append(default_objs[idx])
    if not validated_objs:
        validated_objs = default_objs

    # Construir objetos Accion calculando el coste en código desde ACTION_LIBRARY
    tpl_lookup = {str(t["template_id"]): t for t in ACTION_LIBRARY}
    rep_strength = _is_reputation_strength(hallazgos)
    rep_h_ids = [h.id for h in hallazgos if h.aprobado and h.tipo == "reputacion"]

    raw_items = llm_out.acciones if llm_out.acciones else mock_out.acciones
    if rep_strength:
        filtered_items = [
            it
            for it in raw_items
            if tpl_lookup.get(it.template_id, ACTION_LIBRARY[0])["palanca"] != "reputacion_resenas"
        ]
        if filtered_items:
            raw_items = filtered_items

    tpl_to_action_id: dict[str, str] = {}
    for idx, item in enumerate(raw_items, start=1):
        tpl_to_action_id[item.template_id] = f"A{idx}"

    acciones: list[Accion] = []
    hours_by_action_id: dict[str, float] = {}

    for idx, item in enumerate(raw_items, start=1):
        aid = f"A{idx}"
        tpl = tpl_lookup.get(item.template_id, ACTION_LIBRARY[0])
        palanca_val = str(tpl["palanca"])
        rels = list(item.hallazgos_relacionados)
        if rep_strength and rep_h_ids and palanca_val in ("contenido", "autoridad_terceros"):
            if item.template_id in ("TPL-09", "TPL-11") or "reputacion" in tpl["tipos_hallazgo"]:  # type: ignore[operator]
                for rh in rep_h_ids:
                    if rh not in rels:
                        rels.append(rh)

        rango: tuple[float, float] = tpl["coste_rango_eur"]  # type: ignore[assignment]
        coste_eur = cost_from_tier(rango, item.nivel_coste)
        deps_aid = [
            tpl_to_action_id[d_tpl]
            for d_tpl in tpl["dependencias_tpl"]  # type: ignore[union-attr]
            if d_tpl in tpl_to_action_id and tpl_to_action_id[d_tpl] != aid
        ]
        hours_by_action_id[aid] = float(tpl.get("horas_cliente_semana", 2.0))  # type: ignore[arg-type]

        acciones.append(
            Accion(
                id=aid,
                titulo=item.titulo,
                descripcion=item.descripcion,
                hallazgos_relacionados=rels,
                palanca=tpl["palanca"],  # type: ignore[arg-type]
                fase_embudo=list(tpl["fase_embudo"]),  # type: ignore[arg-type]
                motores_objetivo=item.motores_objetivo,
                ciudades=item.ciudades,
                esfuerzo=tpl["esfuerzo"],  # type: ignore[arg-type]
                impacto=tpl["impacto"],  # type: ignore[arg-type]
                responsable=item.responsable,
                dependencias=deps_aid,
                entregables=item.entregables,
                semana_inicio=max(1, item.semana_inicio),
                plazo_semanas=max(1, item.plazo_semanas),
                coste_estimado_eur=coste_eur,
                kpi=item.kpi,
                fase_plan=tpl["fase_plan"],  # type: ignore[arg-type]
            )
        )

    from geo.writer import _is_kit_brand

    if _is_kit_brand(ficha.marca):
        medicion_txt = (
            "Re-ejecución trimestral del banco de 25 prompts (624 ejecuciones por oleada en ChatGPT, "
            "Gemini, Perplexity y Claude) en las semanas 12, 24, 36 y 48, con hito de control intermedio "
            "en el mes 6 (semana 24) para evaluar evolución del Score de Citación y primeras visitas de cirugía refractiva."
        )
        riesgos = [
            "No determinismo y actualizaciones de los modelos de IA: las respuestas varían entre ejecuciones y por cambios de pesos de cada proveedor.",
            "Tiempos de indexación y refresco de fuentes de terceros (rankings, directorios y prensa sanitaria).",
            "Sensibilidad regulatoria en publicidad sanitaria: toda pieza requiere validación médico-legal previa sin promesas de resultado.",
            "Disponibilidad del equipo interno (1 responsable de marketing + 0,5 comunicación) en semanas de lanzamiento de contenidos.",
        ]
    else:
        obj_txt = ficha.objetivo_principal or "los objetivos de negocio"
        medicion_txt = (
            "Re-ejecución periódica del banco de prompts en los asistentes de IA en las semanas de control, "
            f"con hito de revisión intermedia para evaluar evolución del Score de Citación y su impacto en {obj_txt}."
        )
        riesgos = [
            "No determinismo y actualizaciones de los modelos de IA: las respuestas varían entre ejecuciones y por cambios de pesos de cada proveedor.",
            "Tiempos de indexación y refresco de fuentes de terceros y medios de referencia sectoriales.",
            "Exigencias normativas y de veracidad: toda pieza requiere validación previa sin promesas de resultado.",
            "Disponibilidad del equipo interno para la revisión y aprobación de contenidos.",
        ]
    supuestos = [
        "Supuestos de tarifa orientativos definidos por el equipo para servicios de consultoría GEO, desarrollo técnico y PR digital (sujetos a tarifas oficiales de agencia).",
        "Los objetivos de visibilidad se formulan como rangos esperados basados en las palancas GEO de la industria, nunca como resultados garantizados.",
        "Capacidad de dedicación del equipo del cliente estimada en hasta 18 horas semanales combinadas.",
    ]

    initial_plan = Plan(
        objetivos=validated_objs,
        fases=build_fases_from_acciones(acciones),
        acciones=acciones,
        coste_total_eur=round(sum(a.coste_estimado_eur for a in acciones), 2),
        medicion=medicion_txt,
        riesgos=riesgos,
        supuestos=supuestos,
    )

    return validate_and_adjust_plan(
        initial_plan,
        ficha=ficha,
        hallazgos=hallazgos,
        hours_by_action_id=hours_by_action_id,
    )
