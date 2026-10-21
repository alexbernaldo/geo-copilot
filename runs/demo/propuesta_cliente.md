# Propuesta GEO (CLIENTE) — Clínica Alborada Visión

> **Aviso:** Datos sintéticos del kit UFV-EPS × reload. · `run_id=demo` · Fecha: `2026-10-21 15:56`  
> **Verificador GEO: 578/578 cifras trazables · 0 incidencias normativas · Estado: APROBADO**

## Índice de secciones

- 1. Resumen ejecutivo

- 2. Contexto y alcance

- 3. Diagnóstico de visibilidad

- 4. Análisis de la competencia

- 5. Hallazgos clave

- 6. Estrategia recomendada

- 7. Plan de acción por fases

- 8. Medición y seguimiento

- 9. Riesgos y supuestos

- 10. Hoja de ruta y presupuesto

- Anexo de trazabilidad (Hallazgos → Evidencias → Ejecuciones)

---

## 1. Resumen ejecutivo

Clínica Alborada Visión cuenta con una base asistencial y reputacional muy sólida (valoración de 4,7 sobre 5 con 1.800 opiniones, 14 oftalmólogos y 7.500 intervenciones al año). En respuesta a la hipótesis del cliente («con tan buenas reseñas deberíamos salir recomendados»), los datos asistidos confirman esa fortaleza reputacional: cuando se nombra a la clínica (n=108), presenta una reputación sólida con solo un 9.3 % de menciones negativas y fuerza media de 1.21, frente al 25,9 % de Vistalia Oftalmología (n=108) y el 34,3 % de Láser Nítida (n=108); el problema no es la reputación cuando la nombran, sino la visibilidad espontánea. En las 240 ejecuciones espontáneas del estudio, Clínica Alborada Visión ocupa el puesto 7 de 10 con un Score de Citación de 27.97 puntos, un 38.8 % de aparición y un 6.7 % de recomendación activa, lejos del líder real del mercado (Grupo Hospitalario Valdecruz, con 90.8 % de aparición y score 75.02).

Los datos confirman la preocupación del equipo sobre la sede abierta en 2024: en consultas sobre Barcelona la aparición espontánea cae al 4.2 % (n=24) frente al 54.2 % en Madrid (n=24). Asimismo, la presencia se concentra en Perplexity (65.0 %) y Gemini (56.7 %), mientras que en ChatGPT (18.3 %) y Claude (15.0 %) la clínica apenas es citada, y en la fase de Decisión del embudo desciende al 25.0 %.

Para corregir estas brechas proponemos un plan de acción de 14 iniciativas en 4 fases a 12 meses (con primeros resultados medibles en el mes 6), una inversión total de 24,300 € (dentro de la horquilla disponible de 18,000 € a 27,000 €) y pleno respeto a la regulación de publicidad sanitaria.

## 2. Contexto y alcance

Este diagnóstico evalúa la visibilidad generativa de Clínica Alborada Visión en el sector de clínicas privadas de oftalmología en España a partir de un banco estructurado de 25 plantillas de prompt ejecutadas en 4 motores (ChatGPT, Gemini, Perplexity y Claude) con 3 repeticiones por combinación, sumando 624 ejecuciones (156 por motor) y 2.928 evaluaciones marca-ejecución.

**Aviso importante sobre el origen de los datos:** este estudio se ha realizado sobre el dataset sintético del reto UFV-EPS × reload.; los datos reproducen patrones reales de estudios GEO pero no representan el comportamiento real en producción de ningún modelo ni clínica real.

**Limitaciones metodológicas declaradas:** (1) los modelos generativos son no deterministas y cambian con el tiempo, por lo que el estudio refleja una foto en una fecha concreta; (2) el desglose geográfico cuenta con una muestra de n=24 ejecuciones por ciudad (Madrid y Barcelona); (3) la atribución del tipo de fuente por marca tiene una concordancia parcial en el conjunto de validación (56,7 % en apariciones), por lo que las decisiones estratégicas se apoyan siempre en el conjunto agregado de fuentes citadas.

## 3. Diagnóstico de visibilidad

### 3.1 Visibilidad espontánea (consultas sin marca)

En visibilidad **espontánea** (240 ejecuciones de tipo `generico` y `ciudad`, donde el usuario no nombra ninguna clínica), Clínica Alborada Visión alcanza un Score de Citación de 27.97 sobre 100 y aparece en el 38.8 % de las respuestas. El análisis por motor muestra una dualidad clara: en motores con búsqueda intensiva como Perplexity (65.0 %) y Gemini (56.7 %) la marca supera la mitad de las consultas, pero cae al 18.3 % en ChatGPT y al 15.0 % en Claude. Por fase del embudo, la presencia pasa del 44.7 % en Descubrimiento (n=132) al 25.0 % en Decisión (n=48).

