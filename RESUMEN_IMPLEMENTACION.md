# 📋 RESUMEN EJECUTIVO Y TÉCNICO DE LO IMPLEMENTADO · GEO COPILOT

**Reto `reload. × UFV-EPS` · De los datos de visibilidad en IA a la propuesta estratégica y comercial**

---

## 1. Visión general del proyecto completado (`F0` – `F16`)

Se ha construido de extremo a extremo **GEO Copilot**, una plataforma modular en Python + Streamlit que transforma el estudio de visibilidad en asistentes conversacionales (**ChatGPT, Gemini, Perplexity y Claude**) y el briefing de un cliente (o una marca prospecto sin brief) en un **diagnóstico auditable (`T1`–`T12`)**, **hallazgos priorizados (`H1`–`H7`)**, un **plan estratégico a 12 meses presupuestado y nivelado por capacidad** y una **propuesta ejecutiva verificada exportable a `.docx` y `.md`**.

### Indicadores clave verificados del proyecto
- **Fases completadas:** **17 / 17 (`F0` a `F16`)**, cada una con su commit atómico en `main`.
- **Tests automatizados (`pytest`):** **34 / 34 tests en verde** (`100 % pass`).
- **Exactitud del detector (`detection.py`):** **133 / 133 (`100,0 %`)** frente a `muestra_evaluada.csv` en `aparece`, `posicion` y `peso_posicion`.
- **Exactitud del juez (`judge_rules.py` / `judge.py`):**
  - `tipo_mencion`: **100,0 %** ($\kappa = 1{,}000$)
  - `fuerza`: **100,0 %** ($\kappa = 1{,}000$)
  - `sentimiento`: **100,0 %** ($\kappa = 1{,}000$)
  - `tipo_fuente`: **56,7 %** en apariciones ($n=67$) / **78,2 %** global ($n=133$, $\kappa = 0{,}715$), documentando el techo determinista por fuentes listadas a nivel de ejecución.
- **Verificador del Agente Revisor (`reviewer.py`):** **563 / 563 cifras trazables verificadas (`100 %`)** y **0 incidencias normativas sanitarias**.
- **Páginas de la interfaz Streamlit (`app/`):** **8 vistas verificadas con `AppTest` (`0` excepciones)** y precargadas con `runs/demo/`.

---

## 2. Desglose fase por fase (`F0` a `F16`)

