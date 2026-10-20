# 🎙️ Guion de Demostración en Vivo (5 minutos) · GEO Copilot

**Reto `reload. × UFV-EPS`** · Duración total: **5:00 min**

---

## Preparación previa (2 minutos antes de entrar)

1. Arrancar la aplicación Streamlit:
   ```bash
   .venv/bin/streamlit run app/Home.py
   ```
2. Pulsar **«⚡ Cargar Modo Demo (`runs/demo/`)»** en la barra lateral para asegurar que `runs/demo/` está cargado en memoria (`0` latencia de red).
3. Tener abierto en una segunda ventana el documento exportado `runs/demo/propuesta_cliente.docx` por si el jurado pide ver el entregable Word nativo.

---

## Cronograma minuto a minuto

### 1. El Gancho (0:00 – 0:30 · 30 s) · *Pantalla: `Home`*
- **Qué decir:**
  > «Clínica Alborada Visión tiene 4,7 estrellas, más de 1.800 reseñas de pacientes y es líder percibida en Madrid. Su Comité de Dirección cree que con esa reputación los asistentes de IA ya la recomiendan. Pero cuando un paciente pregunta a ChatGPT o Claude sin mencionar ninguna marca, **Alborada cae al puesto 7 de 10 con un Score de Citación de solo 27,97 sobre 100**. Hoy os presentamos **GEO Copilot**: el sistema que convierte datos crudos de visibilidad conversacional en una propuesta estratégica verificada, trazable hasta cada respuesta original y lista para enviar al cliente.»
- **Qué mostrar:**
  - Tarjetas superiores de la portada (`Score espontáneo: 27,97/100 · Puesto 7/10`, `Aparición espontánea: 38,8 % (n=240)`, `Presupuesto Plan: 23.950 €`, `Verificador: 563/563 cifras trazables`).

---

### 2. Brief, Faltantes y Mapa Competitivo Real (0:30 – 1:15 · 45 s) · *Pantallas: `1 Brief` y `2 Competidores`*
- **Qué decir:**
  > «En la página 1 cargamos el briefing del cliente. El código —nunca el LLM— calcula la horquilla presupuestaria anual (`18.000 a 27.000 €`) y detecta qué información falta antes de presupuestar (URL exacta, desglose de tráfico web o acceso al CMS), generando las preguntas para el cliente en el **Checkpoint 0**.»
  > «Al pasar a la página 2 (**Checkpoint 1**), el sistema contrasta lo que el cliente cree contra las 240 ejecuciones espontáneas reales: descubre que el verdadero líder en IA es **Grupo Hospitalario Valdecruz** (`Score 61,60`, `90,8 %` de aparición), alerta de que **Vistalia Oftalmología** (`Score 44,54`, `69,2 %` de aparición) les supera sin estar declarada en su brief, e identifica 3 marcas emergentes fuera del catálogo (`OftalmoPlus`, `EuroLaser` y `Clínica Ocularia`).»
- **Qué mostrar:**
  - En `2_Competidores`, señalar la tabla de contraste y las 3 marcas emergentes detectadas automáticamente.

---

### 3. Diagnóstico Espontáneo vs. Asistido y Trazabilidad a la Evidencia (1:15 – 2:45 · 90 s) · *Pantallas: `3 Diagnóstico` y `4 Hallazgos`*
- **Qué decir:**
  > «Aquí es donde la mayoría de herramientas engañaría al cliente: si mezcláramos consultas con marca y sin marca, inflaríamos artificialmente su visibilidad. En `3_Diagnóstico` separamos estrictamente **Espontáneo (`n=240`)** de **Asistido (`n=384`)**.»
  > «Mirad los tres cuellos de botella de Alborada:
  > 1. **Brecha geográfica (`T4`)**: en Madrid aparecen en el **54,2 %** de las consultas (`n=24`), pero en **Barcelona caen al 4,2 % (`1 de 24`)**, justo donde quieren crecer un 25 %.
  > 2. **Asimetría por motor (`T2`)**: funcionan bien en Perplexity (**65,0 %**) y Gemini (**56,7 %**), pero se desploman en **Claude (15,0 %)** y **ChatGPT (18,3 %)**.
  > 3. **Caída en el embudo y fricción de conversión (`T3`)**: en fase de **Decisión** caen al **23,3 %** espontáneo, y cuando el paciente pregunta directamente por ellos en asistido (`n=91`), el **22,0 % de las respuestas contienen advertencias negativas** por falta de precios orientativos y tiempos de espera.»
  > «Y ninguna cifra es una caja negra: si hacemos clic en **Ver evidencia**, leemos la respuesta exacta del motor con la marca resaltada y los dominios citados.»
- **Qué mostrar:**
  - Alternar pestaña **Espontáneo (`n=240`)** y **Asistido (`n=384`)**.
  - Abrir el desplegable `🔎 Ver evidencia` en `3_Diagnóstico` o en la tarjeta `H1`/`H2` de `4_Hallazgos`.

---