#### Desglose por motor (Espontánea)
| Motor | n | Aparición espontánea | Posición media | Fuerza media | Score (0-100) |
| --- | --- | --- | --- | --- | --- |
| Perplexity | 60 | 65.0 % | 2.44 | 1.20 | 49.08 |
| Gemini | 60 | 56.7 % | 2.79 | 0.88 | 41.38 |
| ChatGPT | 60 | 18.3 % | 4.91 | 0.22 | 11.70 |
| Claude | 60 | 15.0 % | 4.44 | 0.17 | 9.73 |

#### Desglose por fase del embudo (Espontánea)
| Fase del embudo | n | Aparición espontánea | Posición media | Fuerza media | Score (0-100) |
| --- | --- | --- | --- | --- | --- |
| Descubrimiento | 132 | 44.7 % | 2.56 | 0.79 | 33.50 |
| Comparación | 36 | 38.9 % | 3.43 | 0.61 | 27.50 |
| Validación | 24 | 33.3 % | 3.88 | 0.33 | 21.58 |
| Decisión | 48 | 25.0 % | 4.50 | 0.29 | 16.32 |

#### Desglose geográfico: Madrid vs Barcelona (Espontánea)
| Ciudad | n | Aparición espontánea | Posición media | Fuerza media | Score (0-100) |
| --- | --- | --- | --- | --- | --- |
| Madrid | 24 | 54.2 % | 1.92 | 1.04 | 42.17 |
| Barcelona | 24 | 4.2 % | 3.00 | 0.08 | 3.39 |

#### Desglose por familia de prompt (Espontánea)
| Familia de prompt | n | Aparición espontánea | Score (0-100) |
| --- | --- | --- | --- |
| Descubrimiento por perfil | 48 | 58.3 % | 44.96 |
| Descubrimiento genérico | 36 | 47.2 % | 32.52 |
| Decisión final | 24 | 45.8 % | 30.19 |
| Comparación de opciones | 36 | 38.9 % | 27.50 |
| Localización | 48 | 29.2 % | 22.78 |
| Fuentes y citación | 24 | 33.3 % | 21.58 |
| Precio y valor | 24 | 4.2 % | 2.44 |

#### Perfil de fuentes en apariciones de Clínica Alborada Visión
| Tipo de fuente | Apariciones | % sobre apariciones | Calidad catálogo |
| --- | --- | --- | --- |
| Web propia | 42 | 20.9 % | 0.70 |
| Medio | 31 | 15.4 % | 0.90 |
| Plataforma de reseñas | 29 | 14.4 % | 0.60 |
| Ranking / institución | 32 | 15.9 % | 1.00 |
| Directorio / comparador | 41 | 20.4 % | 0.60 |
| Red social / foro | 13 | 6.5 % | 0.40 |
| Sin fuente | 13 | 6.5 % | 0.20 |

### 3.2 Visibilidad asistida (apartado independiente: consultas con marca)

En visibilidad **asistida** (384 ejecuciones del corpus donde el prompt nombra expresamente a la marca o enfrenta un par de clínicas; n=108 para Clínica Alborada Visión), se mide qué dicen los motores cuando ya conocen el nombre de la clínica. Aquí Clínica Alborada Visión muestra una reputación muy sana: fuerza media de 1.21 sobre 3 y tan solo un 9.3 % de menciones con advertencias, destacando de forma recurrente su seguimiento postoperatorio personalizado de 12 meses.

| Puesto | Marca | n | Aparición asistida | Fuerza media | Recomendación activa | Menciones negativas | Score asistido |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Grupo Hospitalario Valdecruz | 72 | 100.0 % | 2.17 | 69.4 % | 16.7 % | 82.99 |
| 2 | Instituto Oftálmico Tramuntana | 132 | 100.0 % | 1.69 | 34.8 % | 5.3 % | 79.84 |
| 3 | Clínica Alborada Visión | 108 | 100.0 % | 1.21 | 6.5 % | 9.3 % | 73.97 |
| 4 | Vistalia Oftalmología | 108 | 100.0 % | 0.74 | 1.9 % | 25.9 % | 68.67 |
| 5 | Láser Nítida | 108 | 100.0 % | 0.55 | 1.9 % | 34.3 % | 67.36 |

## 4. Análisis de la competencia

