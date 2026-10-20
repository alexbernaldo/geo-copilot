# 📋 RESUMEN EJECUTIVO Y TÉCNICO DE LO IMPLEMENTADO · GEO COPILOT

**Reto `reload. × UFV-EPS` · De los datos de visibilidad en IA a la propuesta estratégica y comercial**

---

## 1. Visión general del proyecto completado (`F0` – `F16`)

Se ha construido de extremo a extremo **GEO Copilot**, una plataforma modular en Python + Streamlit que transforma el estudio de visibilidad en asistentes conversacionales (**ChatGPT, Gemini, Perplexity y Claude**) y el briefing de un cliente (o una marca prospecto sin brief) en un **diagnóstico auditable (`T1`–`T12`)**, **hallazgos priorizados (`H1`–`H7`)**, un **plan estratégico a 12 meses presupuestado y nivelado por capacidad** y una **propuesta ejecutiva verificada exportable a `.docx` y `.md`**.

### Indicadores clave verificados del proyecto
- **Fases completadas:** **17 / 17 (`F0` a `F16`)**, cada una con su commit atómico en `main`.
- **Tests automatizados (`pytest`):** **40 / 40 tests en verde** (`100 % pass`).
- **Exactitud del detector (`detection.py`):** **133 / 133 (`100,0 %`)** frente a `muestra_evaluada.csv` en `aparece`, `posicion` y `peso_posicion`.
- **Exactitud del juez (`judge_rules.py` / `judge.py`):**
  - `tipo_mencion`: **100,0 %** ($\kappa = 1{,}000$)
  - `fuerza`: **100,0 %** ($\kappa = 1{,}000$)
  - `sentimiento`: **100,0 %** ($\kappa = 1{,}000$)
  - `tipo_fuente`: **56,7 %** en apariciones ($n=67$, $\kappa = 0{,}468$) · **62,3 %** en *held-out* de 12 ejecuciones ($n=53$, $\kappa = 0{,}527$) · **78,2 %** global ($n=133$, $\kappa = 0{,}715$), documentando el techo determinista por fuentes listadas a nivel de ejecución.
  - Ninguna regla de `geo/judge_rules.py` contiene identificadores `EJ-xxxx`, y las 3 ejecuciones *few-shot* (`EJ-0502`, `EJ-0565`, `EJ-0624`) se excluyen en la validación *held-out* de `scripts/validate_judge.py`.
- **Verificador del Agente Revisor (`reviewer.py`):**
  - `verify_numbers`: **571 / 571 cifras trazables verificadas (`100 %`)**.
  - `verify_entities`: bloquea cualquier marca, dominio, ciudad o perfil ausente de `marcas.csv`, `fuentes_catalogo.csv`, `banco_prompts.csv` o `FichaMarca`.
  - `compliance`: **0 incidencias normativas sanitarias**.

---

## 2. Desglose fase por fase (`F0` a `F16`)