### 4. Plan Estratégico, Restricciones y Simulador What-If (2:45 – 3:45 · 60 s) · *Pantalla: `5 Plan`*
- **Qué decir:**
  > «Cada hallazgo aprobado en el **Checkpoint 2** activa acciones concretas en `5_Plan`. No son recomendaciones genéricas: son 11 acciones en 4 fases a 12 meses con entregable, responsable, KPI y grafo de dependencias sin ciclos.»
  > «El módulo `budget.py` garantiza dos restricciones duras del brief: el coste total queda en **23.950 €** (dentro de `18.000–27.000 €`) y la carga del equipo interno de 1,5 personas **nunca supera las 8 horas semanales** (máximo `6,5 h/semana`).»
  > «Abajo, el **Simulador What-If** (claramente etiquetado como *escenario hipotético, no una predicción*) nos permite mover el slider de Barcelona y de ChatGPT/Claude, ver en vivo cómo el Score sube de `27,97` y volcarlo con un clic a los objetivos del plan.»
- **Qué mostrar:**
  - Matriz Esfuerzo vs Impacto, Gantt por semanas, curva de horas semanales bajo la línea roja de `8 h/sem` y mover un slider del simulador.

---

### 5. Confianza: Sello del Revisor y Validación del Juez (3:45 – 4:15 · 30 s) · *Pantallas: `6 Propuesta` y `7 Calidad y trazas`*
- **Qué decir:**
  > «¿Cómo garantizamos al Comité de Dirección que el LLM no ha inventado ni un solo dato? En `6_Propuesta`, el Agente Revisor audita el documento completo: **563 de 563 cifras verificadas contra las tablas deterministas** y **0 incidencias normativas sanitarias** (cero promesas garantizadas, cero comparativas denigratorias).»
  > «Además, en `7_Calidad_y_trazas` auditamos nuestro propio juez contra `muestra_evaluada.csv`: **100 % de exactitud y $\kappa = 1{,}000$ en detección, tipo de mención, fuerza y sentimiento**, documentando con total transparencia el 56,7 % en `tipo_fuente` porque el dataset informa las fuentes a nivel de respuesta y no por marca.»
- **Qué mostrar:**
  - Sello verde en `6_Propuesta` + botón de descarga `.docx`, y tabla de $\kappa$ de Cohen en `7_Calidad_y_trazas`.

---

### 6. Giro Comercial: Modo Prospecto en Frío (4:15 – 4:45 · 30 s) · *Pantalla: `6 Propuesta` → Pestaña `Modo Prospecto`*
- **Qué decir:**
  > «Por último, convertimos el estudio sectorial en una máquina de desarrollo de negocio para la agencia. En la pestaña **Modo Prospecto**, seleccionamos a cualquier competidor sin brief —por ejemplo, **Vistalia Oftalmología** o **Láser Nítida**— y el sistema genera al instante una auditoría ejecutiva de captación con sus 3 brechas reales, 3 intervenciones y un correo comercial de 145 palabras listo para enviar.»
- **Qué mostrar:**
  - Cambiar el selector a `Vistalia Oftalmología` y mostrar el correo comercial listo para copiar y el botón de descarga `.docx`.

---

### 7. Cierre: Impacto en Negocio y Honestidad Metodológica (4:45 – 5:00 · 15 s)
- **Qué decir:**
  > «En resumen: pasamos de días de cruce manual de hojas de cálculo a una propuesta consultiva auditable en menos de un minuto y por menos de 4 céntimos de coste LLM, declarando siempre nuestras limitaciones muestrales ($n=24$ por ciudad y datos sintéticos). Muchas gracias.»

---

## Respuestas rápidas a posibles preguntas del jurado

1. **«¿Cómo evitáis que el falso positivo del adjetivo "nítida" infle a la marca Láser Nítida?»**
   - En `geo/text.py` y `geo/detection.py`, el término corto `"nítida"` solo se acepta cuando va precedido de `"láser"` o `"clínica"`. Así evitamos falsos positivos en frases como *«visión más nítida»* y clavamos **133/133 (100 %)** en `muestra_evaluada.csv`.
2. **«¿Por qué `tipo_fuente` tiene un 56,7 % en apariciones mientras los demás campos tienen un 100 %?»**
   - Porque en `ejecuciones.csv` la columna `Fuentes citadas` contiene los dominios de toda la respuesta (separados por `;`), sin indicar qué dominio respalda a qué marca cuando aparecen 3 o 4 clínicas en el mismo texto. Cuando aparece el dominio propio de la clínica (`oftalmologia-alborada.example`), se asigna `Web propia` con 100 % de certeza; en el resto, existe ambigüedad intrínseca al dato de entrada.
3. **«¿Qué ocurre si se cae la API de Anthropic u OpenAI a mitad de la demo?»**
   - El orquestador (`geo/orchestrator.py`) captura cualquier excepción o falta de clave, activa la degradación elegante (`degradado=True` en `trace.jsonl`) hacia el motor determinista/mock, y además contamos con caché SHA-256 en disco y el directorio `runs/demo/` precalculado.
