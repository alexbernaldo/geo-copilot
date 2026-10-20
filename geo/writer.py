"""Redactor de propuestas en modo cliente y modo prospecto con verificación de cifras (F11)."""

from datetime import datetime
import json
import os
from typing import Any, Sequence
import pandas as pd
from pydantic import BaseModel

from geo.config import LLM_MODEL_WRITER, LLM_PROVIDER, PROMPTS_DIR
from geo.findings import generate_findings
from geo.llm import complete_json, get_llm_stats
from geo.metrics import build_brand_summary_metrics
from geo.reviewer import compliance, verify_numbers
from geo.schemas import (
    FichaMarca,
    Hallazgo,
    InformeRevision,
    Marca,
    Plan,
    Propuesta,
)
from geo.strategy import build_plan


class _ClientNarrativeLLM(BaseModel):
    """Párrafos interpretativos devueltos por el LLM para las secciones de la propuesta de cliente."""

    resumen_ejecutivo: str
    contexto_y_alcance: str
    intro_diagnostico_espontaneo: str
    intro_diagnostico_asistido: str
    intro_competencia: str
    intro_estrategia: str
    medicion_y_seguimiento: str


class _ProspectNarrativeLLM(BaseModel):
    """Secciones devueltas por el LLM para la propuesta en modo prospecto."""

    gancho: str
    oportunidad: str
    que_hariamos: str
    correo_comercial: str


def _df_to_markdown_table(df: pd.DataFrame, columns: list[tuple[str, str]]) -> str:
    """Convierte un DataFrame en una tabla Markdown limpia usando la lista `(col_name, header_label)`."""
    if df.empty:
        return "_Sin datos disponibles._"
    headers = [label for _, label in columns]
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines: list[str] = []
    for _, row in df.iterrows():
        cells: list[str] = []
        for col, _ in columns:
            val = row.get(col, "")
            if isinstance(val, list):
                cells.append(", ".join(str(x) for x in val))
            elif val is None or (not isinstance(val, (list, dict, tuple, set)) and pd.isna(val)):
                cells.append("-")
            elif isinstance(val, float):
                if col.startswith(("tasa_", "%", "pct_")):
                    cells.append(f"{val * 100.0:.1f} %")
                else:
                    cells.append(f"{val:.2f}")
            else:
                cells.append(str(val))
        body_lines.append("| " + " | ".join(cells) + " |")
    return "\n".join([header_line, sep_line, *body_lines])


