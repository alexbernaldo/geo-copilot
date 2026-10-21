"""Contratos de datos Pydantic de Preload."""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

Motor = Literal["ChatGPT", "Gemini", "Perplexity", "Claude"]
Intencion = Literal["Descubrimiento", "Comparación", "Validación", "Decisión"]
Instanciacion = Literal["generico", "ciudad", "marca", "par"]
TipoMencion = Literal["Recomendación activa", "Comparación neutra", "Pasiva"]
Sentimiento = Literal["positivo", "neutro", "negativo"]
TipoFuente = Literal["Ranking / institución", "Medio", "Web propia",
                     "Directorio / comparador", "Plataforma de reseñas",
                     "Red social / foro", "Sin fuente"]
Palanca = Literal["autoridad_terceros", "entidad_datos_estructurados", "contenido",
                  "reputacion_resenas", "comunidades", "tecnico", "medicion"]
Talla = Literal["S", "M", "L"]
Responsable = Literal["cliente_marketing", "cliente_comunicacion", "cliente_medico",
                      "agencia", "tercero"]

# ---------- Entrada ----------
class Marca(BaseModel):
    nombre: str
    nivel: Literal["foco", "contexto"]
    rol: str
    dominio: str
    alias: list[str]
    es_marca_brief: bool = False

class Prompt(BaseModel):
    prompt_id: str
    familia: str
    intencion: Intencion
    prioridad: str
    uso: str
    instanciacion: Instanciacion
    plantilla: str

class Ejecucion(BaseModel):
    ejecucion_id: str
    prompt_id: str
    familia: str
    intencion: Intencion
    instanciacion: Instanciacion
    prompt_ejecutado: str
    motor: Motor
    repeticion: int
    marcas_a_evaluar: list[str]
    respuesta: str
    fuentes: list[str]          # dominios
    fecha: str
    ciudad: Optional[str] = None
    espontanea: bool            # instanciacion in {generico, ciudad}

# ---------- Evaluación (una fila por marca y ejecución) ----------
class Evaluacion(BaseModel):
    ejecucion_id: str
    marca: str
    aparece: int                       # 0/1
    posicion: Optional[int] = None
    peso_posicion: int                 # 0..3
    tipo_mencion: Optional[TipoMencion] = None
    fuerza: int = Field(ge=-1, le=3)   # 0 si no aparece
    sentimiento: Optional[Sentimiento] = None
    tipo_fuente: Optional[TipoFuente] = None
    dominio_fuente: Optional[str] = None
    calidad_fuente: Optional[float] = None
    desconocimiento: bool = False      # «no dispongo de información…»
    fragmento: Optional[str] = None    # texto donde se menciona (evidencia)
    juez: Literal["reglas", "llm", "ensemble", "humano"] = "reglas"
    confianza_juez: float = 1.0
    discrepancia: bool = False         # reglas y LLM no coinciden

# ---------- Brief ----------
class FichaMarca(BaseModel):
    marca: str
    web: Optional[str] = None
    sector: str
    subsector: Optional[str] = None
    servicios: list[str] = []
    servicios_prioritarios: list[str] = []
    diferenciales: list[str] = []
    publicos: list[str] = []
    ciudades: list[str] = []
    ciudad_principal: Optional[str] = None
    ciudad_crecimiento: Optional[str] = None
    competidores_declarados: list[str] = []
    situacion_digital: dict[str, str] = {}
    hipotesis_cliente: list[str] = []
    objetivo_principal: str
    kpis_negocio: list[str] = []
    horizonte_meses: int = 12
    presupuesto_min_eur: Optional[float] = None
    presupuesto_max_eur: Optional[float] = None
    equipo: str = ""
    restricciones_normativas: list[str] = []
    tono: str = ""
    audiencia: str = ""
    formato: str = ""

# ---------- Mercado ----------
class MarcaMercado(BaseModel):
    nombre: str
    rol: Literal["marca_brief", "lider", "competidor_directo", "referencia", "contexto"]
    declarada_en_brief: bool
    detectada_en_datos: bool
    tasa_aparicion_espontanea: float
    nota: str = ""

class ContrasteMercado(BaseModel):
    marcas: list[MarcaMercado]
    no_declaradas_relevantes: list[str]     # p. ej. Vistalia, Valdecruz como líder
    discrepancias_brief: list[str]          # texto con cifra y origen
    aprobado_por_humano: bool = False

# ---------- Hallazgos ----------
class Evidencia(BaseModel):
    metrica: str                  # p. ej. "aparicion_espontanea[ciudad=Barcelona]"
    valor: float
    n: int                        # tamaño de muestra
    tabla: str                    # nombre de la tabla de origen
    ejecucion_ids: list[str]      # 3-10 ejemplos

class Hallazgo(BaseModel):
    id: str                       # H1, H2…
    titulo: str
    descripcion: str              # redactado por plantilla de código
    tipo: Literal["geografia", "motor", "embudo", "competencia", "fuentes",
                  "reputacion", "brief_vs_datos", "consistencia", "perfil"]
    fase_embudo: Optional[Intencion] = None
    motores: list[Motor] = []
    evidencias: list[Evidencia]
    impacto: Literal["alto", "medio", "bajo"]
    confianza: Literal["alta", "media", "baja"]
    prioridad: int                # 1 = más importante
    aprobado: bool = True

# ---------- Estrategia y plan ----------
class Objetivo(BaseModel):
    kpi: str
    valor_actual: float
    valor_objetivo_min: float
    valor_objetivo_max: float
    plazo_meses: int
    hallazgos: list[str]

class Accion(BaseModel):
    id: str                       # A1…
    titulo: str
    descripcion: str
    hallazgos_relacionados: list[str]   # obligatorio, ≥1
    palanca: Palanca
    fase_embudo: list[Intencion]
    motores_objetivo: list[Motor]
    ciudades: list[str] = []
    esfuerzo: Talla
    impacto: Talla
    responsable: Responsable
    dependencias: list[str] = []
    entregables: list[str]
    semana_inicio: int
    plazo_semanas: int
    coste_estimado_eur: float
    kpi: str
    fase_plan: Literal[0, 1, 2, 3]

class FasePlan(BaseModel):
    numero: Literal[0, 1, 2, 3]
    nombre: str
    semanas: tuple[int, int]
    objetivo: str
    acciones: list[str]

class Plan(BaseModel):
    objetivos: list[Objetivo]
    fases: list[FasePlan]
    acciones: list[Accion]
    coste_total_eur: float
    medicion: str
    riesgos: list[str]
    supuestos: list[str]

# ---------- Revisión ----------
class Incidencia(BaseModel):
    tipo: Literal["cifra_no_trazable", "promesa_resultado", "comparativa_denigratoria",
                  "tono", "presupuesto", "accion_sin_hallazgo", "campo_vacio"]
    texto: str
    sugerencia: str
    bloqueante: bool

class InformeRevision(BaseModel):
    incidencias: list[Incidencia]
    cifras_verificadas: int
    cifras_no_trazables: int
    aprobado: bool

# ---------- Salida ----------
class Propuesta(BaseModel):
    modo: Literal["cliente", "prospecto"]
    marca: str
    secciones: dict[str, str]     # markdown por sección
    plan: Optional[Plan] = None
    hallazgos: list[Hallazgo]
    revision: InformeRevision
    metadatos: dict               # run_id, fecha, modelo, versión de prompts, coste