| Fase | Commit | Módulos principales | Qué se implementó y verificó |
|---|---|---|---|
| **F0 · Setup y contratos** | `e41512b` | `geo/schemas.py`, `geo/config.py`, `CLAUDE.md`, `requirements.txt` | Contratos Pydantic v2 inmutables (`Marca`, `Ejecucion`, `Evaluacion`, `Hallazgo`, `Accion`, `Plan`, `FichaMarca`, `ContrasteMercado`, `InformeRevision`, `Propuesta`), constantes metodológicas (pesos `30/20/30/20`) y entorno virtual `.venv`. |
| **F1 · Carga y validación** | `b5fbd20` | `geo/loader.py`, `tests/test_loader.py`, `scripts/smoke_numbers.py` | Lectura con `utf-8-sig` de los 5 CSV del kit: `10` marcas, `25` prompts, `624` ejecuciones (`240` espontáneas y `384` asistidas; `24` Madrid y `24` Barcelona), `2.928` pares a evaluar y `133` filas en `muestra_evaluada.csv`. |
| **F2 · Detección de menciones** | `bf3a486` | `geo/text.py`, `geo/detection.py`, `tests/test_detection.py` | Normalización sin tildes, regex con límites de palabra (`\b`), regla anti-falso positivo para el adjetivo *«nítida»*, cálculo del orden de primera aparición y `peso_posicion` ($\{1:3, 2:2, 3:2, \ge 4:1, \text{ausente}:0\}$). **100 % de acierto (133/133)**. |
| **F3 · Juez por reglas** | `0e7addb` | `geo/judge_rules.py`, `geo/validation.py`, `scripts/validate_judge.py`, `tests/test_judge_rules.py` | Clasificador determinista para `tipo_mencion`, `fuerza` y `sentimiento` (100 % accuracy, $\kappa=1{,}000$) y cruce con `fuentes_catalogo.csv` para `tipo_fuente` y `calidad_fuente`. |
| **F4 · Juez LLM + Ensemble** | `83c453c` | `geo/llm.py`, `geo/prompts/judge_v1.md`, `geo/judge_llm.py`, `geo/judge.py` | Cliente unificado (`mock`, `anthropic`, `openai`) con caché SHA-256 en disco (`cache/`), `temperature=0`, evaluación de todas las marcas presentes en 1 sola llamada por ejecución, acotación por código y marcado de `discrepancia`. |
| **F5 · Métricas y Tablas T1–T12** | `56ff282` | `geo/metrics.py`, `tests/test_metrics.py` | Cálculo determinista del **Score de Citación (0–100)** y generación de las tablas **T1 a T12** (ranking espontáneo/asistido, motor, embudo, ciudad, perfil de paciente, fuentes, dominios, pares competitivos, sentimiento asistido y consistencia inter-repetición) con `ambito` y `evidencia_ids`. |
| **F6 · Motor de Hallazgos** | `b7e2457` | `geo/findings.py`, `tests/test_findings.py` | Reglas deterministas `R1`–`R10` que producen los hallazgos `H1`–`H7` para **Clínica Alborada Visión** con cifras reales, tamaño muestral `n`, severidad/prioridad y `ejecucion_ids` trazables. |
| **F7 · Intake de Brief** | `0bcc202` | `geo/intake.py`, `geo/prompts/intake_v1.md` | Extracción de `FichaMarca` desde `.md`, `.docx`, `.txt` o texto pegado. Cálculo en código del presupuesto anual (`1.500–2.250 €/mes × 12 = 18.000–27.000 €`) y detección de preguntas `faltantes` para el **Checkpoint 0**. |
| **F8 · Contraste de Mercado** | `5436a7f` | `geo/market.py` | Cruza los competidores declarados en el brief contra `T1_espontanea`, detecta al líder real (`Grupo Hospitalario Valdecruz`) y competidores omitidos (`Vistalia Oftalmología`) y descubre marcas fuera del catálogo (`OftalmoPlus`, `EuroLaser`, `Clínica Ocularia`) para el **Checkpoint 1**. |
| **F9 · Estrategia y Presupuesto** | `dc0ca2d` | `geo/config.py`, `geo/budget.py`, `geo/strategy.py`, `geo/prompts/strategy_v1.md`, `tests/test_budget.py` | Biblioteca de 22 plantillas (`ACTION_LIBRARY`), generación del Plan a 12 meses en 4 fases (`Fases 0–3`), verificación de DAG sin ciclos, ajuste presupuestario (`23.950 €` dentro de `18.000–27.000 €`) y nivelación de carga del equipo del cliente (`<= 8 h/semana`, pico de `6,5 h/sem`). |
| **F10 · Agente Revisor** | `c9b9050` | `geo/reviewer.py`, `geo/prompts/compliance_v1.md`, `tests/test_reviewer.py` | Verificador determinista `verify_numbers` (comprueba que cada número del texto proceda de las tablas calculadas con tolerancia $\pm 0{,}15$) y auditor de cumplimiento normativo sanitario (`compliance`, bloqueando promesas garantizadas y comparativas denigratorias). |
| **F11 · Redactor y Exportación** | `4161ab7` | `geo/writer.py`, `geo/export.py`, `geo/prompts/writer_client_v1.md`, `geo/prompts/writer_prospect_v1.md` | Generación de propuestas en **Modo Cliente** (10 secciones + tablas inyectadas por código + Anexo de trazabilidad) y **Modo Prospecto** (gancho, 3 hallazgos, 3 acciones y correo comercial de 120–180 palabras), con bucle corrector junto a `reviewer.py` y exportación a `.docx` y `.md`. |
| **F12 · Orquestador y CLI** | `4b9fc30` | `geo/orchestrator.py`, `scripts/run_pipeline.py`, `tests/test_pipeline_mock.py`, `runs/demo/` | Gestión de estado por `run_id` (`state.json`), registro de trazas auditable (`trace.jsonl`), reanudación desde el último paso `done`, degradación elegante a `mock`/reglas, soporte de los **4 checkpoints humanos** y generación completa de `runs/demo/`. |
| **F13 · Interfaz Streamlit** | `028867e` | `app/Home.py`, `app/ui_shared.py`, `app/pages/1_Brief.py` … `7_Calidad_y_trazas.py` | Aplicación multipágina con banner fijo de datos sintéticos, botón de **Modo Demo** instantáneo, visor de evidencias reutilizable (`evidence_view`), gráficos Plotly interactivos, los 4 checkpoints humanos y descarga directa de `.docx` y `.md`. |
| **F14 · Simulador What-If** | `da0a92a` | `geo/simulate.py`, `app/pages/5_Plan.py`, `tests/test_simulate.py` | Simulador interactivo del Score de Citación espontáneo con sliders por ciudad, motor, fuerza media y `% de fuentes de calidad`, etiqueta explícita *«Escenario hipotético, no una predicción»* y botón **«🎯 Usar como objetivo en el Plan»**. |
| **F15 · Conectores APIs Reales** | `d1a03ef` | `geo/engines/__init__.py`, `openai_engine.py`, `gemini_engine.py`, `claude_engine.py`, `perplexity_engine.py`, `tests/test_engines.py` | Conectores con búsqueda web activa (`web_search_preview`, `google_search` grounding, `web_search_20250305`, `Sonar`), caché en disco, estimación de coste previa y mini-estudio de 24 llamadas (`6×2×2`) aislado del dataset sintético del kit. |
| **F16 · Documentación y Demo** | `81052a8` | `README.md`, `ARQUITECTURA.md`, `docs/demo_guion.md` | Guía de instalación y uso, documento de arquitectura con las 9 secciones exigidas por el reto y guion cronometrado de 5 minutos para la defensa ante el jurado. |