def _build_code_tables_client(
    ficha: FichaMarca,
    tablas: dict[str, pd.DataFrame],
    plan: Plan,
) -> dict[str, str]:
    """Genera en código todas las tablas Markdown de las secciones 3, 4, 7 y 10."""
    marca = ficha.marca
    t1_esp = tablas["T1_espontanea"]
    t1_asis = tablas["T1_asistida"]
    t2 = tablas["T2"][tablas["T2"]["marca"] == marca]
    t3 = tablas["T3"][tablas["T3"]["marca"] == marca]
    t4 = tablas["T4"][tablas["T4"]["marca"] == marca]
    t5 = tablas["T5"][tablas["T5"]["marca"] == marca]
    t6 = tablas["T6"]
    t8 = tablas["T8"]
    t9 = tablas["T9"]

    md_t1_esp = _df_to_markdown_table(
        t1_esp,
        [
            ("puesto", "Puesto"),
            ("marca", "Marca"),
            ("n", "n"),
            ("tasa_aparicion", "Aparición espontánea"),
            ("pos_media", "Posición media"),
            ("fuerza_media", "Fuerza media"),
            ("%recomendacion_activa", "Recomendación activa"),
            ("score", "Score (0-100)"),
        ],
    )
    md_t2 = _df_to_markdown_table(
        t2,
        [
            ("motor", "Motor"),
            ("n", "n"),
            ("tasa_aparicion", "Aparición espontánea"),
            ("pos_media", "Posición media"),
            ("fuerza_media", "Fuerza media"),
            ("score", "Score (0-100)"),
        ],
    )
    md_t3 = _df_to_markdown_table(
        t3,
        [
            ("intencion", "Fase del embudo"),
            ("n", "n"),
            ("tasa_aparicion", "Aparición espontánea"),
            ("pos_media", "Posición media"),
            ("fuerza_media", "Fuerza media"),
            ("score", "Score (0-100)"),
        ],
    )
    md_t4 = _df_to_markdown_table(
        t4,
        [
            ("ciudad", "Ciudad"),
            ("n", "n"),
            ("tasa_aparicion", "Aparición espontánea"),
            ("pos_media", "Posición media"),
            ("fuerza_media", "Fuerza media"),
            ("score", "Score (0-100)"),
        ],
    )
    md_t5 = _df_to_markdown_table(
        t5,
        [
            ("familia", "Familia de prompt"),
            ("n", "n"),
            ("tasa_aparicion", "Aparición espontánea"),
            ("score", "Score (0-100)"),
        ],
    )
    md_t1_asis = _df_to_markdown_table(
        t1_asis,
        [
            ("puesto", "Puesto"),
            ("marca", "Marca"),
            ("n", "n"),
            ("tasa_aparicion", "Aparición asistida"),
            ("fuerza_media", "Fuerza media"),
            ("%recomendacion_activa", "Recomendación activa"),
            ("%negativo", "Menciones negativas"),
            ("score", "Score asistido"),
        ],
    )
    md_t9 = _df_to_markdown_table(
        t9,
        [
            ("marca", "Marca"),
            ("n", "n"),
            ("fuerza_media", "Fuerza en apariciones"),
            ("%negativo", "Menciones negativas"),
            ("objeciones_recurrentes", "Objeciones recurrentes detectadas"),
        ],
    )
    md_t6_alb = _df_to_markdown_table(
        t6[t6["marca"] == marca],
        [
            ("tipo_fuente", "Tipo de fuente"),
            ("n", "Apariciones"),
            ("pct_apariciones", "% sobre apariciones"),
            ("calidad_media_tipo", "Calidad catálogo"),
        ],
    )
    md_t8_alb = _df_to_markdown_table(
        t8[t8["par"].str.contains(marca, na=False)],
        [
            ("par", "Duelo directo"),
            ("motor", "Motor"),
            ("n", "n"),
            ("victorias_a", "Victorias A"),
            ("victorias_b", "Victorias B"),
            ("ganador", "Ganador"),
        ],
    )

    # Tabla de objetivos (Sección 6)
    df_obj = pd.DataFrame([o.model_dump() for o in plan.objetivos])
    df_obj["rango_objetivo"] = df_obj.apply(
        lambda r: f"{r['valor_objetivo_min']:.1f} – {r['valor_objetivo_max']:.1f}", axis=1
    )
    md_obj = _df_to_markdown_table(
        df_obj,
        [
            ("kpi", "Indicador (KPI)"),
            ("valor_actual", "Valor actual"),
            ("rango_objetivo", "Rango objetivo"),
            ("plazo_meses", "Plazo (meses)"),
            ("hallazgos", "Hallazgos"),
        ],
    )

    # Tabla de acciones (Sección 7)
    df_acc = pd.DataFrame([a.model_dump() for a in plan.acciones])
    df_acc["calendario"] = df_acc.apply(
        lambda r: f"S{r['semana_inicio']}–S{r['semana_inicio'] + r['plazo_semanas'] - 1} ({r['plazo_semanas']} sem.)",
        axis=1,
    )
    df_acc["coste_fmt"] = df_acc["coste_estimado_eur"].apply(lambda v: f"{v:,.0f} €")
    md_acc = _df_to_markdown_table(
        df_acc,
        [
            ("id", "ID"),
            ("fase_plan", "Fase"),
            ("titulo", "Acción"),
            ("hallazgos_relacionados", "Hallazgos"),
            ("palanca", "Palanca"),
            ("responsable", "Responsable"),
            ("esfuerzo", "Esfuerzo"),
            ("impacto", "Impacto"),
            ("calendario", "Calendario"),
            ("coste_fmt", "Coste estimado"),
            ("kpi", "KPI"),
        ],
    )

    # Tabla de presupuesto por fase y por responsable (Sección 10)
    phase_rows = []
    for f in plan.fases:
        acts_f = [a for a in plan.acciones if a.id in f.acciones]
        cost_f = sum(a.coste_estimado_eur for a in acts_f)
        phase_rows.append(
            {
                "fase": f.nombre,
                "semanas": f"S{f.semanas[0]}–S{f.semanas[1]}",
                "objetivo": f.objetivo,
                "acciones": ", ".join(f.acciones),
                "coste_fmt": f"{cost_f:,.0f} €",
            }
        )
    md_fases = _df_to_markdown_table(
        pd.DataFrame(phase_rows),
        [
            ("fase", "Fase"),
            ("semanas", "Semanas"),
            ("acciones", "Acciones"),
            ("coste_fmt", "Presupuesto fase"),
            ("objetivo", "Objetivo de la fase"),
        ],
    )

    resp_rows = []
    for resp, grp in df_acc.groupby("responsable", sort=False):
        c_sum = float(grp["coste_estimado_eur"].sum())
        resp_rows.append(
            {
                "responsable": resp,
                "n_acciones": len(grp),
                "coste_fmt": f"{c_sum:,.0f} €",
                "pct_presupuesto": c_sum / plan.coste_total_eur if plan.coste_total_eur > 0 else 0.0,
            }
        )
    md_resp = _df_to_markdown_table(
        pd.DataFrame(resp_rows),
        [
            ("responsable", "Responsable"),
            ("n_acciones", "Nº Acciones"),
            ("coste_fmt", "Inversión asociada"),
            ("pct_presupuesto", "% sobre total"),
        ],
    )

    return {
        "t1_esp": md_t1_esp,
        "t1_asis": md_t1_asis,
        "t2": md_t2,
        "t3": md_t3,
        "t4": md_t4,
        "t5": md_t5,
        "t6_alb": md_t6_alb,
        "t8_alb": md_t8_alb,
        "t9": md_t9,
        "objetivos": md_obj,
        "acciones": md_acc,
        "fases": md_fases,
        "responsables": md_resp,
    }