El contraste con el mercado revela tres aprendizajes clave frente al brief inicial: (1) el líder real en los asistentes de IA es Grupo Hospitalario Valdecruz (90.8 % de aparición espontánea y score 75.02), por delante de la referencia premium declarada Instituto Oftálmico Tramuntana (68,8 %, score 51,70); (2) Vistalia Oftalmología no figuraba en el brief pero alcanza un 41,2 % de aparición espontánea (n=240); y (3) en menciones asistidas, competidores de precio ajustado como Láser Nítida registran un 34,3 % de menciones negativas asociadas al seguimiento postoperatorio, justo el territorio donde Clínica Alborada Visión posee su mayor diferencial clínico.

#### Ranking general de visibilidad espontánea (T1)
| Puesto | Marca | n | Aparición espontánea | Posición media | Fuerza media | Recomendación activa | Score (0-100) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Grupo Hospitalario Valdecruz | 240 | 90.8 % | 1.36 | 1.81 | 34.6 % | 75.02 |
| 2 | Instituto Oftálmico Tramuntana | 240 | 68.8 % | 2.39 | 1.18 | 14.2 % | 51.70 |
| 3 | Oftalmos Centro | 240 | 60.0 % | 3.14 | 0.75 | 4.6 % | 40.70 |
| 4 | Láser Nítida | 240 | 55.8 % | 3.20 | 0.57 | 3.8 % | 37.50 |
| 5 | Clínica del Ojo Cervantes | 240 | 44.2 % | 4.38 | 0.53 | 0.8 % | 28.58 |
| 6 | Instituto Ocular Santa Eulalia | 240 | 42.5 % | 4.02 | 0.54 | 0.4 % | 28.04 |
| 7 | Clínica Alborada Visión | 240 | 38.8 % | 3.05 | 0.62 | 6.7 % | 27.97 |
| 8 | Vistalia Oftalmología | 240 | 41.2 % | 4.09 | 0.45 | 1.7 % | 26.59 |
| 9 | Visionar Clínicas | 240 | 33.3 % | 4.84 | 0.32 | 0.0 % | 20.46 |
| 10 | Centro Lasik Península | 240 | 31.2 % | 4.87 | 0.30 | 0.0 % | 19.39 |

#### Calidad de mención asistida y objeciones recurrentes del mercado (T9)
| Marca | n | Fuerza en apariciones | Menciones negativas | Objeciones recurrentes detectadas |
| --- | --- | --- | --- | --- |
| Grupo Hospitalario Valdecruz | 72 | 2.17 | 16.7 % | Eso sí, algunos pacientes mencionan listas de espera largas y un trato poco personalizado. (12) |
| Instituto Oftálmico Tramuntana | 132 | 1.69 | 5.3 % | Eso sí, su coste es notablemente superior a la media del sector. (7) |
| Clínica Alborada Visión | 108 | 1.21 | 9.3 % | Eso sí, algunos pacientes echan en falta más franjas de cita por la tarde. (3) |
| Vistalia Oftalmología | 108 | 0.74 | 25.9 % | Eso sí, las valoraciones sobre la atención administrativa son desiguales. (9) |
| Láser Nítida | 108 | 0.55 | 34.3 % | Eso sí, hay opiniones que advierten de poca continuidad en el seguimiento postoperatorio. (18) | Entre los inconvenientes que se mencionan sobre Láser Nítida: hay opiniones que advierten de poca continuidad en el seguimiento postoperatorio. (4) | Antes de confirmar con Láser Nítida, ten en cuenta que hay opiniones que advierten de poca continuidad en el seguimiento postoperatorio. (3) |

#### Duelos directos 1 a 1 de Clínica Alborada Visión (T8)
| Duelo directo | Motor | n | Victorias A | Victorias B | Ganador |
| --- | --- | --- | --- | --- | --- |
| Clínica Alborada Visión vs Instituto Oftálmico Tramuntana | ChatGPT | 6 | 2 | 4 | Instituto Oftálmico Tramuntana |
| Clínica Alborada Visión vs Instituto Oftálmico Tramuntana | Gemini | 6 | 3 | 3 | Empate |
| Clínica Alborada Visión vs Instituto Oftálmico Tramuntana | Perplexity | 6 | 3 | 3 | Empate |
| Clínica Alborada Visión vs Instituto Oftálmico Tramuntana | Claude | 6 | 1 | 5 | Instituto Oftálmico Tramuntana |
| Clínica Alborada Visión vs Grupo Hospitalario Valdecruz | ChatGPT | 6 | 1 | 5 | Grupo Hospitalario Valdecruz |
| Clínica Alborada Visión vs Grupo Hospitalario Valdecruz | Gemini | 6 | 2 | 4 | Grupo Hospitalario Valdecruz |
| Clínica Alborada Visión vs Grupo Hospitalario Valdecruz | Perplexity | 6 | 0 | 6 | Grupo Hospitalario Valdecruz |
| Clínica Alborada Visión vs Grupo Hospitalario Valdecruz | Claude | 6 | 1 | 5 | Grupo Hospitalario Valdecruz |