| Fase | Módulos principales | Qué se implementó y verificó |
|---|---|---|
| **F0 · Setup y contratos** | `geo/schemas.py`, `geo/config.py`, `CLAUDE.md`, `requirements.txt` | Contratos Pydantic v2 inmutables (`Marca`, `Ejecucion`, `Evaluacion`, `Hallazgo`, `Accion`, `Plan`, `FichaMarca`, `ContrasteMercado`, `InformeRevision`, `Propuesta`), constantes metodológicas (pesos `30/20/30/20`) y entorno virtual `.venv`. |
| **F1 · Carga y validación** | `geo/loader.py`, `tests/test_loader.py`, `scripts/smoke_numbers.py` | Lectura con `utf-8-sig` de los 5 CSV del kit: `10` marcas, `25` prompts, `624` ejecuciones (`240` espontáneas y `384` asistidas; `24` Madrid y `24` Barcelona), `2.928` pares a evaluar y `133` filas en `muestra_evaluada.csv`. |
| **F2 · Detección de menciones** | `geo/text.py`, `geo/detection.py`, `tests/test_detection.py` | Normalización sin tildes, regex con límites de palabra (`\b`), regla anti-falso positivo para el adjetivo *«nítida»*, cálculo del orden de primera aparición y `peso_posicion` ($\{1:3, 2:2, 3:2, \ge 4:1, \text{ausente}:0\}$). **100 % de acierto (133/133)**. |
| **F3 · Juez por reglas** | `geo/judge_rules.py`, `geo/validation.py`, `scripts/validate_judge.py`, `tests/test_judge_rules.py` | Clasificador determinista para `tipo_mencion`, `fuerza` y `sentimiento` (100 % accuracy, $\kappa=1{,}000$) y cruce con `fuentes_catalogo.csv` para `tipo_fuente` y `calidad_fuente`. |
| **F4 · Juez LLM + Ensemble** | `geo/llm.py`, `geo/prompts/judge_v1.md`, `geo/judge_llm.py`, `geo/judge.py` | Cliente unificado (`mock`, `anthropic`, `openai`) con caché SHA-256 en disco (`cache/`), `temperature=0`, evaluación de todas las marcas presentes en 1 sola llamada por ejecución, acotación por código y marcado de `discrepancia`. |
| **F5 · Métricas y Tablas T1–T12** | `geo/metrics.py`, `tests/test_metrics.py` | Cálculo determinista del **Score de Citación (0–100)** y generación de las tablas **T1 a T12** con `ambito` y `evidencia_ids`. |
| **F6 · Motor de Hallazgos** | `geo/findings.py`, `tests/test_findings.py` | Reglas deterministas `R1`–`R10` que producen los hallazgos `H1`–`H7` para **Clínica Alborada Visión** con cifras reales, tamaño muestral `n`, severidad/prioridad y `ejecucion_ids` trazables. |
| **F7 · Intake de Brief** | `geo/intake.py`, `geo/prompts/intake_v1.md` | Extracción de `FichaMarca` desde `.md`, `.docx`, `.txt` o texto pegado. Cálculo en código del presupuesto anual (`1.500–2.250 €/mes × 12 = 18.000–27.000 €`) y detección de preguntas `faltantes` para el **Checkpoint 0**. |
| **F8 · Contraste de Mercado** | `geo/market.py` | Cruza los competidores declarados en el brief contra `T1_espontanea`, detecta al líder real (`Grupo Hospitalario Valdecruz`, `90,8 %`), confirma a `Instituto Oftálmico Tramuntana` (`68,8 %`) y `Láser Nítida` (`55,8 %`), e identifica los 6 actores no declarados con presencia espontánea $\ge 30\%$ (incluida `Vistalia Oftalmología` con `41,2 %`). |
| **F9 · Estrategia y Presupuesto** | `geo/config.py`, `geo/budget.py`, `geo/strategy.py`, `geo/prompts/strategy_v1.md`, `tests/test_budget.py` | Biblioteca de 22 plantillas (`ACTION_LIBRARY`), generación del Plan a 12 meses en 4 fases (`Fases 0–3`), verificación de DAG sin ciclos, ajuste presupuestario (`24.300 €` dentro de `18.000–27.000 €`) y nivelación de carga del equipo del cliente (`<= 8 h/semana`, pico de `6,5 h/sem`). |
| **F10 · Agente Revisor** | `geo/reviewer.py`, `geo/prompts/compliance_v1.md`, `tests/test_reviewer.py` | Verificador determinista `verify_numbers`, verificador de entidades del kit `verify_entities` y auditor de cumplimiento normativo sanitario (`compliance`). |
| **F11 · Redactor y Exportación** | `geo/writer.py`, `geo/export.py`, `geo/prompts/writer_client_v1.md`, `geo/prompts/writer_prospect_v1.md` | Generación de propuestas en **Modo Cliente** (10 secciones + tablas inyectadas por código + Anexo de trazabilidad) y **Modo Prospecto** (gancho, 3 hallazgos, 3 acciones y correo comercial de 120–180 palabras), con exportación a `.docx` y `.md`. |
| **F12 · Orquestador y CLI** | `geo/orchestrator.py`, `scripts/run_pipeline.py`, `tests/test_pipeline_mock.py`, `runs/demo/` | Gestión de estado por `run_id` (`state.json`), registro de trazas auditable (`trace.jsonl`), reanudación desde el último paso `done`, degradación elegante a `mock`/reglas, soporte de los **4 checkpoints humanos** y generación completa de `runs/demo/`. |
| **F13 · Interfaz Streamlit** | `app/Home.py`, `app/ui_shared.py`, `app/pages/1_Brief.py` … `7_Calidad_y_trazas.py` | Aplicación multipágina con banner fijo de datos sintéticos, botón de **Modo Demo** instantáneo, visor de evidencias reutilizable (`evidence_view`), gráficos Plotly interactivos, los 4 checkpoints humanos y descarga directa de `.docx` y `.md`. |
| **F14 · Simulador What-If** | `geo/simulate.py`, `app/pages/5_Plan.py`, `tests/test_simulate.py` | Simulador interactivo del Score de Citación espontáneo con sliders por ciudad, motor, fuerza media y `% de fuentes de calidad`, etiqueta explícita *«Escenario hipotético, no una predicción»* y botón **«🎯 Usar como objetivo en el Plan»**. |
| **F15 · Conectores APIs Reales** | `geo/engines/__init__.py`, `openai_engine.py`, `gemini_engine.py`, `claude_engine.py`, `perplexity_engine.py`, `tests/test_engines.py` | Conectores con búsqueda web activa (`web_search_preview`, `google_search` grounding, `web_search_20250305`, `Sonar`), caché en disco, estimación de coste previa y mini-estudio de 24 llamadas (`6×2×2`) aislado del dataset sintético del kit. |
| **F16 · Documentación y Demo** | `README.md`, `ARQUITECTURA.md`, `docs/demo_guion.md`, `RESUMEN_IMPLEMENTACION.md` | Guía de instalación y uso, documento de arquitectura con las 9 secciones exigidas por el reto y guion cronometrado de 5 minutos. |