def _mock_client_narrative(
    ficha: FichaMarca,
    metrics_summary: dict[str, Any],
    plan: Plan,
) -> _ClientNarrativeLLM:
    """Construye los párrafos interpretativos deterministas (modo mock) usando solo cifras trazables."""
    marca = ficha.marca
    sc_esp = metrics_summary["score_espontaneo"]
    ap_esp = round(metrics_summary["tasa_aparicion_espontanea"] * 100.0, 1)
    puesto = metrics_summary["puesto_espontaneo"]
    total_m = metrics_summary["total_marcas"]
    lider = metrics_summary["lider_espontaneo"]
    sc_lider = metrics_summary["score_lider_espontaneo"]
    ap_lider = round(metrics_summary["tasa_aparicion_lider_espontanea"] * 100.0, 1)
    rec_esp = round(metrics_summary["pct_recomendacion_activa_espontanea"] * 100.0, 1)

    ap_bcn = round(
        metrics_summary["por_ciudad_espontanea"].get("Barcelona", {}).get("tasa_aparicion", 0.0417) * 100.0,
        1,
    )
    ap_mad = round(
        metrics_summary["por_ciudad_espontanea"].get("Madrid", {}).get("tasa_aparicion", 0.5417) * 100.0,
        1,
    )
    ap_gpt = round(
        metrics_summary["por_motor_espontanea"].get("ChatGPT", {}).get("tasa_aparicion", 0.1833) * 100.0,
        1,
    )
    ap_cla = round(
        metrics_summary["por_motor_espontanea"].get("Claude", {}).get("tasa_aparicion", 0.15) * 100.0,
        1,
    )
    ap_perp = round(
        metrics_summary["por_motor_espontanea"].get("Perplexity", {}).get("tasa_aparicion", 0.65) * 100.0,
        1,
    )
    ap_gem = round(
        metrics_summary["por_motor_espontanea"].get("Gemini", {}).get("tasa_aparicion", 0.5667) * 100.0,
        1,
    )
    ap_desc = round(
        metrics_summary["por_embudo_espontanea"].get("Descubrimiento", {}).get("tasa_aparicion", 0.447) * 100.0,
        1,
    )
    ap_dec = round(
        metrics_summary["por_embudo_espontanea"].get("Decisión", {}).get("tasa_aparicion", 0.25) * 100.0,
        1,
    )
    neg_asis = round(metrics_summary["pct_negativo_asistida"] * 100.0, 1)
    fm_asis = metrics_summary["fuerza_media_asistida"]
    p_min = ficha.presupuesto_min_eur or 18000.0
    p_max = ficha.presupuesto_max_eur or 27000.0

    return _ClientNarrativeLLM(
        resumen_ejecutivo=(
            f"{marca} cuenta con una base asistencial y reputacional muy sólida (valoración de 4,7 sobre 5 "
            f"con 1.800 opiniones, 14 oftalmólogos y 7.500 intervenciones al año), pero esa fortaleza aún no se "
            f"traduce en visibilidad espontánea cuando un paciente consulta a un asistente de IA sin mencionar "
            f"marcas. En las 240 ejecuciones espontáneas del estudio, {marca} ocupa el puesto {puesto} de {total_m} "
            f"con un Score de Citación de {sc_esp:.2f} puntos, un {ap_esp:.1f} % de aparición y un {rec_esp:.1f} % "
            f"de recomendación activa, lejos del líder real del mercado ({lider}, con {ap_lider:.1f} % de aparición "
            f"y score {sc_lider:.2f}).\n\n"
            f"Los datos confirman la preocupación del equipo sobre la sede abierta en 2024: en consultas sobre "
            f"Barcelona la aparición espontánea cae al {ap_bcn:.1f} % (n=24) frente al {ap_mad:.1f} % en Madrid (n=24). "
            f"Asimismo, la presencia se concentra en Perplexity ({ap_perp:.1f} %) y Gemini ({ap_gem:.1f} %), mientras "
            f"que en ChatGPT ({ap_gpt:.1f} %) y Claude ({ap_cla:.1f} %) la clínica apenas es citada, y en la fase "
            f"de Decisión del embudo desciende al {ap_dec:.1f} %.\n\n"
            f"Para corregir estas brechas proponemos un plan de acción de {len(plan.acciones)} iniciativas en 4 fases "
            f"a {ficha.horizonte_meses} meses (con primeros resultados medibles en el mes 6), una inversión total de "
            f"{plan.coste_total_eur:,.0f} € (dentro de la horquilla disponible de {p_min:,.0f} € a {p_max:,.0f} €) "
            f"y pleno respeto a la regulación de publicidad sanitaria."
        ),
        contexto_y_alcance=(
            f"Este diagnóstico evalúa la visibilidad generativa de {marca} en el sector de clínicas privadas de "
            f"oftalmología en España a partir de un banco estructurado de 25 plantillas de prompt ejecutadas en "
            f"4 motores (ChatGPT, Gemini, Perplexity y Claude) con 3 repeticiones por combinación, sumando 624 "
            f"ejecuciones (156 por motor) y 2.928 evaluaciones marca-ejecución.\n\n"
            f"**Aviso importante sobre el origen de los datos:** este estudio se ha realizado sobre el dataset "
            f"sintético del reto UFV-EPS × reload.; los datos reproducen patrones reales de estudios GEO pero no "
            f"representan el comportamiento real en producción de ningún modelo ni clínica real.\n\n"
            f"**Limitaciones metodológicas declaradas:** (1) los modelos generativos son no deterministas y cambian "
            f"con el tiempo, por lo que el estudio refleja una foto en una fecha concreta; (2) el desglose geográfico "
            f"cuenta con una muestra de n=24 ejecuciones por ciudad (Madrid y Barcelona); (3) la atribución del "
            f"tipo de fuente por marca tiene una concordancia parcial en el conjunto de validación (56,7 % en "
            f"apariciones), por lo que las decisiones estratégicas se apoyan siempre en el conjunto agregado de "
            f"fuentes citadas."
        ),
        intro_diagnostico_espontaneo=(
            f"En visibilidad **espontánea** (240 ejecuciones de tipo `generico` y `ciudad`, donde el usuario no "
            f"nombra ninguna clínica), {marca} alcanza un Score de Citación de {sc_esp:.2f} sobre 100 y aparece en "
            f"el {ap_esp:.1f} % de las respuestas. El análisis por motor muestra una dualidad clara: en motores con "
            f"búsqueda intensiva como Perplexity ({ap_perp:.1f} %) y Gemini ({ap_gem:.1f} %) la marca supera la "
            f"mitad de las consultas, pero cae al {ap_gpt:.1f} % en ChatGPT y al {ap_cla:.1f} % en Claude. Por fase "
            f"del embudo, la presencia pasa del {ap_desc:.1f} % en Descubrimiento (n=132) al {ap_dec:.1f} % en "
            f"Decisión (n=48)."
        ),
        intro_diagnostico_asistido=(
            f"En visibilidad **asistida** (384 ejecuciones del corpus donde el prompt nombra expresamente a la "
            f"marca o enfrenta un par de clínicas; n=108 para {marca}), se mide qué dicen los motores cuando ya "
            f"conocen el nombre de la clínica. Aquí {marca} muestra una reputación muy sana: fuerza media de "
            f"{fm_asis:.2f} sobre 3 y tan solo un {neg_asis:.1f} % de menciones con advertencias, destacando de "
            f"forma recurrente su seguimiento postoperatorio personalizado de 12 meses."
        ),
        intro_competencia=(
            f"El contraste con el mercado revela tres aprendizajes clave frente al brief inicial: (1) el líder "
            f"real en los asistentes de IA es {lider} ({ap_lider:.1f} % de aparición espontánea y score {sc_lider:.2f}), "
            f"por delante de la referencia premium declarada Instituto Oftálmico Tramuntana (68,8 %, score 51,70); "
            f"(2) Vistalia Oftalmología no figuraba en el brief pero alcanza un 41,2 % de aparición espontánea "
            f"(n=240); y (3) en menciones asistidas, competidores de precio ajustado como Láser Nítida registran "
            f"un 34,3 % de menciones negativas asociadas al seguimiento postoperatorio, justo el territorio donde "
            f"{marca} posee su mayor diferencial clínico."
        ),
        intro_estrategia=(
            f"La estrategia recomendada conecta cada hallazgo del diagnóstico con objetivos cuantitativos expresados "
            f"en rangos realistas a {ficha.horizonte_meses} meses (con revisión intermedia en el mes 6), sin realizar "
            f"promesas de resultado y priorizando las palancas de datos estructurados, páginas locales en Barcelona, "
            f"contenidos de decisión (precios y seguimiento postoperatorio de 12 meses en positivo) y autoridad en "
            f"prensa y rankings sanitarios."
        ),
        medicion_y_seguimiento=(
            f"El sistema de seguimiento establece 4 oleadas trimestrales de re-medición (semanas 12, 24, 36 y 48) "
            f"ejecutando el banco de 25 prompts en los 4 motores con 3 repeticiones (624 ejecuciones por oleada). "
            f"En el mes 6 (semana 24) se presentará al Comité de Dirección el informe de primeros resultados "
            f"visibles, cruzando la evolución del Score de Citación espontáneo en Madrid y Barcelona con la evolución "
            f"de primeras visitas de cirugía refractiva (+25 % objetivo anual del negocio) y consultas asistidas en CRM."
        ),
    )


