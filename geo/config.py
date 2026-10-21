"""Configuración global, rutas, constantes de la metodología y settings de entorno."""

import csv
import os
from pathlib import Path
from dotenv import load_dotenv

from geo.schemas import Intencion, Motor, TipoFuente

load_dotenv()

# ---------- Rutas ----------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
KIT_DIR: Path = ROOT_DIR / "kit" / "Kit Participantes Hackaton"
REFERENCE_DATA_DIR: Path = Path(__file__).resolve().parent / "reference_data"
DATA_DIR: Path = REFERENCE_DATA_DIR  # solo datos del kit (modo de referencia)
BRIEF_DIR: Path = REFERENCE_DATA_DIR
BRIEF_MD: Path = BRIEF_DIR / "Brief_de_ejemplo_Clinica_Alborada.md"
BRIEF_DOCX: Path = BRIEF_DIR / "Brief_de_ejemplo_Clinica_Alborada.docx"
DOCS_DIR: Path = KIT_DIR / "03_Documentacion"
PROMPTS_DIR: Path = Path(__file__).resolve().parent / "prompts"
CACHE_DIR: Path = ROOT_DIR / "cache"
RUNS_DIR: Path = ROOT_DIR / "runs"

# Archivos CSV del kit
MARCAS_CSV: Path = DATA_DIR / "marcas.csv"
BANCO_PROMPTS_CSV: Path = DATA_DIR / "banco_prompts.csv"
EJECUCIONES_CSV: Path = DATA_DIR / "ejecuciones.csv"
FUENTES_CATALOGO_CSV: Path = DATA_DIR / "fuentes_catalogo.csv"
MUESTRA_EVALUADA_CSV: Path = DATA_DIR / "muestra_evaluada.csv"

# ---------- Constantes de la metodología ----------
MOTORES: list[Motor] = ["ChatGPT", "Gemini", "Perplexity", "Claude"]

# Orden del embudo de decisión
INTENCIONES: list[Intencion] = [
    "Descubrimiento",
    "Comparación",
    "Validación",
    "Decisión",
]

INSTANCIACIONES_ESPONTANEAS: set[str] = {"generico", "ciudad"}
INSTANCIACIONES_ASISTIDAS: set[str] = {"marca", "par"}

CIUDADES_CONOCIDAS: list[str] = [
    "Madrid",
    "Barcelona",
    "Valencia",
    "Sevilla",
    "Bilbao",
    "Zaragoza",
    "Málaga",
]

# Pesos máximos de los componentes del Score de Citación (0-100)
SCORE_WEIGHTS: dict[str, int] = {
    "aparicion": 30,
    "posicion": 20,
    "fuerza": 30,
    "fuente": 20,
}

# Pesos por posición: {1: 3, 2: 2, 3: 2, >=4: 1, ausente: 0}
POSITION_WEIGHTS: dict[int, int] = {
    0: 0,
    1: 3,
    2: 2,
    3: 2,
}
DEFAULT_POSITION_WEIGHT_GE_4: int = 1


def peso_por_posicion(posicion: int | None) -> int:
    """Devuelve el peso de posición según la metodología GEO (1->3, 2-3->2, >=4->1, None/0->0)."""
    if posicion is None or posicion <= 0:
        return 0
    return POSITION_WEIGHTS.get(posicion, DEFAULT_POSITION_WEIGHT_GE_4)


# Calidad por tipo de fuente (0.0 a 1.0)
SOURCE_QUALITY_BY_TYPE: dict[TipoFuente, float] = {
    "Ranking / institución": 1.0,
    "Medio": 0.9,
    "Web propia": 0.7,
    "Directorio / comparador": 0.6,
    "Plataforma de reseñas": 0.6,
    "Red social / foro": 0.4,
    "Sin fuente": 0.2,
}

# ---------- Léxico del juez por reglas (F3, texto normalizado sin tildes) ----------
FUERZA_3: list[str] = [
    "es la que mas recomendaria",
    "la opcion mas recomendable",
    "seria mi recomendacion principal",
    "si tuviera que inclinarme por una",
    "es la opcion mas recomendada",
    "mi recomendacion principal",
    "tambien la recomendaria con confianza",
    "me inclinaria por",
]

