"""Verificador de trazabilidad de cifras y guardia normativa sanitaria (F10)."""

import json
import math
import re
from typing import Any, Sequence
import pandas as pd
from pydantic import BaseModel

from geo.config import PROMPTS_DIR, SCORE_WEIGHTS, SOURCE_QUALITY_BY_TYPE
from geo.llm import complete_json
from geo.loader import load_fuentes, load_marcas, load_prompts
from geo.schemas import FichaMarca, Hallazgo, Incidencia, InformeRevision, Plan
from geo.text import normalize

_METHODOLOGY_CONSTANTS: tuple[float, ...] = (
    0.0,
    1.0,
    2.0,
    3.0,
    4.0,
    5.0,
    6.0,
    7.0,
    8.0,
    9.0,
    10.0,
    12.0,
    14.0,
    15.0,
    18.0,
    20.0,
    24.0,
    25.0,
    30.0,
    36.0,
    48.0,
    50.0,
    52.0,
    53.0,
    60.0,
    66.0,
    67.0,
    70.0,
    90.0,
    100.0,
    104.0,
    120.0,
    133.0,
    156.0,
    180.0,
    200.0,
    240.0,
    384.0,
    624.0,
    1198.0,
    1500.0,
    1800.0,
    2009.0,
    2024.0,
    2025.0,
    2026.0,
    2250.0,
    2928.0,
    3200.0,
    6500.0,
    7500.0,
    18000.0,
    27000.0,
    90000.0,
    4.7,
    1.5,
    0.468,
    0.527,
    0.715,
    0.035,
    0.185,
)

_COMPETITOR_NAMES: tuple[str, ...] = (
    "Instituto Oftálmico Tramuntana",
    "Tramuntana",
    "Láser Nítida",
    "Nítida",
    "Vistalia Oftalmología",
    "Vistalia",
    "Grupo Hospitalario Valdecruz",
    "Valdecruz",
    "Oftalmos Centro",
    "Oftalmos",
    "Clínica del Ojo Cervantes",
    "Cervantes",
    "Visionar Clínicas",
    "Visionar",
    "Instituto Ocular Santa Eulalia",
    "Santa Eulalia",
    "Centro Lasik Península",
    "Lasik Península",
)

_PROMISE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bgarantiza(?:mos|n|do|da|r)?\b", flags=re.IGNORECASE),
        "Sustituir garantías absolutas por rangos orientativos sujetos a valoración médica o re-medición.",
    ),
    (
        re.compile(r"\bresultados?\s+asegurados?\b", flags=re.IGNORECASE),
        "Eliminar 'resultados asegurados'; en sanidad y GEO no se pueden prometer resultados.",
    ),
    (
        re.compile(r"\b100\s*%\s*(?:de\s+)?(?:éxito|exito|eficacia|seguro|efectivo)\b", flags=re.IGNORECASE),
        "Retirar afirmaciones del '100 % de éxito/eficacia'; usar datos clínicos verificables.",
    ),
    (
        re.compile(r"\b(?:el\s+mejor\s+centro|la\s+mejor\s+cl[ií]nica)\b", flags=re.IGNORECASE),
        "Evitar superlativos absolutos ('la mejor clínica'); describir hechos y diferenciales verificables.",
    ),
    (
        re.compile(r"\bsin\s+riesgos?\b", flags=re.IGNORECASE),
        "Retirar 'sin riesgo'; toda intervención médica conlleva consideraciones clínicas que evalúa el especialista.",
    ),
]


class _ComplianceLLMOutput(BaseModel):
    """Salida estructurada del revisor normativo LLM."""

    incidencias: list[Incidencia] = []


def _add_number_variants(allowed: set[float], val: float) -> None:
    """Añade al conjunto permitido un valor numérico, sus redondeos a 1 y 2 decimales (y entero si está a <=0.28) y conversión 0..1 <-> %."""
    if math.isnan(val) or math.isinf(val):
        return
    for candidate in (val, val * 100.0 if 0.0 <= abs(val) <= 1.0 else val):
        allowed.add(round(candidate, 4))
        allowed.add(round(candidate, 2))
        allowed.add(round(candidate, 1))
        if abs(candidate - round(candidate, 0)) <= 0.28:
            allowed.add(round(candidate, 0))