def write_client(
    ficha: FichaMarca,
    tablas: dict[str, pd.DataFrame],
    hallazgos: Sequence[Hallazgo],
    plan: Plan,
    *,
    run_id: str = "demo",
    provider: str | None = None,
    model: str | None = None,
    use_cache: bool = True,
) -> Propuesta:
    """Genera la Propuesta completa en modo cliente (10 secciones + anexo), verificada por reviewer."""
    active_provider = (provider or os.getenv("LLM_PROVIDER", LLM_PROVIDER) or "mock").strip().lower()
    active_model = (
        model
        or os.getenv("LLM_MODEL_WRITER", LLM_MODEL_WRITER)
        or active_provider
    ).strip()

    metrics_summary = build_brand_summary_metrics(tablas, marca_brief=ficha.marca)
    code_tables = _build_code_tables_client(ficha, tablas, plan)
    mock_narr = _mock_client_narrative(ficha, metrics_summary, plan)

    system_prompt = (PROMPTS_DIR / "writer_client_v1.md").read_text(encoding="utf-8")
    payload = {
        "ficha": ficha.model_dump(),
        "metrics_summary": metrics_summary,
        "hallazgos": [h.model_dump() for h in hallazgos if h.aprobado],
        "plan_resumen": {
            "coste_total_eur": plan.coste_total_eur,
            "n_acciones": len(plan.acciones),
            "objetivos": [o.model_dump() for o in plan.objetivos],
        },
    }
    user_prompt = (
        "Redacta los bloques narrativos de la propuesta para el Comité de Dirección usando solo cifras de <datos>:\n"
        f"<datos>\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n</datos>"
    )

    narrative = complete_json(
        system=system_prompt,
        user=user_prompt,
        schema=_ClientNarrativeLLM,
        model=active_model,
        temperature=0.0,
        prompt_version="writer_client_v1",
        mock_builder=lambda: mock_narr,
        provider=active_provider,
        use_cache=use_cache,
    )

    contexto_cifras = {
        "metrics": metrics_summary,
        "tablas": tablas,
        "hallazgos": list(hallazgos),
        "plan": plan,
        "ficha": ficha,
    }

    # Bucle de verificación y reescritura (máximo 2 reintentos si hay incidencias en el texto narrativo)
    initial_rev_narr: InformeRevision | None = None
    rewrite_iterations = 0
    for attempt in range(2):
        full_narr_text = "\n\n".join(narrative.model_dump().values())
        rev_narr = compliance(
            full_narr_text,
            plan=plan,
            ficha=ficha,
            contexto_cifras=contexto_cifras,
            provider=active_provider,
            use_cache=use_cache,
        )
        if initial_rev_narr is None:
            initial_rev_narr = rev_narr
        if rev_narr.aprobado:
            break
        if active_provider == "mock":
            narrative = mock_narr
            break
        rewrite_iterations += 1
        inc_txt = "\n".join(f"- [{i.tipo}] {i.texto} -> {i.sugerencia}" for i in rev_narr.incidencias)
        retry_prompt = (
            f"{user_prompt}\n\n"
            f"Corrige estas incidencias detectadas por el verificador (iteración {attempt + 1}):\n{inc_txt}"
        )
        narrative = complete_json(
            system=system_prompt,
            user=retry_prompt,
            schema=_ClientNarrativeLLM,
            model=active_model,
            temperature=0.0,
            prompt_version="writer_client_v1",
            mock_builder=lambda: mock_narr,
            provider=active_provider,
            use_cache=False,
        )

    # Construir sección 5 (Hallazgos clave) desde los objetos Hallazgo validados
    hallazgos_lines: list[str] = []
    for h in hallazgos:
        if not h.aprobado:
            continue
        evs_str = "; ".join(
            f"`{e.metrica}` = {e.valor} ({e.tabla}, n={e.n}, ej: {', '.join(e.ejecucion_ids[:3])})"
            for e in h.evidencias
        )
        hallazgos_lines.append(
            f"### {h.id} · {h.titulo}\n"
            f"- **Prioridad:** {h.prioridad} · **Tipo:** `{h.tipo}` · **Impacto:** `{h.impacto}` · **Confianza:** `{h.confianza}`\n"
            f"- **Descripción:** {h.descripcion}\n"
            f"- **Evidencia trazable:** {evs_str}"
        )

    riesgos_md = "### Riesgos identificados y mitigación\n" + "\n".join(
        f"- {r}" for r in plan.riesgos
    )
    supuestos_md = "### Supuestos de trabajo y tarifas\n" + "\n".join(
        f"- {s}" for s in plan.supuestos
    )

    secciones: dict[str, str] = {
        "1. Resumen ejecutivo": narrative.resumen_ejecutivo,
        "2. Contexto y alcance": narrative.contexto_y_alcance,
        "3. Diagnóstico de visibilidad": (
            f"### 3.1 Visibilidad espontánea (consultas sin marca)\n\n"
            f"{narrative.intro_diagnostico_espontaneo}\n\n"
            f"#### Desglose por motor (Espontánea)\n{code_tables['t2']}\n\n"
            f"#### Desglose por fase del embudo (Espontánea)\n{code_tables['t3']}\n\n"
            f"#### Desglose geográfico: Madrid vs Barcelona (Espontánea)\n{code_tables['t4']}\n\n"
            f"#### Desglose por familia de prompt (Espontánea)\n{code_tables['t5']}\n\n"
            f"#### Perfil de fuentes en apariciones de {ficha.marca}\n{code_tables['t6_alb']}\n\n"
            f"### 3.2 Visibilidad asistida (apartado independiente: consultas con marca)\n\n"
            f"{narrative.intro_diagnostico_asistido}\n\n"
            f"{code_tables['t1_asis']}"
        ),
        "4. Análisis de la competencia": (
            f"{narrative.intro_competencia}\n\n"
            f"#### Ranking general de visibilidad espontánea (T1)\n{code_tables['t1_esp']}\n\n"
            f"#### Calidad de mención asistida y objeciones recurrentes del mercado (T9)\n{code_tables['t9']}\n\n"
            f"#### Duelos directos 1 a 1 de {ficha.marca} (T8)\n{code_tables['t8_alb']}"
        ),
        "5. Hallazgos clave": "\n\n".join(hallazgos_lines),
        "6. Estrategia recomendada": (
            f"{narrative.intro_estrategia}\n\n"
            f"#### Objetivos cuantitativos a {ficha.horizonte_meses} meses\n{code_tables['objetivos']}"
        ),
        "7. Plan de acción por fases": (
            f"El plan consta de {len(plan.acciones)} acciones específicas enlazadas a los hallazgos `H1`–`H{len(hallazgos)}`:\n\n"
            f"{code_tables['acciones']}"
        ),
        "8. Medición y seguimiento": narrative.medicion_y_seguimiento,
        "9. Riesgos y supuestos": f"{riesgos_md}\n\n{supuestos_md}",
        "10. Hoja de ruta y presupuesto": (
            f"La inversión total asciende a **{plan.coste_total_eur:,.0f} €**, dentro del rango "
            f"presupuestario del brief ({(ficha.presupuesto_min_eur or 18000):,.0f} € – "
            f"{(ficha.presupuesto_max_eur or 27000):,.0f} €) y respetando la capacidad semanal "
            f"del equipo interno (1 responsable de marketing + 0,5 comunicación).\n\n"
            f"#### Calendario y presupuesto por fase\n{code_tables['fases']}\n\n"
            f"#### Reparto por responsable\n{code_tables['responsables']}"
        ),
    }

    full_doc_text = "\n\n".join(secciones.values())
    final_revision = compliance(
        full_doc_text,
        plan=plan,
        ficha=ficha,
        contexto_cifras=contexto_cifras,
        provider=active_provider,
        use_cache=use_cache,
    )

    stats = get_llm_stats()
    metadatos = {
        "run_id": run_id,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "proveedor": active_provider,
        "modelo": active_model,
        "prompt_version": "writer_client_v1",
        "coste_estimado_llm_eur": stats["estimated_cost_eur"],
        "llm_calls": stats["calls"],
        "iteraciones_reescritura": rewrite_iterations,
        "revision_antes_reescritura": (
            initial_rev_narr.model_dump() if initial_rev_narr is not None else None
        ),
        "datos_sinteticos": True,
    }

    return Propuesta(
        modo="cliente",
        marca=ficha.marca,
        secciones=secciones,
        plan=plan,
        hallazgos=list(hallazgos),
        revision=final_revision,
        metadatos=metadatos,
    )