---

## 3. Resultados del Caso Práctico: Clínica Alborada Visión (`runs/demo/`)

### 3.1. Diagnóstico cuantitativo clave (`T1`–`T12`)
- **Visibilidad espontánea global (`n=240`):**
  - **Score de Citación espontáneo:** **`27,97 / 100`** (**Puesto 7 de 10**).
  - **Tasa de aparición espontánea:** **`38,8 %`** (`93 / 240` ejecuciones).
  - **Desglose de componentes del Score espontáneo:** Aparición `11,62` / 30 · Posición `4,72` / 20 · Fuerza `6,17` / 30 · Fuente `5,46` / 20.
  - **Líder real del mercado espontáneo:** **Grupo Hospitalario Valdecruz** (`Score 61,60`, aparición `90,8 %`), seguido de **Instituto Oftalmológico Mirasierra** (`Score 52,07`, `77,5 %`) y **Vistalia Oftalmología** (`Score 44,54`, `69,2 %`, no declarada en el brief).
- **Brecha geográfica (`T4`, espontánea):**
  - **Madrid (`n=24`):** **`54,2 %`** de aparición (`13/24`, `Score 39,28`).
  - **Barcelona (`n=24`):** **`4,2 %`** de aparición (`1/24`, `Score 2,89`), frente al objetivo de negocio de crecer un `+25 %` en primeras visitas en Barcelona.
- **Asimetría por motor conversacional (`T2`, espontánea `n=60` por motor):**
  - **Perplexity:** `65,0 %` (`Score 49,61`) · **Gemini:** `56,7 %` (`Score 40,86`) · **ChatGPT:** `18,3 %` (`Score 11,83`) · **Claude:** `15,0 %` (`Score 9,58`).
- **Caída en el embudo de conversión (`T3`, espontánea `n=60` por fase):**
  - **Descubrimiento:** `45,0 %` · **Comparación:** `50,0 %` · **Validación:** `36,7 %` · **Decisión:** **`23,3 %`** (`Score 15,78`).