def _extract_numbers_from_any(obj: Any, allowed: set[float]) -> None:
    """Recorre recursivamente diccionarios, listas, DataFrames o modelos Pydantic extrayendo cifras permitidas."""
    if obj is None:
        return
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        _add_number_variants(allowed, float(obj))
        return
    if isinstance(obj, str):
        for raw_m in re.findall(r"\d{1,3}(?:\.\d{3})+|\d+(?:[.,]\d+)?", obj):
            cleaned = (
                raw_m.replace(".", "")
                if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw_m)
                else raw_m.replace(",", ".")
            )
            try:
                _add_number_variants(allowed, float(cleaned))
            except ValueError:
                pass
        return
    if isinstance(obj, BaseModel):
        _extract_numbers_from_any(obj.model_dump(), allowed)
        return
    if isinstance(obj, pd.DataFrame):
        for col in obj.columns:
            if col == "evidencia_ids":
                continue
            for v in obj[col].dropna().tolist():
                _extract_numbers_from_any(v, allowed)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k != "evidencia_ids":
                _extract_numbers_from_any(v, allowed)
        return
    if isinstance(obj, (list, tuple, set)):
        for item in obj:
            _extract_numbers_from_any(item, allowed)


def build_allowed_numbers(contexto_cifras: Any) -> set[float]:
    """Construye el conjunto de números permitidos (incluyendo redondeos y % <-> decimal) desde el contexto dado."""
    allowed: set[float] = set()
    for c in _METHODOLOGY_CONSTANTS:
        _add_number_variants(allowed, c)
    for w in SCORE_WEIGHTS.values():
        _add_number_variants(allowed, float(w))
    for q in SOURCE_QUALITY_BY_TYPE.values():
        _add_number_variants(allowed, float(q))

    _extract_numbers_from_any(contexto_cifras, allowed)
    return allowed