FUERZA_2: list[str] = [
    "alternativa muy bien valorada",
    "opcion solida y bien valorada",
    "tambien la recomendaria",
    "encaja bien",
]

NEGATIVO: list[str] = [
    "eso si,",
    "quejas",
    "advierten",
    "listas de espera",
    "coste notablemente superior",
    "pocas opiniones verificadas",
    "desiguales",
    "mas antiguas",
    "varia bastante",
    "echan en falta",
    "muy cargada",
]

DESCONOCIMIENTO: list[str] = [
    "no dispongo de informacion",
    "no tengo informacion",
    "no cuento con datos",
]

# Umbral de longitud mínima del fragmento (sin el nombre de la marca) para no ser Pasiva en pos 1-3
PASIVA_MAX_CHARS: int = 35

# ---------- Umbrales del motor de hallazgos (F6) ----------
FINDINGS_THRESHOLDS: dict[str, float] = {
    "r1_geo_diff_pp": 25.0,               # Diferencia >= 25 pp entre ciudades
    "r1_geo_growth_city_max": 0.15,       # O aparición < 15 % en ciudad de crecimiento
    "r2_weak_motor_ratio": 0.50,          # Aparición en un motor < 50 % de la media en los demás
    "r3_funnel_drop_pp": 20.0,            # Caída >= 20 pp respecto a fase anterior
    "r3_funnel_leader_gap_pp": 30.0,      # Brecha con el líder >= 30 pp en una fase
    "r5_authority_sources_gap_pp": 20.0,  # Brecha >= 20 pp en Ranking/institución + Medio vs líder
    "r5_sin_fuente_min": 0.15,            # O % Sin fuente >= 15 %
    "r7_undeclared_competitor_min": 0.30, # Competidor no declarado con >= 30 % aparición espontánea
    "r8_azar_min": 0.50,                  # % de series en zona de azar (1-2/3) > 50 %
    "r9_profile_low_max": 0.40,           # Aparición en familia DP < 40 %
    "r10_desconocimiento_min": 0.05,      # % de desconocimiento en asistida >= 5 %
}
MAX_FINDINGS: int = 7

# Capacidad semanal máxima del equipo del cliente dedicada al plan GEO (1 resp. marketing + 0.5 comunicación -> ~18 h/sem dedicables)
CLIENT_WEEKLY_HOURS_CAPACITY: float = 18.0


def get_catalog_domains_by_type(path: Path = FUENTES_CATALOGO_CSV) -> dict[str, list[str]]:
    """Lee fuentes_catalogo.csv y devuelve los dominios agrupados por Tipo_de_fuente."""
    by_type: dict[str, list[str]] = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                dom = str(row["Dominio"]).strip().lower()
                t_fuente = str(row["Tipo_de_fuente"]).strip()
                by_type.setdefault(t_fuente, []).append(dom)
    return by_type


def _fmt_domain_list(domains: list[str]) -> str:
    if not domains:
        return ""
    if len(domains) == 1:
        return domains[0]
    return ", ".join(domains[:-1]) + " y " + domains[-1]


_CATALOG_BY_TYPE: dict[str, list[str]] = get_catalog_domains_by_type()
_DOM_DIRECTORIOS: str = _fmt_domain_list(_CATALOG_BY_TYPE.get("Directorio / comparador", []))
_DOM_MEDIOS: str = _fmt_domain_list(_CATALOG_BY_TYPE.get("Medio", []))
_DOM_MEDIOS_COMMA: str = ", ".join(_CATALOG_BY_TYPE.get("Medio", []))
_DOM_RESENAS: str = _fmt_domain_list(_CATALOG_BY_TYPE.get("Plataforma de reseñas", []))
_RANKINGS_EXAMPLE: list[str] = [
    d for d in _CATALOG_BY_TYPE.get("Ranking / institución", []) if d.endswith(".example")
]
_DOM_RANKINGS: str = _fmt_domain_list(_RANKINGS_EXAMPLE or _CATALOG_BY_TYPE.get("Ranking / institución", []))
_DOM_RANKINGS_COMMA: str = ", ".join(_RANKINGS_EXAMPLE or _CATALOG_BY_TYPE.get("Ranking / institución", []))
_FOROS_EXAMPLE: list[str] = [
    d for d in _CATALOG_BY_TYPE.get("Red social / foro", []) if d.endswith(".example")
]
_DOM_FOROS: str = _fmt_domain_list(_FOROS_EXAMPLE or _CATALOG_BY_TYPE.get("Red social / foro", []))

