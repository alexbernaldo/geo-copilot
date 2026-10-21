# 🎙️ Guion de Demostración en Vivo (5 minutos) · GEO Copilot

**Reto `reload. × UFV-EPS`** · Duración total: **5:00 min**
**Plataforma:** Aplicación Web React + FastAPI (`make app`)

---

## Preparación previa (la noche anterior y antes de entrar)

1. Arrancar la aplicación con el comando único de producción:
   ```bash
   make app
   ```
   La aplicación arranca en el navegador en modo aplicación.
2. En **Ajustes**: clave de OpenRouter configurada y probada (para demostrar conectividad real con modelos LLM) y roles de modelos asignados.
3. Tener en el escritorio o en carpeta accesible:
   - `Brief_de_ejemplo_Clinica_Alborada.docx` (o formato markdown)
   - Carpeta del kit `caso_oftalmologia` con los 5 archivos CSV (`ejecuciones.csv`, `marcas.csv`, `banco_prompts.csv`, `motores.csv`, `metricas_agregadas.csv`).
4. Ensayar el recorrido completo y borrar o archivar proyectos de ensayo para comenzar la demo con la lista limpia o con un proyecto previo de otro sector.
5. (Opcional) Tener ya ejecutado un proyecto de otro sector con estudio en vivo en modo «Rápido» para enseñar el funcionamiento y coste real.

---

## Cronograma minuto a minuto

### 1. El Gancho y Creación del Proyecto (0:00 – 0:45 · 45 s) · *Pantalla: `Proyectos` y `Nuevo proyecto (Asistente)`*
- **Qué decir:**
  > «Clínica Alborada Visión tiene 4,7 estrellas, más de 1.800 reseñas de pacientes y es líder percibida en Madrid. Su Comité de Dirección cree que con esa reputación los asistentes de IA ya la recomiendan. Pero cuando un paciente pregunta a ChatGPT o Claude sin mencionar ninguna marca, **Alborada cae al puesto 7 de 10 con un Score de Citación de solo 27,97 sobre 100**. Hoy os presentamos **GEO Copilot**: la plataforma web que convierte datos crudos de visibilidad conversacional en una propuesta estratégica verificada, trazable hasta cada respuesta original y lista para el cliente.»
- **Qué mostrar:**
  - Pulsar **«Nuevo proyecto»**. Seleccionar **Cliente (tengo su brief)** y asignar nombre.
  - En Paso 2, subir `Brief_de_ejemplo_Clinica_Alborada.docx`. Señalar la vista previa inmediata de la ficha (marca, sector, ciudades, presupuesto y campos faltantes).
  - En Paso 3, subir los CSV del estudio en la pestaña de datos. La plataforma valida en milisegundos las 624 ejecuciones, 4 motores y 3 repeticiones.
  - En Paso 4, seleccionar modo **«Parar en cada punto de control»** y pulsar **«Lanzar análisis»**.

---

### 2. Checkpoints 0 y 1: Ficha y Contraste de Mercado (0:45 – 1:30 · 45 s) · *Pantallas: `Ficha` y `Competencia`*
- **Qué decir:**
  > «El pipeline comienza y se detiene en el **Punto de Control 0**: revisamos y aprobamos la ficha técnica del cliente con sus objetivos y restricciones presupuestarias (`18.000 a 27.000 €`).»
  > «Al reanudar, el sistema ejecuta el contraste de mercado y se detiene en el **Punto de Control 1**: detecta automáticamente que el brief omitía a **Vistalia Oftalmología** (`41,2 %` de aparición espontánea, superando a Alborada) y que el verdadero líder en IA es **Grupo Hospitalario Valdecruz** (`90,8 %` de aparición y score `75,02`). Aprobamos el mapa competitivo validado.»
- **Qué mostrar:**
  - Barra superior de Checkpoint con confirmación interactiva.
  - En `Competencia`, mostrar el contraste entre marcas declaradas y detectadas.

---

### 3. Diagnóstico Espontáneo vs. Asistido y Trazabilidad a Evidencias (1:30 – 2:45 · 75 s) · *Pantallas: `Diagnóstico` y `Hallazgos`*
- **Qué decir:**
  > «En Diagnóstico demostramos por qué no se pueden mezclar consultas: separamos con un conmutador **Espontánea (`n=240`)** de **Asistida (`n=384`)**.»
  > «Observad los tres cuellos de botella reales de Alborada:
  > 1. **Brecha geográfica**: en Madrid aparecen en el **54,2 %** (`Score 42,17`), pero en **Barcelona caen al 4,2 %** (solo 1 de 24 consultas), justo donde buscan crecer un 25 %.
  > 2. **Asimetría de motores**: fuerte presencia en Perplexity (**65,0 %**) y Gemini (**56,7 %**), pero invisibles en **Claude (15,0 %)** y **ChatGPT (18,3 %)**.
  > 3. **Embudo de decisión**: caen del 44,7 % en Descubrimiento al 25,0 % en Decisión final. En cambio, en consultas asistidas sobre la marca tienen el 100 % con solo un 9,3 % negativo, frente al 34,3 % de críticas postoperatorias de su competidor low-cost Láser Nítida.»
  > «Y nada es una caja negra: hacemos clic en **Ver evidencia** y abrimos la respuesta textual original del motor con marcas resaltadas.»
- **Qué mostrar:**
  - Conmutador Espontánea / Asistida.
  - Gráficos por motor, ciudad y embudo.
  - Abrir el cajón de evidencia desde una métrica de la tabla o tarjeta de Hallazgos.
  - Aprobar el **Punto de Control 2** en Hallazgos.

---

### 4. Plan Estratégico, Simulador y Checkpoint 3 (2:45 – 3:45 · 60 s) · *Pantalla: `Plan`*
- **Qué decir:**
  > «En el Plan Estratégico, las acciones responden a los hallazgos con matriz Esfuerzo vs. Impacto, cronograma por semanas y estricto control de restricciones: coste total en **24.300 €** (dentro del rango del brief) y carga de trabajo para el equipo del cliente siempre por debajo de 8 horas semanales.»
  > «Abajo disponemos del **Simulador What-If** (*escenario hipotético, no una predicción*), que recalcula el impacto en el Score global al mejorar el rendimiento en Barcelona y ChatGPT. Aprobamos el **Punto de Control 3**.»
- **Qué mostrar:**
  - Matriz 2x2 interactiva, cronograma Gantt y barra de presupuesto y horas.
  - Mover un control del simulador y observar la actualización visual.
  - Aprobar el Punto de Control 3.

---

### 5. Propuesta Ejecutiva y Cierre (3:45 – 5:00 · 75 s) · *Pantalla: `Propuesta`*
- **Qué decir:**
  > «Llegamos a la Propuesta Ejecutiva. Cada sección incluye su etiqueta de origen (`Calculado`, `Generado automáticamente`, `Revisado`).»
  > «El **Sello del Revisor** certifica de forma automática que el **100 % de las cifras proceden de las tablas calculadas** y que existen **0 incidencias deontológicas o normativas** en materia sanitaria.»
  > «Descargamos el informe en `.docx` con formato corporativo impecable listo para entregar al cliente. Y si se tratara de una prospección comercial en frío, disponemos del modo Prospecto con un correo comercial ejecutivo listo para enviar.»
- **Qué mostrar:**
  - Vista previa de la propuesta y etiquetas `OriginTag`.
  - Sello verde del Agente Revisor con 0 incidencias.
  - Botón de descarga de propuesta `.docx`.
  - (Si sobra tiempo) Mostrar la pestaña de prospecto o las trazas técnicas de ejecución.