## 5. Hallazgos clave

### H1 · Brecha crítica de visibilidad en Barcelona frente a Madrid
- **Prioridad:** 1 · **Tipo:** `geografia` · **Impacto:** `alto` · **Confianza:** `media`
- **Descripción:** En consultas sin marca sobre Barcelona, Clínica Alborada Visión aparece en el 4.2% de las respuestas (n=24), frente al 54.2% en Madrid (n=24), lo que confirma la hipótesis del cliente sobre la baja visibilidad local en Barcelona.
- **Evidencia trazable:** `tasa_aparicion_espontanea[ciudad=Barcelona]` = 4.2 (T4, n=24, ej: EJ-0406); `tasa_aparicion_espontanea[ciudad=Madrid]` = 54.2 (T4, n=24, ej: EJ-0193, EJ-0195, EJ-0202)

### H2 · Fortaleza en reputación asistida: reputación sólida cuando la nombran; el problema es la visibilidad espontánea
- **Prioridad:** 2 · **Tipo:** `reputacion` · **Impacto:** `alto` · **Confianza:** `alta`
- **Descripción:** FORTALEZA: cuando se consulta por la marca en asistido, Clínica Alborada Visión presenta una reputación sólida con solo un 9.3% de menciones negativas y fuerza media de 1.21 (n=108), frente al 25.9% de Vistalia Oftalmología (n=108) y el 34.3% de Láser Nítida por seguimiento postoperatorio (n=108). Esto contrasta la hipótesis del cliente «con tan buenas reseñas deberíamos salir recomendados»: la reputación es sólida cuando la nombran, pero el problema es la visibilidad espontánea (38.8%, n=240).
- **Evidencia trazable:** `pct_negativo_asistida[marca=Clínica Alborada Visión]` = 9.3 (T9, n=108, ej: EJ-0067, EJ-0079, EJ-0110); `fuerza_media_asistida[marca=Clínica Alborada Visión]` = 1.21 (T9, n=108, ej: EJ-0067, EJ-0079, EJ-0110); `pct_negativo_asistida[marca=Vistalia Oftalmología]` = 25.9 (T9, n=108, ej: EJ-0049, EJ-0074, EJ-0085); `pct_negativo_asistida[marca=Láser Nítida]` = 34.3 (T9, n=108, ej: EJ-0048, EJ-0058, EJ-0060); `tasa_aparicion_espontanea[marca=Clínica Alborada Visión]` = 38.8 (T1_espontanea, n=240, ej: EJ-0002, EJ-0003, EJ-0006)

### H3 · Visibilidad espontánea deficitaria en ChatGPT, Claude
- **Prioridad:** 3 · **Tipo:** `motor` · **Impacto:** `alto` · **Confianza:** `alta`
- **Descripción:** La aparición espontánea de Clínica Alborada Visión cae en ChatGPT (18.3%, n=60), Claude (15.0%, n=60), muy por debajo de su presencia en Perplexity (65.0%, n=60), Gemini (56.7%, n=60).
- **Evidencia trazable:** `tasa_aparicion_espontanea[motor=ChatGPT]` = 18.3 (T2, n=60, ej: EJ-0025, EJ-0153, EJ-0193); `tasa_aparicion_espontanea[motor=Claude]` = 15.0 (T2, n=60, ej: EJ-0012, EJ-0176, EJ-0204); `tasa_aparicion_espontanea[motor=Perplexity]` = 65.0 (T2, n=60, ej: EJ-0003, EJ-0007, EJ-0011); `tasa_aparicion_espontanea[motor=Gemini]` = 56.7 (T2, n=60, ej: EJ-0002, EJ-0006, EJ-0010)

### H4 · Brecha de visibilidad espontánea frente a Grupo Hospitalario Valdecruz y competidores directos
- **Prioridad:** 4 · **Tipo:** `competencia` · **Impacto:** `alto` · **Confianza:** `alta`
- **Descripción:** Clínica Alborada Visión registra un score espontáneo de 27.97 con un 38.8% de aparición (n=240), frente al líder Grupo Hospitalario Valdecruz con score 75.02 y 90.8% de aparición (n=240) y frente a Instituto Oftálmico Tramuntana con score 51.70 y 68.8% de aparición (n=240).
- **Evidencia trazable:** `score_espontaneo[marca=Clínica Alborada Visión]` = 27.97 (T1_espontanea, n=240, ej: EJ-0002, EJ-0003, EJ-0006); `tasa_aparicion_espontanea[marca=Clínica Alborada Visión]` = 38.8 (T1_espontanea, n=240, ej: EJ-0002, EJ-0003, EJ-0006); `score_espontaneo[marca=Grupo Hospitalario Valdecruz]` = 75.02 (T1_espontanea, n=240, ej: EJ-0001, EJ-0002, EJ-0003); `tasa_aparicion_espontanea[marca=Grupo Hospitalario Valdecruz]` = 90.8 (T1_espontanea, n=240, ej: EJ-0001, EJ-0002, EJ-0003); `score_espontaneo[marca=Instituto Oftálmico Tramuntana]` = 51.7 (T1_espontanea, n=240, ej: EJ-0001, EJ-0002, EJ-0003); `tasa_aparicion_espontanea[marca=Instituto Oftálmico Tramuntana]` = 68.8 (T1_espontanea, n=240, ej: EJ-0001, EJ-0002, EJ-0003)