# ---------- Catálogo de plantillas de acción (F9, ACTION_LIBRARY: 22 plantillas) ----------
ACTION_LIBRARY: list[dict[str, object]] = [
    {
        "template_id": "TPL-01",
        "titulo": "Datos estructurados schema.org (MedicalClinic, Physician, MedicalProcedure, FAQPage)",
        "descripcion": "Implementar marcado JSON-LD completo en las fichas de cirugía refractiva, cataratas, miopía infantil y sedes de {ciudades}, vinculando cuadro médico y acreditaciones.",
        "palanca": "entidad_datos_estructurados",
        "tipos_hallazgo": ["fuentes", "motor", "embudo"],
        "fase_embudo": ["Descubrimiento", "Validación"],
        "esfuerzo": "M",
        "impacto": "L",
        "responsable": "agencia",
        "coste_rango_eur": (1500.0, 2500.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 3,
        "fase_plan": 0,
        "dependencias_tpl": [],
        "kpi_tipo": "100 % de fichas prioritarias y sedes con schema.org validado sin errores",
        "entregables_tipo": [
            "Especificación JSON-LD por tipo de página (MedicalClinic, Physician, FAQPage)",
            "Validación en Rich Results Test y Schema Markup Validator",
        ],
    },
    {
        "template_id": "TPL-02",
        "titulo": "Auditoría técnica de rastreabilidad para bots de IA (robots.txt, sitemap, renderizado HTML)",
        "descripcion": "Configurar acceso explícito para GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot y Google-Extended, optimizando tiempos de respuesta y contenido sin dependencia de JS.",
        "palanca": "tecnico",
        "tipos_hallazgo": ["motor", "consistencia"],
        "fase_embudo": ["Descubrimiento"],
        "esfuerzo": "S",
        "impacto": "L",
        "responsable": "agencia",
        "coste_rango_eur": (500.0, 1000.0),
        "horas_cliente_semana": 1.5,
        "plazo_semanas": 2,
        "fase_plan": 0,
        "dependencias_tpl": [],
        "kpi_tipo": "Acceso 200 OK verificado para bots de OpenAI, Anthropic, Google y Perplexity",
        "entregables_tipo": [
            "Archivo robots.txt y sitemap.xml actualizados",
            "Informe técnico de renderizado SSR/HTML limpio en las 60 URLs",
        ],
    },
    {
        "template_id": "TPL-03",
        "titulo": f"Normalización de entidad y NAP en directorios sanitarios citados ({', '.join(_CATALOG_BY_TYPE.get('Directorio / comparador', []))})",
        "descripcion": f"Unificar nombre oficial, sedes ({{ciudades}}), especialidades, cuadro médico y horarios en {_DOM_DIRECTORIOS}.",
        "palanca": "entidad_datos_estructurados",
        "tipos_hallazgo": ["fuentes", "geografia", "brief_vs_datos"],
        "fase_embudo": ["Descubrimiento", "Comparación"],
        "esfuerzo": "S",
        "impacto": "M",
        "responsable": "cliente_marketing",
        "coste_rango_eur": (800.0, 1500.0),
        "horas_cliente_semana": 3.0,
        "plazo_semanas": 3,
        "fase_plan": 0,
        "dependencias_tpl": [],
        "kpi_tipo": "100 % de fichas de directorios sectoriales actualizadas y coherentes en Madrid y Barcelona",
        "entregables_tipo": [
            "Matriz maestra de atributos NAP y servicios por sede",
            f"Fichas verificadas en {_DOM_DIRECTORIOS}",
        ],
    },
    {
        "template_id": "TPL-04",
        "titulo": "Creación y enriquecimiento de entidad en Wikidata con referencias verificables",
        "descripcion": "Dar de alta y estructurar la entidad de {marca} en Wikidata con datos verificables (año de fundación 2009, sedes, especialidades, identificadores y referencias de prensa).",
        "palanca": "entidad_datos_estructurados",
        "tipos_hallazgo": ["motor", "fuentes"],
        "fase_embudo": ["Descubrimiento", "Validación"],
        "esfuerzo": "S",
        "impacto": "M",
        "responsable": "agencia",
        "coste_rango_eur": (300.0, 800.0),
        "horas_cliente_semana": 1.0,
        "plazo_semanas": 2,
        "fase_plan": 0,
        "dependencias_tpl": ["TPL-01"],
        "kpi_tipo": "Entidad activa en Wikidata con >= 10 propiedades y referencias externas",
        "entregables_tipo": [
            "Ficha de entidad publicada en Wikidata",
            "Enlace sameAs integrado en el marcado schema.org de la web",
        ],
    },
    {
        "template_id": "TPL-05",
        "titulo": "Páginas locales en Barcelona por tratamiento prioritario (refractiva, cataratas y miopía infantil)",
        "descripcion": "Crear landing pages específicas del centro de Barcelona (abierto en 2024) con equipo médico local, tecnología diagnóstica, tiempos de cita y preguntas frecuentes locales.",
        "palanca": "contenido",
        "tipos_hallazgo": ["geografia"],
        "fase_embudo": ["Descubrimiento", "Decisión"],
        "esfuerzo": "M",
        "impacto": "L",
        "responsable": "agencia",
        "coste_rango_eur": (2000.0, 3500.0),
        "horas_cliente_semana": 3.5,
        "plazo_semanas": 4,
        "fase_plan": 1,
        "dependencias_tpl": ["TPL-01"],
        "kpi_tipo": "Incremento de aparición espontánea en consultas de Barcelona hacia el rango 20 % - 35 %",
        "entregables_tipo": [
            "3 páginas locales de Barcelona (cirugía refractiva, control de miopía infantil, cataratas)",
            "Ficha local de sede Barcelona con perfiles de los oftalmólogos",
        ],
    },
    {
        "template_id": "TPL-06",
        "titulo": "Programa de activación y respuesta de reseñas verificadas en la sede de Barcelona",
        "descripcion": f"Sistematizar la solicitud de reseñas post-revisión en el centro de Barcelona en {_DOM_RESENAS}, respondiendo con detalle informativo.",
        "palanca": "reputacion_resenas",
        "tipos_hallazgo": ["geografia", "reputacion"],
        "fase_embudo": ["Validación", "Decisión"],
        "esfuerzo": "S",
        "impacto": "L",
        "responsable": "cliente_comunicacion",
        "coste_rango_eur": (600.0, 1200.0),
        "horas_cliente_semana": 2.5,
        "plazo_semanas": 5,
        "fase_plan": 1,
        "dependencias_tpl": ["TPL-03"],
        "kpi_tipo": ">= 100 nuevas reseñas verificadas en la sede de Barcelona con tasa de respuesta del 100 %",
        "entregables_tipo": [
            "Protocolo de captación de reseñas en clínica de Barcelona",
            "Guía de respuesta sanitaria conforme a normativa",
        ],
    },
    {
        "template_id": "TPL-07",
        "titulo": "Hub de FAQ citables construidas desde el banco de prompts reales (DG, DP, CO, PR)",
        "descripcion": "Redactar bloques de respuesta directa (40-80 palabras + tabla de criterios) para las dudas recurrentes que lanzan los usuarios a ChatGPT, Claude, Gemini y Perplexity.",
        "palanca": "contenido",
        "tipos_hallazgo": ["embudo", "perfil", "motor"],
        "fase_embudo": ["Descubrimiento", "Comparación", "Decisión"],
        "esfuerzo": "M",
        "impacto": "L",
        "responsable": "agencia",
        "coste_rango_eur": (1500.0, 2500.0),
        "horas_cliente_semana": 3.0,
        "plazo_semanas": 4,
        "fase_plan": 1,
        "dependencias_tpl": ["TPL-01"],
        "kpi_tipo": "Publicación de 25 bloques Q&A estructurados con datos verificables de la clínica",
        "entregables_tipo": [
            "25 módulos FAQ optimizados para citación generativa y validados por dirección médica",
            "Marcado FAQPage integrado en las páginas de servicio",
        ],
    },
    {
        "template_id": "TPL-08",
        "titulo": "Página transparente de precios orientativos, qué incluye el tratamiento y financiación",
        "descripcion": "Publicar desglose claro de rangos de inversión por técnica (LASIK, PRK, lentes fáquicas, cataratas), detallando que incluye valoración de 1 visita y 12 meses de seguimiento.",
        "palanca": "contenido",
        "tipos_hallazgo": ["embudo", "competencia"],
        "fase_embudo": ["Comparación", "Decisión"],
        "esfuerzo": "S",
        "impacto": "L",
        "responsable": "cliente_marketing",
        "coste_rango_eur": (800.0, 1200.0),
        "horas_cliente_semana": 3.0,
        "plazo_semanas": 3,
        "fase_plan": 1,
        "dependencias_tpl": [],
        "kpi_tipo": "Aumento de aparición espontánea en fase de Decisión desde el 25 % hacia el 38 % - 48 %",
        "entregables_tipo": [
            "Página pública de tarifas orientativas, alcance clínico y opciones de financiación",
            "Tabla comparativa de qué incluye el protocolo asistencial de {marca}",
        ],
    },
    {
        "template_id": "TPL-09",
        "titulo": "Contenido de puesta en valor del seguimiento postoperatorio de 12 meses (diferencial propio)",
        "descripcion": "Explicar con rigor médico el protocolo de revisiones durante 12 meses con el mismo oftalmólogo, respondiendo a la principal inquietud del paciente sin nombrar ni comparar con terceros.",
        "palanca": "contenido",
        "tipos_hallazgo": ["reputacion", "embudo"],
        "fase_embudo": ["Validación", "Decisión"],
        "esfuerzo": "S",
        "impacto": "L",
        "responsable": "cliente_medico",
        "coste_rango_eur": (1000.0, 1500.0),
        "horas_cliente_semana": 2.5,
        "plazo_semanas": 3,
        "fase_plan": 1,
        "dependencias_tpl": [],
        "kpi_tipo": "Incremento de menciones de recomendación activa basadas en seguimiento postoperatorio",
        "entregables_tipo": [
            "Guía clínica del protocolo de seguimiento postoperatorio de 12 meses firmada por el equipo médico",
            "Infografía de cronograma de revisiones (24 h, 1 semana, 1 mes, 3, 6 y 12 meses)",
        ],
    },
    {
        "template_id": "TPL-10",
        "titulo": "Guías específicas por perfil de paciente (miopía infantil para padres, mayores de 60, pilotos)",
        "descripcion": "Crear guías clínicas dedicadas a padres de niños con miopía progresiva, acompañantes de mayores con cataratas y opositores/pilotos con requisitos visuales.",
        "palanca": "contenido",
        "tipos_hallazgo": ["perfil", "embudo"],
        "fase_embudo": ["Descubrimiento", "Comparación"],
        "esfuerzo": "M",
        "impacto": "M",
        "responsable": "agencia",
        "coste_rango_eur": (2000.0, 3000.0),
        "horas_cliente_semana": 2.5,
        "plazo_semanas": 5,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-07"],
        "kpi_tipo": "Incremento de visibilidad espontánea en prompts de familia DP (Descubrimiento por perfil)",
        "entregables_tipo": [
            "Guía para familias sobre control de miopía infantil",
            "Guía sobre cirugía refractiva según edad y profesión (25-50 años, pilotos)",
            "Guía de cirugía de cataratas con lentes premium para pacientes y familiares",
        ],
    },
    {
        "template_id": "TPL-11",
        "titulo": f"Plan de PR digital en prensa de salud citada ({_DOM_MEDIOS_COMMA})",
        "descripcion": f"Publicar tribunas médicas y notas con datos clínicos propios (~7.500 intervenciones/año, 14 oftalmólogos y protocolo de 12 meses de seguimiento) en {_DOM_MEDIOS}.",
        "palanca": "autoridad_terceros",
        "tipos_hallazgo": ["fuentes", "competencia", "brief_vs_datos", "reputacion"],
        "fase_embudo": ["Descubrimiento", "Validación"],
        "esfuerzo": "L",
        "impacto": "L",
        "responsable": "agencia",
        "coste_rango_eur": (4000.0, 7000.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 12,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-05", "TPL-09"],
        "kpi_tipo": f">= 6 apariciones editoriales en {_DOM_MEDIOS}",
        "entregables_tipo": [
            "Informe anual de datos clínicos y tendencias en cirugía refractiva y miopía infantil",
            f"6 artículos/entrevistas con portavoces médicos publicados en {_DOM_MEDIOS}",
        ],
    },
    {
        "template_id": "TPL-12",
        "titulo": f"Dossier y candidatura a rankings y guías sectoriales ({_DOM_RANKINGS_COMMA})",
        "descripcion": f"Presentar memoria clínica y asistencial ante {_DOM_RANKINGS} para mejorar respaldo institucional.",
        "palanca": "autoridad_terceros",
        "tipos_hallazgo": ["fuentes", "competencia"],
        "fase_embudo": ["Descubrimiento", "Comparación", "Validación"],
        "esfuerzo": "M",
        "impacto": "L",
        "responsable": "cliente_comunicacion",
        "coste_rango_eur": (1000.0, 3000.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 8,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-03"],
        "kpi_tipo": "Presencia activa en >= 3 rankings/guías sectoriales de calidad 1.0",
        "entregables_tipo": [
            "Dossier institucional de indicadores médicos, equipamiento y sedes",
            f"Solicitudes de inclusión/actualización en {_DOM_RANKINGS}",
        ],
    },
    {
        "template_id": "TPL-13",
        "titulo": "Cápsulas de vídeo divulgativo del equipo médico en YouTube y comunidades de salud",
        "descripcion": "Producir vídeos breves de oftalmólogos de {marca} con transcripción estructurada respondiendo dudas sobre LASIK vs PRK, postoperatorio y miopía infantil.",
        "palanca": "comunidades",
        "tipos_hallazgo": ["fuentes", "reputacion"],
        "fase_embudo": ["Comparación", "Validación"],
        "esfuerzo": "M",
        "impacto": "M",
        "responsable": "cliente_comunicacion",
        "coste_rango_eur": (1500.0, 3000.0),
        "horas_cliente_semana": 2.5,
        "plazo_semanas": 8,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-09"],
        "kpi_tipo": "6 vídeos médicos publicados con transcripción completa embebida en fichas web",
        "entregables_tipo": [
            "6 cápsulas de vídeo divulgativo en YouTube con capítulos y transcripción",
            "Integración de VideoObject schema en las páginas de tratamiento",
        ],
    },
    {
        "template_id": "TPL-14",
        "titulo": "Guía comparativa objetiva de técnicas quirúrgicas (LASIK, PRK, ICL) con criterios médicos",
        "descripcion": "Publicar tablas clínicas comparativas de indicaciones, tiempos de recuperación y perfiles candidatos entre técnicas, ayudando a los motores en prompts de Comparación.",
        "palanca": "contenido",
        "tipos_hallazgo": ["embudo", "competencia"],
        "fase_embudo": ["Comparación"],
        "esfuerzo": "M",
        "impacto": "M",
        "responsable": "cliente_medico",
        "coste_rango_eur": (1200.0, 2000.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 4,
        "fase_plan": 1,
        "dependencias_tpl": ["TPL-01"],
        "kpi_tipo": "Mejora de tasa de aparición y posición media en prompts de Comparación",
        "entregables_tipo": [
            "Matriz comparativa LASIK vs PRK vs lentes fáquicas ICL avalada por comité médico",
            "Bloques HTML tabulares fácilmente extraíbles por buscadores de IA",
        ],
    },
    {
        "template_id": "TPL-15",
        "titulo": "Fichas individuales de los 14 oftalmólogos con colegiación, publicaciones y subespecialidad",
        "descripcion": "Reforzar criterios E-E-A-T sanitarios mediante perfiles detallados de cada especialista en Madrid y Barcelona, enlazados como revisores de las guías médicas.",
        "palanca": "entidad_datos_estructurados",
        "tipos_hallazgo": ["fuentes", "motor"],
        "fase_embudo": ["Validación", "Decisión"],
        "esfuerzo": "S",
        "impacto": "M",
        "responsable": "cliente_marketing",
        "coste_rango_eur": (900.0, 1500.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 3,
        "fase_plan": 0,
        "dependencias_tpl": [],
        "kpi_tipo": "14 perfiles médicos completos con marcado Physician y autoría clínica visible",
        "entregables_tipo": [
            "14 páginas de perfil médico con número de colegiado y experiencia",
            "Sello de revisión médica con fecha en las 60 URLs informativas",
        ],
    },
    {
        "template_id": "TPL-16",
        "titulo": "Optimización de conversión de citas y gestión de expectativas en franjas horarias",
        "descripcion": "Atender las menciones puntuales sobre disponibilidad de franjas de cita mediante agenda online visible y tiempos medios de espera transparentes por sede.",
        "palanca": "reputacion_resenas",
        "tipos_hallazgo": ["reputacion"],
        "fase_embudo": ["Validación", "Decisión"],
        "esfuerzo": "S",
        "impacto": "M",
        "responsable": "cliente_marketing",
        "coste_rango_eur": (500.0, 900.0),
        "horas_cliente_semana": 1.5,
        "plazo_semanas": 3,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-06"],
        "kpi_tipo": "Reducción de menciones negativas asistidas por debajo del 5 %",
        "entregables_tipo": [
            "Bloque informativo de tiempos medios de primera consulta en Madrid y Barcelona",
            "Protocolo de seguimiento de incidencias en reseñas sobre citas",
        ],
    },
    {
        "template_id": "TPL-17",
        "titulo": "Página de datos institucionales verificables (Memoria de actividad y calidad asistencial)",
        "descripcion": "Concentrar en una URL pública de referencia las cifras oficiales de {marca} (fundada en 2009, 14 oftalmólogos, ~7.500 intervenciones/año, 4,7/5 en 1.800 reseñas) para alimentar grounding web.",
        "palanca": "entidad_datos_estructurados",
        "tipos_hallazgo": ["brief_vs_datos", "consistencia", "motor"],
        "fase_embudo": ["Descubrimiento", "Validación"],
        "esfuerzo": "S",
        "impacto": "L",
        "responsable": "cliente_comunicacion",
        "coste_rango_eur": (700.0, 1200.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 2,
        "fase_plan": 0,
        "dependencias_tpl": [],
        "kpi_tipo": "Reducción de apariciones en zona de azar y mejora de consistencia 3/3 repeticiones",
        "entregables_tipo": [
            "Página 'Cifras y Calidad Asistencial' con datos estructurados y fuentes descargables",
            "Hoja de datos rápida (Fact Sheet) para periodistas y asistentes de IA",
        ],
    },
    {
        "template_id": "TPL-18",
        "titulo": "Participación informativa en foros y portales de pacientes oftalmológicos",
        "descripcion": f"Aportar contenido educativo verificado en {_DOM_FOROS} y comunidades de salud ocular sobre preparación preoperatoria y cuidados post-LASIK.",
        "palanca": "comunidades",
        "tipos_hallazgo": ["fuentes", "consistencia"],
        "fase_embudo": ["Descubrimiento", "Validación"],
        "esfuerzo": "M",
        "impacto": "S",
        "responsable": "agencia",
        "coste_rango_eur": (1000.0, 1800.0),
        "horas_cliente_semana": 1.5,
        "plazo_semanas": 6,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-07"],
        "kpi_tipo": "Presencia en hilos informativos citados por motores en la categoría de oftalmología",
        "entregables_tipo": [
            "Calendario de 12 colaboraciones divulgativas supervisadas por equipo médico",
            "Guía de participación ética sin promoción encubierta",
        ],
    },
    {
        "template_id": "TPL-19",
        "titulo": "Optimización semántica de las 60 URLs del blog hacia intenciones de Comparación y Decisión",
        "descripcion": "Reestructurar los artículos existentes del blog con resúmenes ejecutivos iniciales, tablas de decisión, enlaces a sedes de Madrid/Barcelona y autoría médica explícita.",
        "palanca": "contenido",
        "tipos_hallazgo": ["embudo", "consistencia", "motor"],
        "fase_embudo": ["Comparación", "Decisión"],
        "esfuerzo": "M",
        "impacto": "M",
        "responsable": "agencia",
        "coste_rango_eur": (1500.0, 2400.0),
        "horas_cliente_semana": 2.0,
        "plazo_semanas": 6,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-07"],
        "kpi_tipo": "30 artículos prioritarios actualizados con estructura citable y enlaces a conversión",
        "entregables_tipo": [
            "Auditoría y priorización de las 60 URLs actuales de la web",
            "30 artículos reestructurados con bloques TL;DR y validación clínica",
        ],
    },
    {
        "template_id": "TPL-20",
        "titulo": "Monitorización competitiva de actores multicentro no declarados (Vistalia, Oftalmos Centro)",
        "descripcion": "Incorporar en el cuadro de mando a Vistalia Oftalmología y Oftalmos Centro junto a Valdecruz, Tramuntana y Láser Nítida para vigilar cambios de cuota en Madrid y Barcelona.",
        "palanca": "medicion",
        "tipos_hallazgo": ["brief_vs_datos", "competencia"],
        "fase_embudo": ["Descubrimiento", "Comparación"],
        "esfuerzo": "S",
        "impacto": "M",
        "responsable": "agencia",
        "coste_rango_eur": (600.0, 1000.0),
        "horas_cliente_semana": 1.0,
        "plazo_semanas": 4,
        "fase_plan": 3,
        "dependencias_tpl": [],
        "kpi_tipo": "Seguimiento trimestral de las 10 marcas reales del mercado en los 4 motores",
        "entregables_tipo": [
            "Panel comparativo actualizado con competidores declarados y emergentes",
            "Alertas de cambios en fuentes citadas de la competencia",
        ],
    },
    {
        "template_id": "TPL-21",
        "titulo": "Alianzas de contenido con ópticas, colegios y asociaciones en Barcelona",
        "descripcion": "Generar menciones locales de autoridad en Barcelona mediante jornadas de cribado visual infantil y acuerdos con centros educativos y deportivos locales.",
        "palanca": "autoridad_terceros",
        "tipos_hallazgo": ["geografia", "perfil"],
        "fase_embudo": ["Descubrimiento"],
        "esfuerzo": "M",
        "impacto": "M",
        "responsable": "cliente_comunicacion",
        "coste_rango_eur": (1200.0, 2200.0),
        "horas_cliente_semana": 2.5,
        "plazo_semanas": 8,
        "fase_plan": 2,
        "dependencias_tpl": ["TPL-05"],
        "kpi_tipo": ">= 4 menciones en webs y medios locales de Barcelona vinculadas a salud visual",
        "entregables_tipo": [
            "Programa de divulgación local sobre miopía infantil en Barcelona",
            "Cobertura en portales locales y sanitarios catalanes",
        ],
    },
    {
        "template_id": "TPL-22",
        "titulo": "Re-medición trimestral del estudio GEO (4 oleadas: semanas 12, 24, 36 y 48) e informe a Comité",
        "descripcion": "Re-ejecutar el banco de 25 prompts en ChatGPT, Gemini, Perplexity y Claude cada trimestre para medir evolución del Score de Citación, con hito intermedio en el mes 6.",
        "palanca": "medicion",
        "tipos_hallazgo": ["geografia", "motor", "embudo", "competencia", "fuentes", "reputacion", "brief_vs_datos", "consistencia", "perfil"],
        "fase_embudo": ["Descubrimiento", "Comparación", "Validación", "Decisión"],
        "esfuerzo": "S",
        "impacto": "L",
        "responsable": "agencia",
        "coste_rango_eur": (3000.0, 6000.0),
        "horas_cliente_semana": 1.0,
        "plazo_semanas": 36,
        "fase_plan": 3,
        "dependencias_tpl": ["TPL-01", "TPL-05"],
        "kpi_tipo": "4 oleadas trimestrales ejecutadas (S12, S24, S36, S48) con atribución a primeras visitas",
        "entregables_tipo": [
            "4 informes trimestrales de evolución GEO para el Comité de Dirección",
            "Revisión de mitad de horizonte (mes 6) con recalibración de acciones",
        ],
    },
]

# ---------- Settings leídos de .env ----------
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
LLM_MODEL: str = os.getenv("LLM_MODEL", "").strip()
LLM_MODEL_WRITER: str = os.getenv("LLM_MODEL_WRITER", "").strip()
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
MAX_LLM_CALLS: int = int(os.getenv("MAX_LLM_CALLS", "1500").strip() or "1500")
MAX_BUDGET_EUR: float = float(os.getenv("MAX_BUDGET_EUR", "5.0").strip() or "5.0")
