"""Modelos Pydantic de la API (petición y respuesta).

Reflejan `contracts/openapi.yaml`, que es la fuente de verdad del contrato. Son independientes de
`geo/schemas.py`: el motor nunca importa de aquí y aquí nunca se importa del motor.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Error(BaseModel):
    error: ErrorBody


class OriginTag(BaseModel):
    origen: Literal['calculado', 'ia', 'automatico', 'editado']
    modelo: str | None = None


class Checkpoints(BaseModel):
    ficha: bool
    competencia: bool
    hallazgos: bool
    plan: bool


class Project(BaseModel):
    id: str
    nombre: str
    tipo: Literal['cliente', 'prospecto']
    marca: str | None = None
    sector: str | None = None
    origen_datos: Literal['csv', 'vivo'] | None = None
    revision: Literal['pausas', 'continuo']
    estado: Literal['borrador', 'listo_para_lanzar', 'en_ejecucion', 'esperando_revision', 'completado', 'error', 'interrumpido']
    punto_control_pendiente: int | None = None
    checkpoints: Checkpoints
    coste_eur: float
    creado: str
    actualizado: str
    archivado: bool


class ProjectCreate(BaseModel):
    nombre: str
    tipo: Literal['cliente', 'prospecto']


class ProjectPatch(BaseModel):
    nombre: str | None = None
    revision: Literal['pausas', 'continuo'] | None = None
    archivado: bool | None = None


class ProgressStep(BaseModel):
    id: str
    nombre: str
    estado: Literal['pendiente', 'en_curso', 'hecho', 'hecho_automatico', 'error', 'esperando_revision']
    duracion_s: float | None = None
    llamadas: int | None = None
    coste_eur: float | None = None
    error: str | None = None


class Progress(BaseModel):
    estado: Literal['en_ejecucion', 'esperando_revision', 'completado', 'error', 'interrumpido']
    paso_actual: str | None = None
    pasos: list[ProgressStep]
    contador: dict[str, Any] | None = None
    llamadas: int
    coste_eur: float
    coste_real: bool
    transcurrido_s: float


class EstimateStep(BaseModel):
    id: str
    nombre: str
    llamadas: int
    tokens_in: int | None = None
    tokens_out: int | None = None
    eur: float


class Estimate(BaseModel):
    pasos: list[EstimateStep]
    total_llamadas: int
    total_eur: float
    minutos: float
    supera_tope: bool
    tope_eur: float


class ConfirmaCoste(BaseModel):
    confirmo_coste: bool | None = None


class BriefText(BaseModel):
    texto: str


class ProspectData(BaseModel):
    marca: str
    dominio: str
    sector: str
    ciudad: str
    competidores: list[str] | None = None


class FichaMarca(BaseModel):
    marca: str
    web: str | None = None
    sector: str
    subsector: str | None = None
    servicios: list[str] | None = None
    servicios_prioritarios: list[str] | None = None
    diferenciales: list[str] | None = None
    publicos: list[str] | None = None
    ciudades: list[str] | None = None
    ciudad_principal: str | None = None
    ciudad_crecimiento: str | None = None
    competidores_declarados: list[str] | None = None
    situacion_digital: dict[str, Any] | None = None
    hipotesis_cliente: list[str] | None = None
    objetivo_principal: str
    kpis_negocio: list[str] | None = None
    horizonte_meses: int | None = None
    presupuesto_min_eur: float | None = None
    presupuesto_max_eur: float | None = None
    equipo: str | None = None
    restricciones_normativas: list[str] | None = None
    tono: str | None = None
    audiencia: str | None = None
    formato: str | None = None


class FichaPreview(BaseModel):
    ficha: FichaMarca
    faltantes: list[str]
    origen_campos: dict[str, Any] | None = None


class FichaResponse(BaseModel):
    ficha: FichaMarca
    faltantes: list[str]
    origen_campos: dict[str, Any] | None = None
    brief_texto: str | None = None
    aprobada: bool


class ValidationFile(BaseModel):
    archivo: str
    tipo: Literal['ejecuciones', 'marcas', 'banco_prompts', 'fuentes_catalogo', 'muestra_evaluada'] | None = None
    filas: int
    columnas_reconocidas: list[str] | None = None
    errores: list[str]
    avisos: list[str]
    filas_con_error: list[dict[str, Any]] | None = None


class StudySummary(BaseModel):
    ejecuciones: int
    motores: list[str]
    repeticiones: int
    prompts: int
    marcas: int
    espontaneas: int
    asistidas: int
    ciudades: list[str] | None = None


class UploadResult(BaseModel):
    informes: list[ValidationFile]
    resumen: StudySummary | None = None
    bloqueado: bool


class MarcaEstudio(BaseModel):
    nombre: str
    nivel: Literal['foco', 'contexto']
    rol: str
    dominio: str
    alias: list[str]
    motivo: str | None = None
    fuente_url: str | None = None


class BrandsPayload(BaseModel):
    marcas: list[MarcaEstudio]


class PlantillaPrompt(BaseModel):
    prompt_id: str
    familia: str
    intencion: Literal['Descubrimiento', 'Comparación', 'Validación', 'Decisión']
    prioridad: Literal['P1', 'P2']
    uso: str | None = None
    instanciacion: Literal['generico', 'ciudad', 'marca', 'par']
    plantilla: str


class PromptsPayload(BaseModel):
    prompts: list[PlantillaPrompt]


class PromptInstance(BaseModel):
    prompt_id: str
    prompt: str
    instanciacion: str | None = None
    marcas_a_evaluar: list[str] | None = None
    ciudad: str | None = None


class StudyConfig(BaseModel):
    tamano: Literal['rapido', 'estandar', 'completo']
    motores: list[Literal['ChatGPT', 'Gemini', 'Perplexity', 'Claude']]
    repeticiones: int


class CheckpointApprove(BaseModel):
    nota: str | None = None


class RetryStep(BaseModel):
    paso: str
    confirmo_coste: bool | None = None


class Recompute(BaseModel):
    desde_paso: str
    confirmo_coste: bool | None = None


class Invalidation(BaseModel):
    pasos: list[str]
    estimacion: Estimate


class MarcaMercado(BaseModel):
    nombre: str
    rol: Literal['marca_brief', 'lider', 'competidor_directo', 'referencia', 'contexto']
    declarada_en_brief: bool
    detectada_en_datos: bool
    tasa_aparicion_espontanea: float
    nota: str | None = None
    excluida: bool | None = None


class ContrasteMercado(BaseModel):
    marcas: list[MarcaMercado]
    no_declaradas_relevantes: list[str]
    discrepancias_brief: list[str]
    candidatas_no_catalogadas: list[str] | None = None
    aprobado_por_humano: bool


class Evidencia(BaseModel):
    metrica: str
    valor: float
    n: int
    tabla: str
    ejecucion_ids: list[str]


class Hallazgo(BaseModel):
    id: str
    titulo: str
    descripcion: str
    tipo: str
    fase_embudo: str | None = None
    motores: list[str] | None = None
    evidencias: list[Evidencia]
    impacto: Literal['alto', 'medio', 'bajo']
    confianza: Literal['alta', 'media', 'baja']
    prioridad: int
    aprobado: bool
    descartado_motivo: str | None = None
    nota: str | None = None
    origen: OriginTag | None = None


class FindingPatch(BaseModel):
    aprobado: bool | None = None
    descartado_motivo: str | None = None
    titulo: str | None = None
    nota: str | None = None


class Objetivo(BaseModel):
    kpi: str
    valor_actual: float
    valor_objetivo_min: float
    valor_objetivo_max: float
    plazo_meses: int
    hallazgos: list[str]


class Accion(BaseModel):
    id: str
    titulo: str
    descripcion: str
    hallazgos_relacionados: list[str]
    palanca: Literal['autoridad_terceros', 'entidad_datos_estructurados', 'contenido', 'reputacion_resenas', 'comunidades', 'tecnico', 'medicion']
    fase_embudo: list[str] | None = None
    motores_objetivo: list[str] | None = None
    ciudades: list[str] | None = None
    esfuerzo: Literal['S', 'M', 'L']
    impacto: Literal['S', 'M', 'L']
    responsable: Literal['cliente_marketing', 'cliente_comunicacion', 'cliente_medico', 'agencia', 'tercero']
    dependencias: list[str] | None = None
    entregables: list[str]
    semana_inicio: int
    plazo_semanas: int
    coste_estimado_eur: float
    kpi: str
    fase_plan: int


class FasePlan(BaseModel):
    numero: int
    nombre: str
    semanas: list[int]
    objetivo: str
    acciones: list[str]


class Plan(BaseModel):
    objetivos: list[Objetivo]
    fases: list[FasePlan]
    acciones: list[Accion]
    coste_total_eur: float
    medicion: str | None = None
    riesgos: list[str] | None = None
    supuestos: list[str] | None = None


class PlanAviso(BaseModel):
    nivel: Literal['info', 'aviso', 'error']
    texto: str
    accion_id: str | None = None


class PlanResponse(BaseModel):
    plan: Plan
    avisos: list[PlanAviso]
    presupuesto_min_eur: float | None = None
    presupuesto_max_eur: float | None = None
    carga_semanal: list[WeeklyLoad] | None = None
    aprobado: bool


class SimulateRequest(BaseModel):
    cambios: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def wrap_cambios(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "cambios" in data and isinstance(data["cambios"], dict):
                return data
            return {"cambios": data}
        return data


class SimulateResult(BaseModel):
    score_actual: float
    score_simulado: float
    puesto_actual: int
    puesto_simulado: int
    etiqueta: str
    detalle: dict[str, Any] | None = None


class Diagnosis(BaseModel):
    ambito: Literal['espontanea', 'asistida']
    marca_proyecto: str
    lider: str | None = None
    indicadores: dict[str, Any]
    graficos: dict[str, Any]
    no_aplica: dict[str, Any] | None = None


class TableData(BaseModel):
    id: str
    titulo: str | None = None
    columnas: list[str]
    filas: list[dict[str, Any]]
    n: int | None = None


class ExecutionRow(BaseModel):
    ejecucion_id: str
    prompt_id: str
    familia: str | None = None
    intencion: str | None = None
    instanciacion: str | None = None
    ambito: Literal['espontanea', 'asistida'] | None = None
    motor: str
    repeticion: int | None = None
    ciudad: str | None = None
    prompt: str
    marcas_a_evaluar: list[str] | None = None
    fecha: str | None = None


class ExecutionPage(BaseModel):
    total: int
    pagina: int
    tamano: int
    filas: list[ExecutionRow]


class BrandEvaluation(BaseModel):
    marca: str
    aparece: bool
    posicion: int | None = None
    tipo_mencion: str | None = None
    fuerza: int
    sentimiento: str | None = None
    tipo_fuente: str | None = None
    calidad_fuente: float | None = None
    juez: str
    confianza: float
    discrepancia: bool | None = None
    fragmento: str | None = None


class ExecutionDetail(BaseModel):
    fila: ExecutionRow
    respuesta: str
    resaltados: list[ExecutionHighlight]
    fuentes: list[ExecutionSource]
    evaluaciones: list[BrandEvaluation]


class ProposalSection(BaseModel):
    id: str
    titulo: str
    markdown: str
    origen: OriginTag


class ReviewSeal(BaseModel):
    cifras_verificadas: int
    cifras_no_trazables: int
    incidencias_normativas: int
    entidades_fuera_catalogo: int
    incidencias: list[ReviewIncident] | None = None
    aprobado: bool


class Proposal(BaseModel):
    modo: Literal['cliente', 'prospecto']
    marca: str
    secciones: list[ProposalSection]
    sello: ReviewSeal
    correo: dict[str, Any] | None = None
    exportaciones: list[Literal['docx', 'md']] | None = None


class JudgeValidation(BaseModel):
    disponible: bool
    campos: list[ValidationField] | None = None
    n: int | None = None


class Discrepancy(BaseModel):
    ejecucion_id: str
    marca: str
    reglas: dict[str, Any]
    llm: dict[str, Any]
    respuesta: str | None = None
    fragmento: str | None = None


class ApprovalRecord(BaseModel):
    punto_control: int
    nombre: str
    fecha: str
    nota: str | None = None
    automatica: bool | None = None


class Quality(BaseModel):
    validacion: JudgeValidation
    discrepancias: list[Discrepancy]
    aprobaciones: list[ApprovalRecord]
    muestra_para_etiquetar: list[str] | None = None


class HumanLabel(BaseModel):
    ejecucion_id: str
    marca: str
    aparece: bool
    posicion: int | None = None
    tipo_mencion: str | None = None
    fuerza: int
    sentimiento: str | None = None
    tipo_fuente: str | None = None


class LabelsPayload(BaseModel):
    etiquetas: list[HumanLabel]


class DiscrepancyResolve(BaseModel):
    valor: dict[str, Any]


class TraceRow(BaseModel):
    pass


class ModelPrices(BaseModel):
    id: str
    nombre: str | None = None
    precio_in_usd_m: float | None = None
    precio_out_usd_m: float | None = None
    contexto: int | None = None


class ModelRoles(BaseModel):
    juez: str | None = None
    redaccion: str | None = None
    propuesta: str | None = None
    chatgpt: str | None = None
    gemini: str | None = None
    claude: str | None = None
    perplexity: str | None = None


class Limits(BaseModel):
    concurrencia: int
    max_llamadas: int
    tope_gasto_eur: float
    usd_eur: float


class Settings(BaseModel):
    clave_configurada: bool
    clave_mascara: str | None = None
    modelos: ModelRoles
    limites: Limits
    carpeta_datos: str
    modelos_inexistentes: list[str] | None = None


class SettingsUpdate(BaseModel):
    clave: str | None = None
    modelos: ModelRoles | None = None
    limites: Limits | None = None


class SettingsTest(BaseModel):
    ok: bool
    latencia_ms: int | None = None
    coste_eur: float | None = None
    gasto_clave_usd: float | None = None
    limite_clave_usd: float | None = None
    mensaje: str


class Health(BaseModel):
    ok: bool
    version: str


class ExecutionHighlight(BaseModel):
    marca: str
    inicio: int
    fin: int


class ExecutionSource(BaseModel):
    dominio: str
    tipo: str | None = None
    calidad: float | None = None


class ReviewIncident(BaseModel):
    tipo: str
    texto: str
    sugerencia: str | None = None
    bloqueante: bool


class WeeklyLoad(BaseModel):
    semana: int
    horas: float
    capacidad: float


class ValidationField(BaseModel):
    campo: str
    exactitud: float
    kappa: float
    matriz: dict[str, Any] | None = None