### H5 · Contraste Brief vs Datos: Vistalia omitida, Valdecruz líder real y reseñas insuficientes
- **Prioridad:** 5 · **Tipo:** `brief_vs_datos` · **Impacto:** `alto` · **Confianza:** `alta`
- **Descripción:** El brief no incluye a Vistalia Oftalmología, que alcanza un 41.2% de aparición espontánea (n=240); además, el líder real en IA es Grupo Hospitalario Valdecruz con un 90.8% (n=240) y no Tramuntana, y las buenas reseñas de Clínica Alborada Visión solo se traducen en un 6.7% de recomendación activa (n=240).
- **Evidencia trazable:** `tasa_aparicion_espontanea[marca=Vistalia Oftalmología]` = 41.2 (T1_espontanea, n=240, ej: EJ-0001, EJ-0002, EJ-0003); `tasa_aparicion_espontanea[marca=Grupo Hospitalario Valdecruz]` = 90.8 (T1_espontanea, n=240, ej: EJ-0001, EJ-0002, EJ-0003); `pct_recomendacion_activa_espontanea[marca=Clínica Alborada Visión]` = 6.7 (T1_espontanea, n=240, ej: EJ-0002, EJ-0003, EJ-0006)

### H6 · Caída de visibilidad en la fase de Decisión del embudo
- **Prioridad:** 6 · **Tipo:** `embudo` · **Impacto:** `alto` · **Confianza:** `alta`
- **Descripción:** Clínica Alborada Visión pasa de un 44.7% de aparición espontánea en Descubrimiento (n=132) a un 25.0% en la fase crítica de Decisión (n=48), donde Grupo Hospitalario Valdecruz alcanza el 97.9% (n=48).
- **Evidencia trazable:** `tasa_aparicion_espontanea[intencion=Descubrimiento]` = 44.7 (T3, n=132, ej: EJ-0002, EJ-0003, EJ-0006); `tasa_aparicion_espontanea[intencion=Decisión]` = 25.0 (T3, n=48, ej: EJ-0153, EJ-0155, EJ-0176); `tasa_aparicion_lider[intencion=Decisión,lider=Grupo Hospitalario Valdecruz]` = 97.9 (T11, n=48, ej: EJ-0153, EJ-0155, EJ-0176)

### H7 · Menor respaldo en rankings y prensa sanitaria frente al líder
- **Prioridad:** 7 · **Tipo:** `fuentes` · **Impacto:** `alto` · **Confianza:** `alta`
- **Descripción:** El 31.3% de las apariciones de Clínica Alborada Visión se apoya en Rankings o Medios (n=201, calidad media 0.69), frente al 38.3% de Grupo Hospitalario Valdecruz (n=290).
- **Evidencia trazable:** `pct_fuentes_autoridad[marca=Clínica Alborada Visión]` = 31.3 (T6, n=201, ej: EJ-0002, EJ-0038, EJ-0041); `pct_fuentes_autoridad[marca=Grupo Hospitalario Valdecruz]` = 38.3 (T6, n=290, ej: EJ-0001, EJ-0011, EJ-0018); `calidad_media_fuente[marca=Clínica Alborada Visión]` = 0.69 (T6, n=201, ej: EJ-0002, EJ-0038, EJ-0041)

## 6. Estrategia recomendada

La estrategia recomendada conecta cada hallazgo del diagnóstico con objetivos cuantitativos expresados en rangos realistas a 12 meses (con revisión intermedia en el mes 6), sin realizar promesas de resultado y priorizando las palancas de datos estructurados, páginas locales en Barcelona, contenidos de decisión (precios y seguimiento postoperatorio de 12 meses en positivo) y autoridad en prensa y rankings sanitarios.

