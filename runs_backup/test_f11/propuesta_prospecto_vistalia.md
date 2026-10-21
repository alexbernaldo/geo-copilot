# Propuesta GEO (PROSPECTO) — Vistalia Oftalmología

> **Aviso:** Datos sintéticos del kit UFV-EPS × reload. · `run_id=test_f11` · Fecha: `2026-10-21 00:11`  
> **Verificador GEO: 41/41 cifras trazables · 0 incidencias normativas · Estado: APROBADO**

## Índice de secciones

- 0. Nota metodológica (Modo Prospecto sin brief)

- 1. Gancho

- 2. Oportunidad (3 hallazgos clave)

- 3. Qué haríamos (3 acciones de alto impacto)

- 4. Correo comercial

- Anexo de trazabilidad (Hallazgos → Evidencias → Ejecuciones)

---

## 0. Nota metodológica (Modo Prospecto sin brief)

Esta auditoría de captación para **Vistalia Oftalmología** se ha generado sin brief interno, construyendo la ficha base a partir del catálogo público del sector (`marcas.csv`) y de las 624 ejecuciones del estudio sintético GEO.

## 1. Gancho

**Gancho comercial:** Vistalia Oftalmología ya aparece en el **41.2 %** de las consultas espontáneas en IA (n=240, puesto 8 de 10 con score 26.59), pero solo logra recomendación principal en el **1.7 %** de ellas.

## 2. Oportunidad (3 hallazgos clave)

1. **Brecha de visibilidad espontánea frente a Grupo Hospitalario Valdecruz y competidores directos (H1):** Vistalia Oftalmología registra un score espontáneo de 26.59 con un 41.2% de aparición (n=240), frente al líder Grupo Hospitalario Valdecruz con score 75.02 y 90.8% de aparición (n=240) y frente a Instituto Oftálmico Tramuntana con score 51.70 y 68.8% de aparición (n=240).

1. **Contraste Brief vs Datos: Vistalia omitida, Valdecruz líder real y reseñas insuficientes (H2):** El brief no incluye a Vistalia Oftalmología, que alcanza un 41.2% de aparición espontánea (n=240); además, el líder real en IA es Grupo Hospitalario Valdecruz con un 90.8% (n=240) y no Tramuntana, y las buenas reseñas de Vistalia Oftalmología solo se traducen en un 1.7% de recomendación activa (n=240).

1. **Caída de visibilidad en la fase de Decisión del embudo (H3):** Vistalia Oftalmología pasa de un 41.7% de aparición espontánea en Descubrimiento (n=132) a un 43.8% en la fase crítica de Decisión (n=48), donde Grupo Hospitalario Valdecruz alcanza el 97.9% (n=48).

## 3. Qué haríamos (3 acciones de alto impacto)

1. **Datos estructurados schema.org (MedicalClinic, Physician, MedicalProcedure, FAQPage) (`entidad_datos_estructurados`):** Implementar marcado JSON-LD completo en las fichas de cirugía refractiva, cataratas, miopía infantil y sedes de Madrid y Barcelona, vinculando cuadro médico y acreditaciones. — *Entregable:* Especificación JSON-LD por tipo de página (MedicalClinic, Physician, FAQPage). *KPI:* 100 % de fichas prioritarias y sedes con schema.org validado sin errores.

2. **Auditoría técnica de rastreabilidad para bots de IA (robots.txt, sitemap, renderizado HTML) (`tecnico`):** Configurar acceso explícito para GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot y Google-Extended, optimizando tiempos de respuesta y contenido sin dependencia de JS. — *Entregable:* Archivo robots.txt y sitemap.xml actualizados. *KPI:* Acceso 200 OK verificado para bots de OpenAI, Anthropic, Google y Perplexity.

3. **Normalización de entidad y NAP en directorios sanitarios citados (comparaclinicas.example, directoriomedico.example) (`entidad_datos_estructurados`):** Unificar nombre oficial, sedes (Madrid y Barcelona), especialidades, cuadro médico y horarios en comparaclinicas.example y directoriomedico.example. — *Entregable:* Matriz maestra de atributos NAP y servicios por sede. *KPI:* 100 % de fichas de directorios sectoriales actualizadas y coherentes en Madrid y Barcelona.

## 4. Correo comercial

**Asunto:** Auditoría de visibilidad de Vistalia Oftalmología en ChatGPT, Gemini, Perplexity y Claude

Estimado equipo de Dirección de Vistalia Oftalmología,

En reload. hemos realizado un estudio sectorial independiente sobre cómo recomiendan los asistentes de IA a las clínicas oftalmológicas en España tras analizar 624 ejecuciones en ChatGPT, Gemini, Perplexity y Claude (nota: diagnóstico elaborado a partir de datos públicos y sintéticos del sector, sin brief interno previo de su clínica).

Los resultados muestran una oportunidad muy clara para Vistalia Oftalmología: aunque aparece en el 41.2 % de las consultas espontáneas sin marca (n=240, puesto 8 de 10 con un Score de Citación de 26.59 puntos), solo recibe una recomendación principal activa en el 1.7 % de las ocasiones, y en consultas asistidas presenta un 25.9 % de menciones con advertencias que frenan la conversión frente al líder Grupo Hospitalario Valdecruz (90,8 % de aparición).

Hemos preparado tres intervenciones concretas sobre datos estructurados, contenidos de decisión y gestión de objeciones para transformar esas apariciones pasivas en primeras visitas médicas. ¿Tendrían 20 minutos esta semana para revisar el informe completo con sus evidencias?

## Anexo de trazabilidad (Hallazgos → Evidencias → Ejecuciones)

| Hallazgo | Métrica | Valor | n | Tabla | Ejecucion_IDs de evidencia |
| --- | --- | --- | --- | --- | --- |
| H1 (competencia) | `score_espontaneo[marca=Vistalia Oftalmología]` | 26.59 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H1 (competencia) | `tasa_aparicion_espontanea[marca=Vistalia Oftalmología]` | 41.2 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H1 (competencia) | `score_espontaneo[marca=Grupo Hospitalario Valdecruz]` | 75.02 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H1 (competencia) | `tasa_aparicion_espontanea[marca=Grupo Hospitalario Valdecruz]` | 90.8 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H1 (competencia) | `score_espontaneo[marca=Instituto Oftálmico Tramuntana]` | 51.7 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H1 (competencia) | `tasa_aparicion_espontanea[marca=Instituto Oftálmico Tramuntana]` | 68.8 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H2 (brief_vs_datos) | `tasa_aparicion_espontanea[marca=Vistalia Oftalmología]` | 41.2 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H2 (brief_vs_datos) | `tasa_aparicion_espontanea[marca=Grupo Hospitalario Valdecruz]` | 90.8 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H2 (brief_vs_datos) | `pct_recomendacion_activa_espontanea[marca=Vistalia Oftalmología]` | 1.7 | 240 | T1_espontanea | EJ-0001, EJ-0002, EJ-0003 |
| H3 (embudo) | `tasa_aparicion_espontanea[intencion=Descubrimiento]` | 41.7 | 132 | T3 | EJ-0001, EJ-0002, EJ-0003 |
| H3 (embudo) | `tasa_aparicion_espontanea[intencion=Decisión]` | 43.8 | 48 | T3 | EJ-0154, EJ-0155, EJ-0173 |
| H3 (embudo) | `tasa_aparicion_lider[intencion=Decisión,lider=Grupo Hospitalario Valdecruz]` | 97.9 | 48 | T11 | EJ-0154, EJ-0155, EJ-0173 |


---
_Datos sintéticos · run_id: test_f11 · fecha: 2026-10-21 00:11_
