# 🎙️ Guion de Demostración en Vivo (5 minutos) · GEO Copilot

**Reto `reload. × UFV-EPS`** · Duración total: **5:00 min**
**Plataforma:** Aplicación Web React + FastAPI (`make app`)

---

## Preparación previa (la noche anterior y antes de entrar)

1. Arrancar la aplicación con el comando único de producción:
   ```bash
   make app
   ```
   En Windows (sin `make`): `.venv\Scripts\python scripts\geo_copilot.py`. La aplicación arranca y se abre en el navegador.
2. En **Ajustes**: clave de OpenRouter configurada y probada (para demostrar conectividad real con modelos LLM) y roles de modelos asignados.
3. Tener en el escritorio o en carpeta accesible:
   - `Brief_de_ejemplo_Clinica_Alborada.docx` (o formato markdown)
   - Carpeta del kit `caso_oftalmologia` con los 5 archivos CSV (`ejecuciones.csv`, `marcas.csv`, `banco_prompts.csv`, `fuentes_catalogo.csv`, `muestra_evaluada.csv`).
4. Ensayar el recorrido completo y borrar o archivar proyectos de ensayo. La lista siempre arranca con **«Ejemplo · Clínica Alborada Visión»** ya analizado (se crea solo al arrancar; si se borra, vuelve al reiniciar). Sirve de plan B: si algo falla en directo, se abre ese proyecto y se sigue la demo desde el Diagnóstico.
5. (Opcional) Tener ya ejecutado un proyecto de otro sector con estudio en vivo en modo «Rápido» para enseñar el funcionamiento y coste real.

---

## Cronograma minuto a minuto

### 1. El Gancho y Creación del Proyecto (0:00 – 0:45 · 45 s) · *Pantalla: `Proyectos` y `Nuevo proyecto (Asistente)`*
- **Qué decir:**
  > «Clínica Alborada Visión tiene 4,7 estrellas, más de 1.800 reseñas de pacientes y es líder percibida en Madrid. Su Comité de Dirección cree que con esa reputación los asistentes de IA ya la recomiendan. Pero cuando un paciente pregunta a ChatGPT o Claude sin mencionar ninguna marca, **Alborada cae al puesto 7 de 10 con un Score de Citación de solo 28 sobre 100**. Hoy os presentamos **GEO Copilot**: la plataforma web que convierte datos crudos de visibilidad conversacional en una propuesta estratégica verificada, trazable hasta cada respuesta original y lista para el cliente.»
- **Qué mostrar:**
  - Pulsar **«Nuevo proyecto»**. Seleccionar **Cliente (tengo su brief)** y asignar nombre.
  - En Paso 2, subir `Brief_de_ejemplo_Clinica_Alborada.docx`. Señalar la vista previa de la ficha (marca, sector, ciudades y objetivo).
  - En Paso 3, subir los 5 CSV en la pestaña «Subir datos del estudio». La plataforma valida las 624 ejecuciones, 4 motores y 3 repeticiones.
  - En Paso 4, dejar el modo **«Parar en cada punto de control»**, marcar la casilla del coste estimado y pulsar **«Lanzar análisis»**. La web abre el Resumen del proyecto con el progreso.

---

### 2. Checkpoints 0 y 1: Ficha y Contraste de Mercado (0:45 – 1:30 · 45 s) · *Pantallas: `Ficha` y `Competencia`*
- **Qué decir:**
  > «El pipeline comienza y se detiene en el **Punto de Control 0**: revisamos y aprobamos la ficha técnica del cliente con sus objetivos y restricciones presupuestarias (`18.000 a 27.000 €`).»
  > «Al reanudar, el sistema ejecuta el contraste de mercado y se detiene en el **Punto de Control 1**: detecta automáticamente que el brief omitía a **Vistalia Oftalmología** (`41,2 %` de aparición espontánea, por encima de Alborada) y que el verdadero líder en IA es **Grupo Hospitalario Valdecruz** (`90,8 %` de aparición y score `75,02`). Aprobamos el mapa competitivo validado.»
- **Qué mostrar:**
  - En el Resumen, el bloque «Siguiente paso: Revisa la ficha» lleva a la Ficha. Aprobar con el botón **«Aprobar»** de la banda «Punto de control 0» al pie de la página.
  - En `Competencia`, mostrar los avisos «Discrepancias entre el brief y los datos» y la tabla de marcas declaradas y no declaradas. Aprobar el **Punto de control 1**.

---