#### Objetivos cuantitativos a 12 meses
| Indicador (KPI) | Valor actual | Rango objetivo | Plazo (meses) | Hallazgos |
| --- | --- | --- | --- | --- |
| Score de Citación espontáneo global (0-100) | 27.97 | 40.0 – 48.0 | 12 | H4, H7 |
| Tasa de aparición espontánea global (%) | 38.80 | 50.8 – 58.8 | 12 | H4, H5 |
| Tasa de aparición espontánea en Barcelona (%) | 4.20 | 20.0 – 35.0 | 12 | H1 |
| Tasa de aparición espontánea en ChatGPT (%) | 18.30 | 32.0 – 45.0 | 12 | H3 |
| Tasa de aparición espontánea en fase de Decisión (%) | 25.00 | 38.0 – 50.0 | 12 | H6 |

## 7. Plan de acción por fases

El plan consta de 14 acciones específicas enlazadas a los hallazgos `H1`–`H7`:

| ID | Fase | Acción | Hallazgos | Palanca | Responsable | Esfuerzo | Impacto | Calendario | Coste estimado | KPI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 0 | Datos estructurados schema.org (MedicalClinic, Physician, MedicalProcedure, FAQPage) | H7, H3, H6 | entidad_datos_estructurados | agencia | M | L | S1–S3 (3 sem.) | 2,000 € | 100 % de fichas prioritarias y sedes con schema.org validado sin errores |
| A2 | 0 | Auditoría técnica de rastreabilidad para bots de IA (robots.txt, sitemap, renderizado HTML) | H3 | tecnico | agencia | S | L | S1–S2 (2 sem.) | 750 € | Acceso 200 OK verificado para bots de OpenAI, Anthropic, Google y Perplexity |
| A3 | 0 | Normalización de entidad y NAP en directorios sanitarios citados (comparaclinicas.example, directoriomedico.example) | H7, H1, H5 | entidad_datos_estructurados | cliente_marketing | S | M | S2–S4 (3 sem.) | 1,150 € | 100 % de fichas de directorios sectoriales actualizadas y coherentes en Madrid y Barcelona |
| A4 | 0 | Creación y enriquecimiento de entidad en Wikidata con referencias verificables | H3, H7 | entidad_datos_estructurados | agencia | S | M | S4–S5 (2 sem.) | 550 € | Entidad activa en Wikidata con >= 10 propiedades y referencias externas |
| A5 | 0 | Página de datos institucionales verificables (Memoria de actividad y calidad asistencial) | H5, H3 | entidad_datos_estructurados | cliente_comunicacion | S | L | S2–S3 (2 sem.) | 950 € | Reducción de apariciones en zona de azar y mejora de consistencia 3/3 repeticiones |
| A6 | 1 | Páginas locales en Barcelona por tratamiento prioritario (refractiva, cataratas y miopía infantil) | H1 | contenido | agencia | M | L | S5–S8 (4 sem.) | 2,750 € | Incremento de aparición espontánea en consultas de Barcelona hacia el rango 20 % - 35 % |
| A7 | 0 | Fichas individuales de los 14 oftalmólogos con colegiación, publicaciones y subespecialidad | H7, H3 | entidad_datos_estructurados | cliente_marketing | S | M | S3–S5 (3 sem.) | 900 € | 14 perfiles médicos completos con marcado Physician y autoría clínica visible |
| A8 | 1 | Hub de FAQ citables construidas desde el banco de prompts reales (DG, DP, CO, PR) | H6, H3 | contenido | agencia | M | L | S5–S8 (4 sem.) | 2,000 € | Publicación de 25 bloques Q&A estructurados con datos verificables de la clínica |
| A9 | 1 | Página transparente de precios orientativos, qué incluye el tratamiento y financiación | H6, H4 | contenido | cliente_marketing | S | L | S6–S8 (3 sem.) | 1,000 € | Aumento de aparición espontánea en fase de Decisión desde el 25 % hacia el 38 % - 48 % |
| A10 | 1 | Contenido de puesta en valor del seguimiento postoperatorio de 12 meses (diferencial propio) | H2, H6 | contenido | cliente_medico | S | L | S7–S9 (3 sem.) | 1,250 € | Incremento de menciones de recomendación activa basadas en seguimiento postoperatorio |
| A11 | 2 | Guías específicas por perfil de paciente (miopía infantil para padres, mayores de 60, pilotos) | H6 | contenido | agencia | M | M | S11–S15 (5 sem.) | 2,000 € | Incremento de visibilidad espontánea en prompts de familia DP (Descubrimiento por perfil) |
| A12 | 2 | Plan de PR digital en prensa de salud citada (bienestar-hoy.example, diariosalud.example, saludactual.example) | H7, H4, H5, H2 | autoridad_terceros | agencia | L | L | S11–S22 (12 sem.) | 4,000 € | >= 6 apariciones editoriales en bienestar-hoy.example, diariosalud.example y saludactual.example |
| A13 | 2 | Dossier y candidatura a rankings y guías sectoriales (colegiooftalmologos.example, guiaoftalmologia.example, rankingclinicas.example) | H7, H4 | autoridad_terceros | cliente_comunicacion | M | L | S12–S19 (8 sem.) | 2,000 € | Presencia activa en >= 3 rankings/guías sectoriales de calidad 1.0 |
| A14 | 3 | Re-medición trimestral del estudio GEO (4 oleadas: semanas 12, 24, 36 y 48) e informe a Comité | H1, H3, H6, H4, H7, H2, H5 | medicion | agencia | S | L | S12–S47 (36 sem.) | 3,000 € | 4 oleadas trimestrales ejecutadas (S12, S24, S36, S48) con atribución a primeras visitas |