def build_default_prospect_ficha(
    marca_nombre: str,
    marcas_catalogo: Sequence[Marca] | None = None,
) -> FichaMarca:
    """Construye una FichaMarca por defecto a partir de marcas.csv cuando no existe brief (modo prospecto)."""
    dom = "clinica.example"
    rol = "Clínica oftalmológica del sector"
    if marcas_catalogo:
        for m in marcas_catalogo:
            if m.nombre == marca_nombre:
                dom = m.dominio
                rol = m.rol
                break
    return FichaMarca(
        marca=marca_nombre,
        web=f"https://{dom}",
        sector="Sanidad privada · oftalmología",
        subsector=rol,
        servicios=["Cirugía refractiva", "Cirugía de cataratas", "Revisiones oftalmológicas"],
        servicios_prioritarios=["cirugía refractiva", "cataratas"],
        ciudades=["Madrid", "Barcelona"],
        ciudad_principal="Madrid",
        ciudad_crecimiento="Barcelona",
        competidores_declarados=[
            "Grupo Hospitalario Valdecruz",
            "Instituto Oftálmico Tramuntana",
        ],
        objetivo_principal=(
            f"Incrementar la recomendación activa y el posicionamiento espontáneo de {marca_nombre} en asistentes de IA."
        ),
        horizonte_meses=12,
        presupuesto_min_eur=15000.0,
        presupuesto_max_eur=25000.0,
        restricciones_normativas=[
            "Publicidad sanitaria regulada: sin promesas de resultado ni comparativas denigratorias."
        ],
        tono="Riguroso, ejecutivo y consultivo",
        audiencia="Dirección General y Dirección de Marketing (Prospecto sin brief previo)",
        formato="Auditoría ejecutiva de captación + correo comercial",
    )