---

## 3. Cifras reales extraídas de `runs/demo/metrics.json` y `runs/demo/tablas/*.parquet`

### 3.1. Tabla `T1_espontanea` completa (`n=240` ejecuciones espontáneas)

| Puesto | Marca (`marcas.csv`) | Dominio (`marcas.csv`) | `n` | Apariciones | Tasa aparición | Score (0–100) | % Recom. activa | % Negativo |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| **1** | **Grupo Hospitalario Valdecruz** | `valdecruz.example` | 240 | 218 | **90,8 %** (`0.9083`) | **75,02** | 34,6 % | 8,8 % |
| **2** | **Instituto Oftálmico Tramuntana** | `tramuntana-oftalmologia.example` | 240 | 165 | **68,8 %** (`0.6875`) | **51,70** | 14,2 % | 4,2 % |
| **3** | **Oftalmos Centro** | `oftalmoscentro.example` | 240 | 144 | **60,0 %** (`0.6000`) | **40,70** | 4,6 % | 7,9 % |
| **4** | **Láser Nítida** | `lasernitida.example` | 240 | 134 | **55,8 %** (`0.5583`) | **37,50** | 3,8 % | 12,9 % |
| **5** | **Clínica del Ojo Cervantes** | `clinicacervantes.example` | 240 | 106 | **44,2 %** (`0.4417`) | **28,58** | 0,8 % | 3,3 % |
| **6** | **Instituto Ocular Santa Eulalia** | `santaeulalia-ocular.example` | 240 | 102 | **42,5 %** (`0.4250`) | **28,04** | 0,4 % | 1,2 % |
| **7** | **Clínica Alborada Visión** *(Marca del Brief)* | `alboradavision.example` | 240 | 93 | **38,8 %** (`0.3875`) | **27,97** | 6,7 % | 1,2 % |
| **8** | **Vistalia Oftalmología** | `vistalia-oftalmologia.example` | 240 | 99 | **41,2 %** (`0.4125`) | **26,59** | 1,7 % | 5,4 % |
| **9** | **Visionar Clínicas** | `visionar-clinicas.example` | 240 | 80 | **33,3 %** (`0.3333`) | **20,46** | 0,0 % | 4,2 % |
| **10** | **Centro Lasik Península** | `lasikpeninsula.example` | 240 | 75 | **31,2 %** (`0.3125`) | **19,39** | 0,0 % | 5,0 % |

### 3.2. Tabla `T1_asistida` completa (5 marcas foco evaluadas en asistido)

| Puesto | Marca | `n` | Apariciones | Tasa aparición | Score asistido | Fuerza media | % Recom. activa | % Negativo | % Desconocimiento |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **1** | **Grupo Hospitalario Valdecruz** | 72 | 72 | 100,0 % | **82,99** | 1,78 | 69,4 % | 16,7 % | 0,0 % |
| **2** | **Instituto Oftálmico Tramuntana** | 132 | 132 | 100,0 % | **79,84** | 1,80 | 34,8 % | 5,3 % | 1,5 % |
| **3** | **Clínica Alborada Visión** | 108 | 108 | 100,0 % | **73,97** | 1,21 | 6,5 % | **9,3 %** | 6,5 % |
| **4** | **Vistalia Oftalmología** | 108 | 108 | 100,0 % | **68,67** | 0,74 | 1,9 % | 25,9 % | 6,5 % |
| **5** | **Láser Nítida** | 108 | 108 | 100,0 % | **67,36** | 0,55 | 1,9 % | **34,3 %** | 2,8 % |

### 3.3. Cortes diagnósticos de `Clínica Alborada Visión` (`metrics.json`)
- **Por ciudad espontánea (`T4`):**
  - **Madrid (`n=24`):** aparición **`54,2 %`** (`0.5417`), Score **`42,17`**.
  - **Barcelona (`n=24`):** aparición **`4,2 %`** (`0.0417`), Score **`3,39`**.
- **Por motor espontáneo (`T2`, `n=60` por motor):**
  - **Perplexity:** aparición **`65,0 %`**, Score **`49,08`**.
  - **Gemini:** aparición **`56,7 %`**, Score **`41,38`**.
  - **ChatGPT:** aparición **`18,3 %`**, Score **`11,70`**.
  - **Claude:** aparición **`15,0 %`**, Score **`9,73`**.