## 8. Medición y seguimiento

El sistema de seguimiento establece 4 oleadas trimestrales de re-medición (semanas 12, 24, 36 y 48) ejecutando el banco de 25 prompts en los 4 motores con 3 repeticiones (624 ejecuciones por oleada). En el mes 6 (semana 24) se presentará al Comité de Dirección el informe de primeros resultados visibles, cruzando la evolución del Score de Citación espontáneo en Madrid y Barcelona con la evolución de primeras visitas de cirugía refractiva (+25 % objetivo anual del negocio) y consultas asistidas en CRM.

## 9. Riesgos y supuestos

### Riesgos identificados y mitigación
- No determinismo y actualizaciones de los modelos de IA: las respuestas varían entre ejecuciones y por cambios de pesos de cada proveedor.
- Tiempos de indexación y refresco de fuentes de terceros (rankings, directorios y prensa sanitaria).
- Sensibilidad regulatoria en publicidad sanitaria: toda pieza requiere validación médico-legal previa sin promesas de resultado.
- Disponibilidad del equipo interno (1 responsable de marketing + 0,5 comunicación) en semanas de lanzamiento de contenidos.

### Supuestos de trabajo y tarifas
- Supuestos de tarifa orientativos definidos por el equipo para servicios de consultoría GEO, desarrollo técnico y PR digital (sujetos a tarifas oficiales de agencia).
- Los objetivos de visibilidad se formulan como rangos esperados basados en las palancas GEO de la industria, nunca como resultados garantizados.
- Capacidad de dedicación del equipo del cliente estimada en hasta 18 horas semanales combinadas.

## 10. Hoja de ruta y presupuesto

La inversión total asciende a **24,300 €**, dentro del rango presupuestario del brief (18,000 € – 27,000 €) y respetando la capacidad semanal del equipo interno (1 responsable de marketing + 0,5 comunicación).

#### Calendario y presupuesto por fase
| Fase | Semanas | Acciones | Presupuesto fase | Objetivo de la fase |
| --- | --- | --- | --- | --- |
| Fase 0 · Fundamentos técnicos, entidad y datos estructurados | S1–S4 | A1, A2, A3, A4, A5, A7 | 6,300 € | Asegurar que los bots de IA rastreen la web sin fricción y comprendan la entidad médica, sedes y cuadro facultativo. |
| Fase 1 · Contenidos prioritarios, páginas locales (Barcelona) y reputación | S5–S10 | A6, A8, A9, A10 | 7,000 € | Cerrar la brecha de visibilidad en Barcelona y en la fase de Decisión con páginas locales, FAQ citables, precios transparentes y protocolo postoperatorio. |
| Fase 2 · Autoridad en terceros, PR digital, rankings y perfiles de paciente | S11–S36 | A11, A12, A13 | 8,000 € | Construir respaldo en medios sanitarios, rankings institucionales y guías por perfil de paciente para escalar recomendaciones en ChatGPT, Claude, Gemini y Perplexity. |
| Fase 3 · Medición continua y recalibración trimestral | S12–S48 | A14 | 3,000 € | Medir la evolución del Score de Citación en las semanas 12, 24, 36 y 48, verificando primeros resultados visibles en el mes 6. |

#### Reparto por responsable
| Responsable | Nº Acciones | Inversión asociada | % sobre total |
| --- | --- | --- | --- |
| agencia | 8 | 17,050 € | 70.2 % |
| cliente_marketing | 3 | 3,050 € | 12.6 % |
| cliente_comunicacion | 2 | 2,950 € | 12.1 % |
| cliente_medico | 1 | 1,250 € | 5.1 % |

## Anexo de trazabilidad (Hallazgos → Evidencias → Ejecuciones)