- **Visibilidad asistida y fricción reputacional (`n=384` total asistido; `n=91` prompts de la marca):**
  - En consultas asistidas donde el paciente incluye a la marca (`n=91`), aparece en el **`100,0 %`**, pero registra un **`22,0 %` de menciones con sentimiento negativo o advertencias** (`20/91`), asociadas a falta de precios orientativos y tiempos de espera en fuentes de terceros.

### 3.2. Hallazgos generados (`H1`–`H7`)
1. **`H1` (`geografia`, prioridad 1):** Desplome en Barcelona (`4,2 %` vs `54,2 %` en Madrid, $n=24$).
2. **`H2` (`motor`, prioridad 1):** Invisibilidad crítica en Claude (`15,0 %`) y ChatGPT (`18,3 %`) frente a Perplexity (`65,0 %`, $n=60$).
3. **`H3` (`embudo`, prioridad 1):** Pérdida de tracción en la fase de Decisión (`23,3 %` espontáneo, $n=60$).
4. **`H4` (`reputacion`, prioridad 2):** Fricción en validación asistida (`22,0 %` de menciones con matices negativos sobre precios/esperas, $n=91$).
5. **`H5` (`brief_vs_datos`, prioridad 2):** Competidor clave omitido en el brief (`Vistalia Oftalmología`, `69,2 %` de aparición espontánea) y liderazgo real de `Grupo Hospitalario Valdecruz` (`90,8 %`).
6. **`H6` (`fuentes`, prioridad 2):** Déficit de citación de la web propia (`oftalmologia-alborada.example`, solo `18,3 %` de las apariciones) y dependencia de directorios/foros.
7. **`H7` (`perfil`, prioridad 3):** Baja cobertura en perfiles específicos (miopía infantil, presbicia/cataratas y paciente con miedo quirúrgico) y aparición de 3 marcas emergentes fuera de catálogo (`OftalmoPlus`, `EuroLaser`, `Clínica Ocularia`).

### 3.3. Plan Estratégico a 12 meses (`plan.json`)
- **11 acciones estructuradas en 4 fases:**
  - **Fase 0 (`S1–S4`):** Auditoría de rastreo IA (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`), marcado Schema.org (`MedicalClinic`, `Physician`, `MedicalProcedure`) y ficha de entidad canónica.
  - **Fase 1 (`S5–S10`):** Páginas locales de Barcelona, guía transparente de precios y financiación, protocolo postoperatorio y de tiempos de espera, y páginas comparativas de técnicas (`LASIK`, `PRK`, `ICL`).
  - **Fase 2 (`S11–S36`):** Dossier clínico de resultados auditados, PR digital en medios sanitarios e instituciones, actualización de directorios médicos y guías por perfil de paciente.
  - **Fase 3 (`S12–S48`):** Re-medición trimestral del estudio GEO en las semanas `12, 24, 36 y 48` (con hito de primeros resultados visibles en el **mes 6 / semana 24**).
- **Presupuesto total:** **`23.950 €`** (dentro del rango `18.000–27.000 €` del brief).
- **Capacidad del equipo del cliente:** máximo **`6,5 h/semana`** (respetando el tope de `8,0 h/semana` para el equipo de 1,5 personas).

---

## 4. Guía rápida de ejecución

```bash
# 1. Ejecutar todos los tests automatizados (34 tests)
.venv/bin/pytest -q

# 2. Arrancar la aplicación interactiva Streamlit
.venv/bin/streamlit run app/Home.py

# 3. Regenerar el pipeline completo en modo cliente (mock, < 3 segundos)
.venv/bin/python scripts/run_pipeline.py \
  --brief "kit/Kit Participantes Hackaton/01_Briefings/Brief_de_ejemplo_Clinica_Alborada.md" \
  --modo cliente \
  --run-id demo \
  --provider mock \
  --auto-approve

# 4. Generar una propuesta comercial en Modo Prospecto (sin brief previo)
.venv/bin/python scripts/run_pipeline.py \
  --modo prospecto \
  --marca "Vistalia Oftalmología" \
  --run-id demo_prospecto \
  --provider mock \
  --auto-approve
```