- **Por etapa del embudo espontáneo (`T3` / `T11`):**
  - **Descubrimiento (`n=132`):** aparición **`44,7 %`**, Score **`33,50`**, fuerza media `0,79`.
  - **Comparación (`n=36`):** aparición **`38,9 %`**, Score **`27,50`**, fuerza media `0,61`.
  - **Validación (`n=24`):** aparición **`33,3 %`**, Score **`21,58`**, fuerza media `0,33`.
  - **Decisión (`n=48`):** aparición **`25,0 %`**, Score **`16,32`**, fuerza media `0,29` (frente al `97,9 %` y Score `79,36` de `Grupo Hospitalario Valdecruz`).
- **Consistencia inter-repetición (`T10`, `n=80` tripletes espontáneos):**
  - Presencia consolidada (3/3 repeticiones): **`18,8 %`** (`15/80`).
  - Presencia al azar (1–2/3 repeticiones): **`41,2 %`** (`33/80`).
  - Ausente (0/3 repeticiones): **`40,0 %`** (`32/80`).

### 3.4. Hallazgos generados (`runs/demo/findings.json`, `H1`–`H7`)
1. **`H1` (`geografia`, prioridad 1):** Brecha crítica de visibilidad en Barcelona (`4,2 %`, $n=24$) frente a Madrid (`54,2 %`, $n=24$).
2. **`H2` (`motor`, prioridad 1):** Visibilidad espontánea deficitaria en ChatGPT (`18,3 %`, $n=60$) y Claude (`15,0 %`, $n=60$) frente a Perplexity (`65,0 %`) y Gemini (`56,7 %`).
3. **`H3` (`competencia`, prioridad 1):** Brecha de visibilidad espontánea (`Score 27,97`, `38,8 %`, $n=240$) frente al líder `Grupo Hospitalario Valdecruz` (`Score 75,02`, `90,8 %`) y frente a `Instituto Oftálmico Tramuntana` (`Score 51,70`, `68,8 %`).
4. **`H4` (`brief_vs_datos`, prioridad 1):** Contraste Brief vs Datos: `Vistalia Oftalmología` omitida en el brief alcanza un `41,2 %` de aparición espontánea ($n=240$), `Grupo Hospitalario Valdecruz` es el líder real (`90,8 %`) y las reseñas de `Clínica Alborada Visión` solo se traducen en un `6,7 %` de recomendación activa espontánea ($n=240$).
5. **`H5` (`embudo`, prioridad 2):** Caída de visibilidad en la fase de Decisión del embudo: pasa del `44,7 %` en Descubrimiento ($n=132$) al `25,0 %` en Decisión ($n=48$), donde `Grupo Hospitalario Valdecruz` alcanza el `97,9 %` ($n=48$).
6. **`H6` (`fuentes`, prioridad 2):** Menor respaldo en rankings y prensa sanitaria frente al líder: el `31,3 %` de las apariciones de `Clínica Alborada Visión` se apoya en Rankings o Medios ($n=201$, calidad media `0,69`), frente al `38,3 %` de `Grupo Hospitalario Valdecruz` ($n=290$).
7. **`H7` (`reputacion`, prioridad 7):** Fortaleza en reputación asistida: cuando se consulta por la marca en asistido ($n=108$), `Clínica Alborada Visión` presenta una reputación sólida con solo un `9,3 %` de menciones negativas y fuerza media de `1,21`, frente al `25,9 %` de `Vistalia Oftalmología` ($n=108$) y el `34,3 %` de `Láser Nítida` por seguimiento postoperatorio ($n=108$). Contrasta la hipótesis del cliente *«con tan buenas reseñas deberíamos salir recomendados»*: la reputación es sólida cuando la nombran, pero el problema es la visibilidad espontánea (`38,8 %`, $n=240$).

### 3.5. Plan Estratégico a 12 meses (`runs/demo/plan.json`)
- **Acciones:** **14 acciones** distribuidas en 4 fases (`Fase 0` `S1–S4`, `Fase 1` `S5–S10`, `Fase 2` `S11–S36`, `Fase 3` `S12–S48`), todas trazadas a `H1`–`H7`, sin ciclos de dependencias y sin gastar presupuesto en gestión reputacional (usando `H7` como argumento en contenido `A10` y PR digital `A12`).
- **Presupuesto total:** **`24.300 €`** (dentro del rango `18.000–27.000 €` del brief).
- **Capacidad del equipo del cliente:** máximo **`6,5 h/semana`** (respetando el tope de `8,0 h/semana` para el equipo de 1,5 personas).