| Hallazgo | Métrica | Valor | n | Tabla | Ejecucion_IDs de evidencia |
| --- | --- | --- | --- | --- | --- |
| H1 (geografia) | `tasa_aparicion_espontanea[ciudad=Barcelona]` | 4.2 | 24 | T4 | EJ-0406 |
| H1 (geografia) | `tasa_aparicion_espontanea[ciudad=Madrid]` | 54.2 | 24 | T4 | EJ-0193, EJ-0195, EJ-0202 |
| H2 (reputacion) | `pct_negativo_asistida[marca=Clínica Alborada Visión]` | 9.3 | 108 | T9 | EJ-0067, EJ-0079, EJ-0110 |
| H2 (reputacion) | `fuerza_media_asistida[marca=Clínica Alborada Visión]` | 1.21 | 108 | T9 | EJ-0067, EJ-0079, EJ-0110 |
| H2 (reputacion) | `pct_negativo_asistida[marca=Vistalia Oftalmología]` | 25.9 | 108 | T9 | EJ-0049, EJ-0074, EJ-0085 |
| H2 (reputacion) | `pct_negativo_asistida[marca=Láser Nítida]` | 34.3 | 108 | T9 | EJ-0048, EJ-0058, EJ-0060 |
| H2 (reputacion) | `tasa_aparicion_espontanea[marca=Clínica Alborada Visión]` | 38.8 | 240 | T1_espontanea | EJ-0002, EJ-0003, EJ-0006 |
| H3 (motor) | `tasa_aparicion_espontanea[motor=ChatGPT]` | 18.3 | 60 | T2 | EJ-0025, EJ-0153, EJ-0193 |
| H3 (motor) | `tasa_aparicion_espontanea[motor=Claude]` | 15.0 | 60 | T2 | EJ-0012, EJ-0176, EJ-0204 |
| H3 (motor) | `tasa_aparicion_espontanea[motor=Perplexity]` | 65.0 | 60 | T2 | EJ-0003, EJ-0007, EJ-0011 |
| H3 (motor) | `tasa_aparicion_espontanea[motor=Gemini]` | 56.7 | 60 | T2 | EJ-0002, EJ-0006, EJ-0010 |
| H4 (competencia) | `score_espontaneo[marca=Clínica Alborada Visión]` | 27.97 | 240 | T1_espontanea | EJ-0002, EJ-0003, EJ-0006 |
| H4 (competencia) | `tasa_aparicion_espontanea[marca=Clínica Alborada Visión]` | 38.8 | 240 | T1_espontanea | EJ-0002, EJ-0003, EJ-0006 |
| H4 (competencia) | `score_espontaneo[marca=Grupo Hospitalario Valdecruz]` | 75.02 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H4 (competencia) | `tasa_aparicion_espontanea[marca=Grupo Hospitalario Valdecruz]` | 90.8 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H4 (competencia) | `score_espontaneo[marca=Instituto Oftálmico Tramuntana]` | 51.7 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H4 (competencia) | `tasa_aparicion_espontanea[marca=Instituto Oftálmico Tramuntana]` | 68.8 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H5 (brief_vs_datos) | `tasa_aparicion_espontanea[marca=Vistalia Oftalmología]` | 41.2 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H5 (brief_vs_datos) | `tasa_aparicion_espontanea[marca=Grupo Hospitalario Valdecruz]` | 90.8 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H5 (brief_vs_datos) | `pct_recomendacion_activa_espontanea[marca=Clínica Alborada Visión]` | 6.7 | 240 | T1_espontanea | EJ-0002, EJ-0003, EJ-0006 |
| H6 (embudo) | `tasa_aparicion_espontanea[intencion=Descubrimiento]` | 44.7 | 132 | T3 | EJ-0002, EJ-0003, EJ-0006 |
| H6 (embudo) | `tasa_aparicion_espontanea[intencion=Decisión]` | 25.0 | 48 | T3 | EJ-0153, EJ-0155, EJ-0176 |
| H6 (embudo) | `tasa_aparicion_lider[intencion=Decisión,lider=Grupo Hospitalario Valdecruz]` | 97.9 | 48 | T11 | EJ-0153, EJ-0155, EJ-0176 |
| H7 (fuentes) | `pct_fuentes_autoridad[marca=Clínica Alborada Visión]` | 31.3 | 201 | T6 | EJ-0002, EJ-0038, EJ-0041 |
| H7 (fuentes) | `pct_fuentes_autoridad[marca=Grupo Hospitalario Valdecruz]` | 38.3 | 290 | T6 | EJ-0001, EJ-0011, EJ-0018 |
| H7 (fuentes) | `calidad_media_fuente[marca=Clínica Alborada Visión]` | 0.69 | 201 | T6 | EJ-0002, EJ-0038, EJ-0041 |


---
_Datos sintéticos · run_id: demo · fecha: 2026-10-21 15:56_