### 3. Diagnóstico Espontáneo vs. Asistido y Trazabilidad a Evidencias (1:30 – 2:45 · 75 s) · *Pantallas: `Diagnóstico` y `Hallazgos`*
- **Qué decir:**
  > «En Diagnóstico demostramos por qué no se pueden mezclar consultas: separamos con un conmutador las **240 consultas espontáneas** (sin marca) de las **asistidas** (las que nombran a la clínica: 108 sobre Alborada).»
  > «Observad los tres cuellos de botella reales de Alborada:
  > 1. **Brecha geográfica**: en Madrid aparecen en el **54,2 %**, pero en **Barcelona caen al 4,2 %** (solo 1 de 24 consultas), justo donde quieren consolidar su centro.
  > 2. **Asimetría de motores**: fuerte presencia en Perplexity (**65,0 %**) y Gemini (**56,7 %**), pero casi invisibles en **Claude (15,0 %)** y **ChatGPT (18,3 %)**.
  > 3. **Embudo de decisión**: caen del 44,7 % en Descubrimiento al 25,0 % en Decisión. En cambio, en consultas asistidas sobre la marca aparecen en el 100 % con solo un 9,3 % de menciones negativas, frente al 34,3 % de su competidor low-cost Láser Nítida.»
  > «Y nada es una caja negra: desde cualquier hallazgo abrimos la respuesta textual original del motor con las marcas resaltadas.»
- **Qué mostrar:**
  - Conmutador Espontánea / Asistida.
  - Gráficos «Marca por motor», «Marca por ciudad» y «Embudo frente al líder».
  - En `Hallazgos`, en H1 (Barcelona): **«Ver evidencias»** → **«Ver ejecuciones»** → pulsar la ejecución para abrir el panel con la respuesta de Gemini y las marcas resaltadas. Cerrar el panel y esperar un segundo antes de pulsar el menú lateral.
  - Aprobar el **Punto de Control 2** al pie de `Hallazgos`.

---

### 4. Plan Estratégico, Simulador y Checkpoint 3 (2:45 – 3:45 · 60 s) · *Pantalla: `Plan`*
- **Qué decir:**
  > «En el Plan Estratégico, las 14 acciones responden a los hallazgos, con matriz Esfuerzo vs. Impacto, cronograma por semanas y control de restricciones: coste total de **24.300 €** (dentro del rango del brief) y carga semanal del equipo del cliente siempre por debajo de su capacidad (pico de 9 horas frente a 18 disponibles).»
  > «Abajo disponemos del **Simulador What-If** (*escenario hipotético, no una predicción*): si Barcelona subiera al 30 % y ChatGPT al 40 %, el score pasaría de 28,0 a 33,8 y Alborada subiría del 7.º al 5.º puesto. Aprobamos el **Punto de Control 3**.»
- **Qué mostrar:**
  - Barra de presupuesto, matriz esfuerzo/impacto, gráfico de carga semanal y cronograma por semanas.
  - En el simulador, mover **Barcelona** a 30 % y **ChatGPT** a 40 % y señalar «Score simulado» y «Puesto simulado».
  - Aprobar el Punto de Control 3.

---

### 5. Propuesta Ejecutiva y Cierre (3:45 – 5:00 · 75 s) · *Pantalla: `Propuesta`*
- **Qué decir:**
  > «Llegamos a la Propuesta Ejecutiva: las 10 secciones del entregable. Cada sección indica quién la produjo: «Generado automáticamente» o «Redactado por IA» con el modelo usado; nunca se atribuye a una IA algo que no escribió.»
  > «El **Sello del Revisor** certifica de forma automática que **las 578 cifras del documento son trazables** a las tablas calculadas y que hay **0 incidencias normativas** en materia sanitaria.»
  > «Descargamos el informe en `.docx`, con las cifras en formato español, listo para entregar al cliente. Y para una prospección comercial en frío, el modo Prospecto genera un gancho, tres oportunidades y un correo comercial.»
- **Qué mostrar:**
  - Vista previa de la propuesta y su etiqueta de origen por sección.
  - Sello del Revisor: «578 cifras trazables · 0 sin traza», «0 incidencias normativas», «0 entidades fuera del catálogo».
  - Botón **«Descargar .docx»**.
  - (Si sobra tiempo) Enseñar `Calidad y trazas` o, desde `Proyectos`, crear un proyecto de tipo **Prospecto** (el modo prospecto es un tipo de proyecto, no una pestaña de este).
