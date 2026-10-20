# 🧭 GEO Copilot · De los datos de visibilidad en IA a la propuesta estratégica y comercial

**Reto `reload. × UFV-EPS` (Hackathon 20–22 de octubre)**

> **Aviso importante:** Este proyecto opera por defecto sobre los **datos sintéticos del kit UFV-EPS × reload.** (`624` ejecuciones, `25` prompts, `10` marcas, `4` motores). Dichos datos no representan el comportamiento real en producción de ningún modelo de lenguaje ni de ninguna clínica sanitaria real.

---

## 1. Qué hace GEO Copilot

**GEO Copilot** transforma el estudio de presencia de marca en motores de respuesta conversacional (**ChatGPT, Gemini, Perplexity y Claude**) y el briefing de un cliente (o una marca en frío sin brief) en:

1. **Diagnóstico riguroso y auditable (`T1`–`T12`)** con separación estricta entre **visibilidad espontánea (`n=240`)** y **visibilidad asistida (`n=384`)**, trazando cada métrica hasta los identificadores exactos de ejecución (`ejecucion_id`).
2. **Contraste de mercado y competidores** que detecta discrepancias entre las creencias del brief y los datos reales de recomendación en IA: identifica que el líder espontáneo real es `Grupo Hospitalario Valdecruz` (`90,8 %` de aparición, `score 75,02`), que `Instituto Oftálmico Tramuntana` es 2º (`68,8 %`, `score 51,70`) y que el brief omite a `Vistalia Oftalmología` (`41,2 %` de aparición espontánea, `score 26,59`) y a otros 5 actores relevantes (`Oftalmos Centro` `60,0 %`, `Clínica del Ojo Cervantes` `44,2 %`, `Instituto Ocular Santa Eulalia` `42,5 %`, `Visionar Clínicas` `33,3 %` y `Centro Lasik Península` `31,2 %`).
3. **Hallazgos priorizados (`H1`–`H7`)** generados por reglas deterministas (`R1`–`R10`) con cifra exacta, tamaño muestral `n`, tabla de origen y desplegable de evidencias originales.
4. **Plan estratégico a 12 meses (`Fases 0 a 3`)** con matriz Esfuerzo vs Impacto, diagrama Gantt por semanas (`S1`–`S52`), control presupuestario automático dentro de la horquilla del brief (`24.300 €` dentro de `18.000–27.000 €`), respeto de la capacidad del equipo del cliente (`<= 8 h/semana`, 1,5 personas) y **Simulador What-If** del Score de Citación.
5. **Propuesta ejecutiva exportable a `.docx` y `.md`** en dos modos:
   - **Modo Cliente** (10 secciones + Anexo de trazabilidad completo para `Clínica Alborada Visión`).
   - **Modo Prospecto** (dossier ejecutivo en frío sin brief previo + correo comercial de 120–180 palabras listo para enviar, p. ej. para `Vistalia Oftalmología` o `Láser Nítida`).
6. **Sello del Agente Revisor**: verificación determinista de que el **100 % de las cifras del documento proceden de las tablas calculadas (`571/571` cifras trazables)** y **0 incidencias de cumplimiento normativo sanitario** (sin promesas garantizadas ni comparativas denigratorias).

---

## 2. Instalación rápida

Requisitos: **Python 3.11+** (probado en Python 3.11 / 3.13).

```bash
# 1. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (opcional: por defecto funciona en modo mock sin claves)
cp .env.example .env
```

---

## 3. Configuración (`.env`)

El sistema funciona al **100 % sin conexión a red ni claves de API** con `LLM_PROVIDER=mock` (configuración por defecto). Si se desea conectar un proveedor LLM real para el juez ensemble, el redactor o los conectores de búsqueda web:

```ini
# Proveedor LLM: mock | anthropic | openai
LLM_PROVIDER=mock
LLM_MODEL=claude-haiku-4-5-20251001
LLM_MODEL_WRITER=claude-sonnet-4-5-20250929

# Claves opcionales (nunca subir al repositorio)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
PERPLEXITY_API_KEY=

# Límites de seguridad y gasto
MAX_LLM_CALLS=1500
MAX_BUDGET_EUR=5.0
```

---

## 4. Comandos principales

### 4.1. Lanzar la interfaz interactiva Streamlit (Modo Demo incluido)
```bash
.venv/bin/streamlit run app/Home.py
```
- En la barra lateral (o en la portada), pulsa **«⚡ Cargar Modo Demo (`runs/demo/`)»** para inspeccionar instantáneamente las 7 páginas con el caso completo de **Clínica Alborada Visión** precalculado.