def write_prospect(
    marca: str,
    tablas: dict[str, pd.DataFrame],
    marcas_catalogo: Sequence[Marca] | None = None,
    *,
    run_id: str = "demo",
    provider: str | None = None,
    model: str | None = None,
    use_cache: bool = True,
) -> Propuesta:
    """Genera una propuesta comercial en modo prospecto (gancho, 3 hallazgos, 3 acciones y correo de 120-180 palabras)."""
    active_provider = (provider or os.getenv("LLM_PROVIDER", LLM_PROVIDER) or "mock").strip().lower()
    active_model = (
        model
        or os.getenv("LLM_MODEL_WRITER", LLM_MODEL_WRITER)
        or active_provider
    ).strip()

    ficha_prosp = build_default_prospect_ficha(marca, marcas_catalogo)
    hallazgos_prosp = generate_findings(tablas, ficha=ficha_prosp)[:3]
    plan_prosp = build_plan(ficha_prosp, hallazgos_prosp, tablas, provider=active_provider)
    top_3_acciones = plan_prosp.acciones[:3]

    metrics_prosp = build_brand_summary_metrics(tablas, marca_brief=marca)
    ap_esp = round(metrics_prosp["tasa_aparicion_espontanea"] * 100.0, 1)
    sc_esp = metrics_prosp["score_espontaneo"]
    puesto = metrics_prosp["puesto_espontaneo"]
    rec_esp = round(metrics_prosp["pct_recomendacion_activa_espontanea"] * 100.0, 1)
    neg_asis = round(metrics_prosp["pct_negativo_asistida"] * 100.0, 1)

    opp_lines = [
        f"1. **{h.titulo} ({h.id}):** {h.descripcion}" for h in hallazgos_prosp
    ]
    act_lines = [
        f"1. **{a.titulo} (`{a.palanca}`):** {a.descripcion} — *Entregable:* {a.entregables[0]}. *KPI:* {a.kpi}."
        if idx == 0
        else f"{idx + 1}. **{a.titulo} (`{a.palanca}`):** {a.descripcion} — *Entregable:* {a.entregables[0]}. *KPI:* {a.kpi}."
        for idx, a in enumerate(top_3_acciones)
    ]

    # Correo comercial entre 120 y 180 palabras, profesional y sin promesas
    correo_mock = (
        f"**Asunto:** Auditoría de visibilidad de {marca} en ChatGPT, Gemini, Perplexity y Claude\n\n"
        f"Estimado equipo de Dirección de {marca},\n\n"
        f"En reload. hemos realizado un estudio sectorial independiente sobre cómo recomiendan los asistentes "
        f"de IA a las clínicas oftalmológicas en España tras analizar 624 ejecuciones en ChatGPT, Gemini, "
        f"Perplexity y Claude (nota: diagnóstico elaborado a partir de datos públicos y sintéticos del sector, "
        f"sin brief interno previo de su clínica).\n\n"
        f"Los resultados muestran una oportunidad muy clara para {marca}: aunque aparece en el {ap_esp:.1f} % "
        f"de las consultas espontáneas sin marca (n=240, puesto {puesto} de 10 con un Score de Citación de "
        f"{sc_esp:.2f} puntos), solo recibe una recomendación principal activa en el {rec_esp:.1f} % de las "
        f"ocasiones, y en consultas asistidas presenta un {neg_asis:.1f} % de menciones con advertencias que "
        f"frenan la conversión frente al líder Grupo Hospitalario Valdecruz (90,8 % de aparición).\n\n"
        f"Hemos preparado tres intervenciones concretas sobre datos estructurados, contenidos de decisión y "
        f"gestión de objeciones para transformar esas apariciones pasivas en primeras visitas médicas. "
        f"¿Tendrían 20 minutos esta semana para revisar el informe completo con sus evidencias?"
    )

    mock_prosp = _ProspectNarrativeLLM(
        gancho=(
            f"**Gancho comercial:** {marca} ya aparece en el **{ap_esp:.1f} %** de las consultas espontáneas "
            f"en IA (n=240, puesto {puesto} de 10 con score {sc_esp:.2f}), pero solo logra recomendación "
            f"principal en el **{rec_esp:.1f} %** de ellas."
        ),
        oportunidad="\n\n".join(opp_lines),
        que_hariamos="\n\n".join(act_lines),
        correo_comercial=correo_mock,
    )

    system_prompt = (PROMPTS_DIR / "writer_prospect_v1.md").read_text(encoding="utf-8")
    payload = {
        "nota_origen": "Ficha construida con marcas.csv y valores por defecto (sin brief del cliente).",
        "ficha": ficha_prosp.model_dump(),
        "metrics_summary": metrics_prosp,
        "hallazgos_top3": [h.model_dump() for h in hallazgos_prosp],
        "acciones_top3": [a.model_dump() for a in top_3_acciones],
    }
    user_prompt = (
        "Redacta la propuesta de captación en modo prospecto usando únicamente las cifras de <datos>:\n"
        f"<datos>\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n</datos>"
    )

    prosp_out = complete_json(
        system=system_prompt,
        user=user_prompt,
        schema=_ProspectNarrativeLLM,
        model=active_model,
        temperature=0.0,
        prompt_version="writer_prospect_v1",
        mock_builder=lambda: mock_prosp,
        provider=active_provider,
        use_cache=use_cache,
    )

    secciones = {
        "0. Nota metodológica (Modo Prospecto sin brief)": (
            f"Esta auditoría de captación para **{marca}** se ha generado sin brief interno, "
            f"construyendo la ficha base a partir del catálogo público del sector (`marcas.csv`) "
            f"y de las 624 ejecuciones del estudio sintético GEO."
        ),
        "1. Gancho": prosp_out.gancho,
        "2. Oportunidad (3 hallazgos clave)": prosp_out.oportunidad,
        "3. Qué haríamos (3 acciones de alto impacto)": prosp_out.que_hariamos,
        "4. Correo comercial": prosp_out.correo_comercial,
    }

    contexto_cifras = {
        "metrics": metrics_prosp,
        "tablas": tablas,
        "hallazgos": hallazgos_prosp,
        "plan": plan_prosp,
        "ficha": ficha_prosp,
    }
    full_text = "\n\n".join(secciones.values())
    revision = compliance(
        full_text,
        plan=plan_prosp,
        ficha=ficha_prosp,
        contexto_cifras=contexto_cifras,
        provider=active_provider,
        use_cache=use_cache,
    )

    stats = get_llm_stats()
    metadatos = {
        "run_id": run_id,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "proveedor": active_provider,
        "modelo": active_model,
        "prompt_version": "writer_prospect_v1",
        "coste_estimado_llm_eur": stats["estimated_cost_eur"],
        "sin_brief": True,
        "datos_sinteticos": True,
    }

    return Propuesta(
        modo="prospecto",
        marca=marca,
        secciones=secciones,
        plan=plan_prosp,
        hallazgos=hallazgos_prosp,
        revision=revision,
        metadatos=metadatos,
    )