def _parse_spanish_number(raw_num: str) -> float | None:
    """Convierte una cadena numérica en español ('90.000', '38,8', '27.97') a float."""
    s = raw_num.strip()
    if not s:
        return None
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def verify_numbers(
    texto: str,
    contexto_cifras: Any,
) -> tuple[list[Incidencia], int, int]:
    """Verifica que todas las cifras cuantitativas del texto sean trazables al contexto de datos.

    Devuelve `(incidencias_cifras, cifras_verificadas, cifras_no_trazables)`.
    """
    if not texto:
        return ([], 0, 0)

    allowed = build_allowed_numbers(contexto_cifras)

    # Limpiar identificadores técnicos (EJ-0449, H1..H9, A1..A25, T1..T12, S12, SHA-256, fechas de modelo -20251001) y numeración de listas
    cleaned = texto.replace("{,}", ",")
    cleaned = re.sub(r"\b(?:EJ-\d+|H\d+|A\d+|T\d+|S\d+|P\d+|F\d+|SHA-\d+)\b", " ", cleaned)
    cleaned = re.sub(r"-\d{8}\b", " ", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", " ", cleaned)

    pattern = re.compile(
        r"(?<![A-Za-z0-9_])(\d{1,3}(?:\.\d{3})+|\d+(?:[.,]\d+)?)\s*(%|pp|€|puntos)?(?![A-Za-z0-9_])"
    )

    incidencias: list[Incidencia] = []
    verificadas = 0
    no_trazables = 0

    for m in pattern.finditer(cleaned):
        raw_num = m.group(1)
        unit = (m.group(2) or "").strip()
        val = _parse_spanish_number(raw_num)
        if val is None:
            continue

        # Ignorar años del calendario (2000..2035) y semanas/fases pequeñas sin unidad porcentual/monetaria
        if not unit and 2000 <= val <= 2035:
            verificadas += 1
            continue

        is_valid = any(
            math.isclose(val, a, abs_tol=0.12)
            for a in allowed
        )
        if is_valid:
            verificadas += 1
        else:
            no_trazables += 1
            snippet_start = max(0, m.start() - 35)
            snippet_end = min(len(cleaned), m.end() + 35)
            snippet = cleaned[snippet_start:snippet_end].strip()
            incidencias.append(
                Incidencia(
                    tipo="cifra_no_trazable",
                    texto=f"{raw_num}{(' ' + unit) if unit else ''} en «...{snippet}...»",
                    sugerencia="Sustituir o eliminar la cifra: solo pueden usarse números presentes en metrics.json, tablas, evidencias, plan o ficha.",
                    bloqueante=True,
                )
            )

    return (incidencias, verificadas, no_trazables)


ALLOWED_ENTITIES_TERMS: set[str] = {
    "España",
    "provincias",
    "LASIK",
    "PRK",
    "ICL",
    "SMILE",
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

_ALLOWED_CAMELCASE_TECH: set[str] = {
    *ALLOWED_ENTITIES_TERMS,
    "SearchBot",
    "GoogleOther",
    "WebSite",
    "Organization",
    "VideoObject",
    "JavaScript",
    "DataFrame",
    "DataFrames",
    "YouTube",
    "Trustpilot",
    "OpenAI",
    "PageSpeed",
    "LinkedIn",
    "GitHub",
    "Pydantic",
    "AppTest",
    "FichaMarca",
    "ContrasteMercado",
    "MarcaMercado",
    "InformeRevision",
    "TipoMencion",
    "TipoFuente",
    "FasePlan",
}

_UNCATALOGED_CITIES_NORM: set[str] = {
    "valencia",
    "sevilla",
    "bilbao",
    "zaragoza",
    "malaga",
    "murcia",
    "alicante",
    "vigo",
    "granada",
    "cordoba",
    "valladolid",
    "palma",
    "gijon",
    "pamplona",
    "santander",
    "salamanca",
    "toledo",
    "burgos",
    "oviedo",
    "tarragona",
    "girona",
    "lleida",
}

_UNCATALOGED_PROFILES_NORM: tuple[str, ...] = (
    "miedo quirurgico",
    "miedo al quirofano",
    "fobia quirurgica",
    "deportista de elite",
    "opositor",
    "conductor profesional",
)

_UNCATALOGED_BRAND_TOKENS_NORM: tuple[str, ...] = (
    "mirasierra",
    "ocularia",
    "oftalmoplus",
    "eurolaser",
    "baviera",
    "barraquer",
    "miranza",
    "fernandez-vega",
    "fernandez vega",
    "vissum",
    "novovision",
    "oftalvist",
    "quironsalud",
)

_GENERIC_CLINIC_STOPWORDS_NORM: set[str] = {
    "clinica",
    "clinicas",
    "instituto",
    "centro",
    "hospital",
    "grupo hospitalario",
    "clinica oftalmologica",
    "clinicas oftalmologicas",
    "centro oftalmologico",
    "centros oftalmologicos",
    "instituto oftalmologico",
    "hospital privado",
    "centro sanitario",
    "clinica privada",
}


def verify_entities(
    texto: str,
    ficha: FichaMarca | None = None,
) -> list[Incidencia]:
    """Verifica que el texto no contenga marcas, dominios, ciudades ni perfiles ausentes de marcas.csv, fuentes_catalogo.csv, banco_prompts.csv o FichaMarca."""
    if not texto:
        return []

    marcas = load_marcas()
    fuentes = load_fuentes()
    _ = load_prompts()

    allowed_brands_norm: set[str] = {normalize(t) for t in ALLOWED_ENTITIES_TERMS}
    allowed_brand_words_norm: set[str] = set()
    allowed_domains: set[str] = {"schema.org", "wikidata.org", "wikipedia.org", "google.com", "env.example"}

    for m in marcas:
        mn = normalize(m.nombre)
        allowed_brands_norm.add(mn)
        allowed_brand_words_norm.update(mn.split())
        for a in m.alias:
            an = normalize(a)
            allowed_brands_norm.add(an)
            allowed_brand_words_norm.update(an.split())
        if m.dominio:
            allowed_domains.add(m.dominio.lower().strip())

    for dom in fuentes:
        allowed_domains.add(dom.lower().strip())

    allowed_cities_norm: set[str] = {"madrid", "barcelona"}
    if ficha is not None:
        if ficha.marca:
            fmn = normalize(ficha.marca)
            allowed_brands_norm.add(fmn)
            allowed_brand_words_norm.update(fmn.split())
        for comp in ficha.competidores_declarados:
            cn = normalize(comp)
            allowed_brands_norm.add(cn)
            allowed_brand_words_norm.update(cn.split())
        for c in ficha.ciudades:
            if c:
                allowed_cities_norm.add(normalize(c))

    incidencias: list[Incidencia] = []
    seen_texts: set[str] = set()

    def _add_inc(label: str, sug: str) -> None:
        if label not in seen_texts:
            seen_texts.add(label)
            incidencias.append(
                Incidencia(
                    tipo="cifra_no_trazable",
                    texto=label,
                    sugerencia=sug,
                    bloqueante=True,
                )
            )

    # 1. Dominios web (.example, .com, .es, .org, .net, .io)
    dom_pat = re.compile(
        r"\b([a-zA-Z0-9][a-zA-Z0-9\-]*(?:\.[a-zA-Z0-9\-]+)*\.(?:example|es|com|org|net|io))\b"
    )
    for m in dom_pat.finditer(texto):
        dom_cand = m.group(1).lower()
        if dom_cand.startswith("www."):
            dom_cand = dom_cand[4:]
        if dom_cand not in allowed_domains:
            _add_inc(
                f"Dominio no catalogado: '{m.group(1)}'",
                "Usar únicamente dominios presentes en marcas.csv o fuentes_catalogo.csv.",
            )

    texto_norm = normalize(texto)

    # 2. Marcas / tokens de clínicas no catalogadas explícitas (p. ej. Mirasierra, Ocularia, OftalmoPlus, EuroLaser)
    for bad_brand in _UNCATALOGED_BRAND_TOKENS_NORM:
        if bad_brand not in allowed_brands_norm and re.search(rf"\b{re.escape(bad_brand)}\b", texto_norm):
            _add_inc(
                f"Marca no catalogada: '{bad_brand}'",
                "Usar únicamente las 10 marcas y alias definidos en marcas.csv.",
            )

    # 3. Patrones nominales de clínicas/institutos/centros con mayúscula no presentes en marcas.csv
    clinic_pat = re.compile(
        r"\b((?:Cl[ií]nicas?|Instituto|Centro|Grupo\s+Hospitalario|Hospital)\s+"
        r"(?:Oftalmol[oó]gic[oa]s?\s+|Oft[aá]lmic[oa]s?\s+|Ocular(?:es)?\s+|del\s+Ojo\s+|de\s+Oftalmolog[ií]a\s+)?"
        r"[A-ZÁÉÍÓÚÑ][A-Za-záéíóúñÁÉÍÓÚÑ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-záéíóúñÁÉÍÓÚÑ]+)*)"
    )
    for m in clinic_pat.finditer(texto):
        phrase = m.group(1).strip()
        p_norm = normalize(phrase)
        if p_norm in _GENERIC_CLINIC_STOPWORDS_NORM:
            continue
        is_known = (
            p_norm in allowed_brands_norm
            or any(ab in p_norm or p_norm in ab for ab in allowed_brands_norm if len(ab) >= 5)
        )
        if not is_known:
            _add_inc(
                f"Entidad clínica no catalogada: '{phrase}'",
                "Sustituir por una de las 10 marcas oficiales de marcas.csv.",
            )

    # 4. Tokens CamelCase de marcas inventadas (p. ej. OftalmoPlus, EuroLaser)
    camel_pat = re.compile(r"\b([A-Z][a-z]+[A-Z][A-Za-z0-9]*)\b")
    for m in camel_pat.finditer(texto):
        tok = m.group(1)
        if tok not in _ALLOWED_CAMELCASE_TECH and normalize(tok) not in allowed_brands_norm:
            _add_inc(
                f"Marca CamelCase no catalogada: '{tok}'",
                "Eliminar marca inventada fuera de marcas.csv.",
            )

    # 5. Ciudades fuera de banco_prompts.csv / FichaMarca
    for city_norm in _UNCATALOGED_CITIES_NORM:
        if city_norm not in allowed_cities_norm and re.search(rf"\b{re.escape(city_norm)}\b", texto_norm):
            _add_inc(
                f"Ciudad no catalogada en el estudio: '{city_norm}'",
                "Ceñirse a las ciudades presentes en banco_prompts.csv y FichaMarca (Madrid y Barcelona).",
            )

    # 6. Perfiles de paciente fuera de banco_prompts.csv / FichaMarca
    for prof_norm in _UNCATALOGED_PROFILES_NORM:
        if re.search(rf"\b{re.escape(prof_norm)}\b", texto_norm):
            _add_inc(
                f"Perfil de paciente no catalogado: '{prof_norm}'",
                "Usar únicamente los perfiles de banco_prompts.csv (45 años miopía, 70 años cataratas, piloto de aviación, 12 años miopía infantil).",
            )

    return incidencias


def _check_regex_compliance(
    texto: str,
    plan: Plan | None = None,
    ficha: FichaMarca | None = None,
) -> list[Incidencia]:
    """Capa 1 determinista: regex de promesas sanitarias, comparativas denigratorias y completitud del plan."""
    incidencias: list[Incidencia] = []

    if texto:
        # 1. Promesas de resultado o superlativos absolutos
        for pat, sug in _PROMISE_PATTERNS:
            for m in pat.finditer(texto):
                s_start = max(0, m.start() - 30)
                s_end = min(len(texto), m.end() + 30)
                incidencias.append(
                    Incidencia(
                        tipo="promesa_resultado",
                        texto=texto[s_start:s_end].strip(),
                        sugerencia=sug,
                        bloqueante=True,
                    )
                )

        # 2. Comparativas denigratorias hacia competidores en el texto
        comp_union = "|".join(re.escape(normalize(c)) for c in _COMPETITOR_NAMES)
        denig_patterns = [
            re.compile(
                rf"\b(?:mejor\s+que|peor\s+que|superior\s+a|a\s+diferencia\s+de|frente\s+a\s+las?\s+deficiencias\s+de)\s+(?:la\s+|el\s+)?({comp_union})\b",
                flags=re.IGNORECASE,
            ),
            re.compile(
                rf"\b({comp_union})\b[^.\n]{{0,50}}\b(?:deficiente|peor|mal\s+trato|abandono|baja\s+calidad|enga[nñ]o)\b",
                flags=re.IGNORECASE,
            ),
        ]
        texto_norm = normalize(texto)
        for dpat in denig_patterns:
            for m in dpat.finditer(texto_norm):
                s_start = max(0, m.start() - 25)
                s_end = min(len(texto_norm), m.end() + 25)
                incidencias.append(
                    Incidencia(
                        tipo="comparativa_denigratoria",
                        texto=texto_norm[s_start:s_end].strip(),
                        sugerencia="Eliminar la comparativa directa o denigratoria hacia el competidor; destacar el diferencial propio en positivo.",
                        bloqueante=True,
                    )
                )

    # 3. Revisión del Plan (acciones sin hallazgo, campos vacíos, presupuesto y mención de competidores en acciones de contenido)
    if plan is not None:
        max_b = (ficha.presupuesto_max_eur if ficha and ficha.presupuesto_max_eur else 27000.0)
        if plan.coste_total_eur > max_b:
            incidencias.append(
                Incidencia(
                    tipo="presupuesto",
                    texto=f"Coste total del plan ({plan.coste_total_eur:,.2f} €) supera el máximo ({max_b:,.2f} €).",
                    sugerencia="Recortar acciones de menor ratio impacto/esfuerzo con geo.budget.validate_and_adjust_plan.",
                    bloqueante=True,
                )
            )

        for acc in plan.acciones:
            if not acc.hallazgos_relacionados:
                incidencias.append(
                    Incidencia(
                        tipo="accion_sin_hallazgo",
                        texto=f"Acción {acc.id} ({acc.titulo}) no tiene hallazgos_relacionados.",
                        sugerencia="Vincular la acción a al menos un hallazgo aprobado (H1..H7) o eliminarla.",
                        bloqueante=True,
                    )
                )
            if (
                not acc.titulo.strip()
                or not acc.descripcion.strip()
                or not acc.kpi.strip()
                or not acc.entregables
            ):
                incidencias.append(
                    Incidencia(
                        tipo="campo_vacio",
                        texto=f"Acción {acc.id} tiene algún campo obligatorio vacío (título, descripción, KPI o entregables).",
                        sugerencia="Completar todos los campos obligatorios de la acción.",
                        bloqueante=True,
                    )
                )

            if acc.palanca == "contenido":
                acc_text_norm = normalize(f"{acc.titulo} {acc.descripcion}")
                for comp in _COMPETITOR_NAMES:
                    c_norm = normalize(comp)
                    if re.search(rf"\b{re.escape(c_norm)}\b", acc_text_norm):
                        incidencias.append(
                            Incidencia(
                                tipo="comparativa_denigratoria",
                                texto=f"Acción de contenido {acc.id} menciona al competidor '{comp}'.",
                                sugerencia="En acciones de contenido propio no nombrar ni comparar con competidores.",
                                bloqueante=True,
                            )
                        )
                        break

    return incidencias


def compliance(
    texto: str,
    plan: Plan | None = None,
    ficha: FichaMarca | None = None,
    *,
    contexto_cifras: Any = None,
    provider: str | None = None,
    model: str | None = None,
    use_cache: bool = True,
) -> InformeRevision:
    """Ejecuta el verificador de cifras (si se pasa `contexto_cifras`) y la guardia normativa (Capa 1 regex + Capa 2 LLM)."""
    incidencias: list[Incidencia] = []
    verificadas = 0
    no_trazables = 0

    if contexto_cifras is not None:
        inc_num, verificadas, no_trazables = verify_numbers(texto, contexto_cifras)
        incidencias.extend(inc_num)

    inc_entities = verify_entities(texto, ficha=ficha)
    incidencias.extend(inc_entities)

    inc_regex = _check_regex_compliance(texto, plan=plan, ficha=ficha)
    incidencias.extend(inc_regex)

    # Capa 2: LLM compliance_v1.md
    system_prompt = (PROMPTS_DIR / "compliance_v1.md").read_text(encoding="utf-8")
    payload = {
        "texto": texto,
        "restricciones_normativas": ficha.restricciones_normativas if ficha else [],
        "tono": ficha.tono if ficha else "Riguroso, cercano y sin sensacionalismo",
    }
    user_prompt = (
        "Revisa el siguiente texto y devuelve las incidencias normativas adicionales en JSON:\n"
        f"<datos>\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n</datos>"
    )

    try:
        llm_out = complete_json(
            system=system_prompt,
            user=user_prompt,
            schema=_ComplianceLLMOutput,
            model=model,
            temperature=0.0,
            prompt_version="compliance_v1",
            mock_builder=lambda: _ComplianceLLMOutput(incidencias=[]),
            provider=provider,
            use_cache=use_cache,
        )
        existing_texts = {inc.texto for inc in incidencias}
        for inc in llm_out.incidencias:
            if inc.texto not in existing_texts:
                incidencias.append(inc)
    except Exception:
        pass

    bloqueantes = any(inc.bloqueante for inc in incidencias)
    return InformeRevision(
        incidencias=incidencias,
        cifras_verificadas=verificadas,
        cifras_no_trazables=no_trazables,
        aprobado=not bloqueantes and no_trazables == 0,
    )