### 4.2. Ejecutar la suite completa de tests (`pytest`)
```bash
.venv/bin/pytest -q
```
Ejecuta los **34 tests automatizados** que verifican carga de datos, detección 100 % exacta frente a `muestra_evaluada.csv`, juez por reglas (`kappa = 1.000` en mención, fuerza y sentimiento), cálculo del Score y tablas `T1`–`T12`, hallazgos `H1`–`H7`, ajuste presupuestario y de capacidad semanal, revisor de cifras y normativa, pipeline completo de extremo a extremo, simulador what-if y conectores de motores.

### 4.3. Ejecutar el pipeline por línea de comandos (`run_pipeline.py`)
```bash
# Modo Cliente (con el brief de Clínica Alborada Visión)
.venv/bin/python scripts/run_pipeline.py \
  --brief "kit/Kit Participantes Hackaton/01_Briefings/Brief_de_ejemplo_Clinica_Alborada.md" \
  --modo cliente \
  --run-id demo \
  --provider mock \
  --auto-approve

# Modo Prospecto (captación en frío sin brief para Vistalia Oftalmología)
.venv/bin/python scripts/run_pipeline.py \
  --modo prospecto \
  --marca "Vistalia Oftalmología" \
  --run-id demo_prospecto \
  --provider mock \
  --auto-approve
```

### 4.4. Scripts de auditoría numérica y validación del juez
```bash
# Resumen de métricas clave del dataset y tablas T1-T12
.venv/bin/python scripts/smoke_numbers.py

# Comparativa Reglas vs LLM vs Ensemble frente a muestra_evaluada.csv (accuracy y kappa)
.venv/bin/python scripts/validate_judge.py
```

---

## 5. Estructura del repositorio

```text
├── CLAUDE.md                     # Reglas de ingeniería y contratos del proyecto
├── PLAN.md                       # Plan maestro por fases (F0-F16)
├── ARQUITECTURA.md               # Documento técnico de arquitectura y decisiones
├── README.md                     # Guía de instalación, uso y reproducción de la demo
├── requirements.txt              # Dependencias fijadas
├── .env.example                  # Plantilla de variables de entorno
├── docs/
│   └── demo_guion.md             # Guion cronometrado de 5 minutos para la defensa
├── geo/
│   ├── schemas.py                # Contratos Pydantic v2 inmutables
│   ├── config.py                 # Constantes metodológicas, léxicos y ACTION_LIBRARY (22 plantillas)
│   ├── loader.py                 # Lectura y validación de los 5 CSV del kit
│   ├── text.py                   # Normalización, ventana de texto y detección por límites de palabra
│   ├── detection.py              # Detección determinista de apariciones, posición y peso
│   ├── judge_rules.py            # Juez determinista por patrones y catálogo de fuentes
│   ├── judge_llm.py              # Juez LLM estructurado con acotación por código
│   ├── judge.py                  # Ensemble Reglas + LLM con marcado de discrepancias
│   ├── validation.py             # Cálculo de accuracy, kappa de Cohen y matrices de confusión
│   ├── metrics.py                # Fórmula oficial del Score (30/20/30/20) y tablas T1-T12
│   ├── findings.py               # Reglas R1-R10 generadoras de hallazgos trazables H1-H7
│   ├── intake.py                 # Extracción estructurada del brief (.md, .docx, .txt)
│   ├── market.py                 # Contraste de competidores declarados vs detectados y marcas fuera de catálogo
│   ├── budget.py                 # Validación presupuestaria, DAG de dependencias y capacidad semanal
│   ├── strategy.py               # Generación del Plan a 12 meses (Fases 0-3)
│   ├── reviewer.py               # Verificador de cifras (verify_numbers) y cumplimiento normativo (compliance)
│   ├── writer.py                 # Redactor en Modo Cliente (10 secciones) y Modo Prospecto (dossier + email)
│   ├── export.py                 # Exportación a Markdown (.md) y Word (.docx) con Anexo de trazabilidad
│   ├── orchestrator.py           # Orquestador con estado persistente, trazas JSONL y 4 checkpoints humanos
│   ├── simulate.py               # Simulador what-if del Score de Citación (F14)
│   ├── engines/                  # Conectores reales con búsqueda web (OpenAI, Gemini, Claude, Perplexity) (F15)
│   └── prompts/                  # Prompts versionados (*_v1.md) con aislamiento <datos>...</datos>
├── app/
│   ├── Home.py                   # Portada Streamlit y activación en 1 clic del Modo Demo
│   ├── ui_shared.py              # Banner sintético, paleta de marca y visor reutilizable de evidencias
│   └── pages/                    # 7 páginas del flujo (1_Brief a 7_Calidad_y_trazas)
├── scripts/
│   ├── smoke_numbers.py          # Verificación rápida del dataset y tablas T1-T12
│   ├── validate_judge.py         # Informe de exactitud y kappa frente a muestra_evaluada.csv
│   └── run_pipeline.py           # CLI del pipeline completo
├── runs/
│   └── demo/                     # Ejecución precalculada completa lista para demostración offline
└── tests/                        # 34 tests unitarios y de integración con pytest
```
