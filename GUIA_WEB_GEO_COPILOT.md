# GUÍA · GEO Copilot como aplicación web (React + FastAPI)

Documento de traspaso para Claude Code. Describe qué tiene que hacer la nueva web, qué decisiones están cerradas, cómo se reparte el trabajo entre agentes en paralelo y el prompt exacto de cada uno. El diseño visual y la implementación se delegan a Claude Code dentro de los límites que fija este documento.

Partes:
- **A. Producto:** qué es la web, quién la usa, qué pantallas tiene y qué hace cada una.
- **B. Comportamiento clave:** modo de referencia (detección del caso del kit), estudio en vivo, puntos de control configurables, sectores genéricos.
- **C. Arquitectura técnica:** backend, frontend, almacenamiento, API, eventos.
- **D. Cambios en el motor `geo/`:** qué hay que generalizar y dónde está cada valor fijo hoy.
- **E. Organización multiagente:** agentes, propiedad de archivos, contratos, olas y calendario.
- **F. Fases con prompts para Claude Code.**
- **G. Cómo hacer la demo**, riesgos y checklist.
- **H. Herramientas obligatorias de diseño y verificación:** skills de Emil Kowalski, Impeccable y Taste Skill; MCP de Figma, Playwright y Lovable; puertas de calidad y segunda pasada obligatoria sobre todo lo que salga de Lovable.

---

## 0. Decisiones cerradas con el equipo

| Tema | Decisión |
|---|---|
| Tecnología | Frontend **React (Vite + TypeScript)**. Backend **FastAPI** que envuelve el motor `geo/` actual sin reescribirlo. Streamlit desaparece. |
| Demo | **No hay demo precargada ni botón de demo.** La web arranca vacía, como un producto. La demo la hace el equipo creando un proyecto con el brief y los datos del kit. |
| Origen de los datos del estudio | Dos vías: **subir CSV** con el formato del kit, o **generar el estudio en vivo** contra ChatGPT, Gemini, Claude y Perplexity vía OpenRouter. |
| Estudio en vivo | Una IA **propone** marcas y banco de prompts a partir del brief; el consultor los **edita y aprueba** viendo el coste antes de lanzar. |
| Sectores | **Cualquier sector.** Nada de oftalmología, Madrid, Barcelona ni Alborada fijado en el código de producto. |
| Usuarios | **Local, un consultor, sin login.** Cada análisis es un proyecto guardado en disco. |
| Puntos de control | **Configurables por proyecto:** parar en cada uno (ficha, competencia, hallazgos, plan) o ejecutar del tirón y revisar después. |
| Caso del kit | Si el brief (o los datos) son los del kit de Clínica Alborada Visión, el sistema lo **detecta de forma fija** y **no usa IA real**: juez por reglas, estrategia y redacción por plantillas, sin estudio en vivo, coste 0. |
| Detección | **Huella del archivo** (hash del texto normalizado del brief del kit en `.md` o `.docx`, y de los CSV del kit) **y, como respaldo, la marca** («Clínica Alborada Visión» o el dominio `alboradavision.example`). |
| Visibilidad de la detección | **Invisible en la interfaz.** Solo queda registrada en la traza técnica (`trace.jsonl` y `state.json`). |
| Diseño visual | **Libertad para Claude Code**, con los principios y restricciones de la sección A6. |
| Ejecución | **Multiagente** en paralelo, con contratos (OpenAPI), propiedad exclusiva de archivos, olas y prompts por agente. |
| Herramientas de diseño | **Obligatorias** las skills de Emil Kowalski (`emilkowalski/skills`), Impeccable (`pbakaus/impeccable`) y Taste Skill (`Leonxlnx/taste-skill`), y los MCP de Figma, Playwright y Lovable, cada uno con un papel y una puerta de calidad fijados en la Parte H. |
| Lovable | Se usa para generar el primer borrador de las pantallas. **Nada generado en Lovable entra en el repo sin la segunda pasada** con Impeccable, Taste Skill y las skills de Emil Kowalski (H5). |

### 0.1 Una regla sobre la detección invisible

Que la detección no se vea no significa que la interfaz mienta. La web **nunca** afirma que un texto lo escribió un modelo concreto si no fue así. Las etiquetas de origen de cada bloque salen de lo que dice la traza de ese paso:

- Paso hecho por un LLM real → «Redactado por IA · `<id del modelo>`».
- Paso hecho por plantilla o reglas (modo de referencia, proveedor simulado o degradación) → «Generado automáticamente».
- Cifras → «Calculado».
- Editado por el consultor → «Editado».

Tampoco se simulan esperas para que parezca que hay llamadas de red. El coste mostrado es el real (0 € en modo de referencia). Así el flujo se ve igual en ambos casos y lo que se muestra es cierto.

---

# PARTE A · Producto

## A1. Qué es

GEO Copilot es una estación de trabajo para consultores de GEO (Generative Engine Optimization) de una agencia como reload. Convierte el brief de una marca y un estudio de cómo la citan los asistentes de IA (ChatGPT, Gemini, Perplexity, Claude) en:

1. un **diagnóstico** de visibilidad trazable hasta cada respuesta,
2. **hallazgos** priorizados con evidencia,
3. un **plan de acción** presupuestado, por fases y con responsables,
4. una **propuesta** lista para enviar al cliente (o un dossier y un correo comercial para una marca que todavía no es cliente).

Todas las cifras las calcula el código. La IA interpreta, evalúa respuestas, propone y redacta, y un revisor comprueba que cada número del documento final existe en las tablas.

## A2. Usuario

Un consultor de la agencia, en su portátil. Sabe de marketing y SEO, no de programación. Usa la herramienta varias veces por semana, con proyectos de sectores distintos. Necesita:
- llegar de un brief a una propuesta en una tarde, no en dos semanas;
- defender cada cifra delante del cliente (de dónde sale y con qué muestra);
- controlar lo que gasta en APIs antes de gastarlo;
- intervenir en los momentos clave (qué competidores cuentan, qué hallazgos van, qué acciones entran).

Lectores secundarios del resultado: el comité del cliente (marketing + dirección), que solo ve el documento exportado.

## A3. Recorrido principal

```
Proyectos ─► Nuevo proyecto (asistente) ─► Ejecución con progreso ─► Espacio del proyecto
                                                                     ├─ Resumen
                                                                     ├─ Ficha (punto de control 0)
                                                                     ├─ Datos del estudio
                                                                     ├─ Competencia (punto de control 1)
                                                                     ├─ Diagnóstico
                                                                     ├─ Hallazgos (punto de control 2)
                                                                     ├─ Plan (punto de control 3)
                                                                     ├─ Propuesta
                                                                     └─ Calidad y trazas
Ajustes (global): conexión OpenRouter, modelos, límites
```

## A4. Pantallas

Cada pantalla se describe por su propósito, su contenido, sus acciones y sus estados (vacío, cargando, error, en ejecución). Claude Code decide la composición visual.

### A4.1 Proyectos (inicio)
**Propósito:** ver y abrir los análisis guardados y empezar uno nuevo.

**Contenido:**
- Lista de proyectos: nombre, marca, tipo (cliente / prospecto), origen de los datos (CSV / estudio en vivo), estado (borrador, en ejecución, esperando revisión, completado, con error), fecha de última modificación, coste acumulado en €.
- Filtro por estado y búsqueda por nombre o marca.
- Botón principal «Nuevo proyecto».

**Estados:**
- **Primer uso (sin proyectos):** estado vacío que explica en dos frases qué hace la herramienta y ofrece dos acciones: «Nuevo proyecto» y, si no hay clave de OpenRouter, «Configurar OpenRouter» (enlace a Ajustes). Sin datos de ejemplo.
- Proyecto en ejecución: fila con barra de progreso y paso actual.

**Acciones por proyecto:** abrir, duplicar (copia la configuración y las entradas, no los resultados), renombrar, archivar. Borrar existe pero pide confirmación escribiendo el nombre.

### A4.2 Asistente «Nuevo proyecto»
Cuatro pasos con indicador de progreso arriba. Se puede volver atrás sin perder lo escrito. El borrador se guarda en el backend en cada paso (un proyecto en estado `borrador`).

**Paso 1 · Tipo de análisis**
- «Cliente (tengo su brief)» o «Prospecto (marca que aún no es cliente, sin brief)».
- Nombre del proyecto (sugerido automáticamente a partir de la marca cuando se conozca).

**Paso 2 · Brief** (solo cliente)
- Subir `.md`, `.docx`, `.txt` o `.pdf`, o pegar texto.
- Tras subirlo, el backend extrae la ficha (intake) y muestra un **resumen previo**: marca, sector, ciudades, competidores declarados, presupuesto, horizonte y los campos que faltan. Es solo una vista previa; la revisión completa es el punto de control 0.
- Para prospecto: este paso pide la marca objetivo, su dominio, su sector y su ciudad principal, y opcionalmente la lista de competidores conocidos.

**Paso 3 · Datos del estudio**

Dos pestañas:

*a) Subir datos del estudio (formato del kit)*
- Zona para soltar varios archivos. Reconoce cada uno por sus columnas, no por el nombre del archivo.
- Archivos: `ejecuciones.csv` (obligatorio), `marcas.csv` (obligatorio), `banco_prompts.csv` (obligatorio), `fuentes_catalogo.csv` (opcional: los dominios que falten se clasifican automáticamente), `muestra_evaluada.csv` (opcional: activa la validación del juez contra evaluación humana).
- Informe de validación por archivo: filas leídas, columnas reconocidas, errores bloqueantes (columna que falta, ID duplicado, motor desconocido) y avisos (fuentes vacías en un X % de filas, dominios fuera del catálogo). Botón «Ver filas con error».
- Resumen del estudio cargado: nº de ejecuciones, motores, repeticiones, prompts, marcas, reparto espontáneo/asistido.

*b) Generar el estudio en vivo*
- Requiere clave de OpenRouter; si no hay, la pestaña lo explica y enlaza a Ajustes.
- **Marcas:** botón «Proponer marcas». Un agente con búsqueda web propone la marca del brief, sus competidores declarados y otros competidores relevantes del sector y las ciudades del brief, cada uno con nivel (foco / contexto), dominio y alias. Tabla editable: añadir, quitar, cambiar nivel, editar alias. Máximo 4 foco y 12 en total (límites configurables).
- **Banco de prompts:** botón «Proponer banco». Un agente propone plantillas para las 9 familias de la metodología (sección B3), con intención, prioridad (P1/P2), uso e instanciación (`generico`, `ciudad`, `marca`, `par`) y marcadores `[CIUDAD]`, `[MARCA_A]`, `[MARCA_B]`. Tabla editable con vista previa de cómo se instancia cada plantilla.
- **Tamaño del estudio:** selector «Rápido» (solo P1, 4 motores, 2 repeticiones), «Estándar» (todo, 4 motores, 2 repeticiones) y «Completo» (todo, 4 motores, 3 repeticiones, como el kit). Muestra prompts instanciados × motores × repeticiones = llamadas.
- **Motores:** casillas para los 4, con el modelo de OpenRouter que usa cada uno (configurable en Ajustes).
- **Estimación:** llamadas, tokens y coste en € (precios del catálogo de OpenRouter + coste de búsqueda web), y tiempo estimado. Si supera el tope de gasto por proyecto, el botón de continuar queda bloqueado.

**Paso 4 · Ejecución**
- «Modo de revisión»: «Parar en cada punto de control» (por defecto) o «Ejecutar del tirón y revisar después».
- Modelos que se van a usar (solo lectura, con enlace a Ajustes).
- Resumen de coste total previsto: estudio en vivo (si aplica) + análisis (juez, estrategia, redacción, revisión).
- Casilla «He revisado el coste estimado» obligatoria si hay coste > 0.
- Botón «Lanzar análisis».

### A4.3 Ejecución y progreso
Al lanzar, la web lleva al **Resumen** del proyecto, que muestra el progreso. El progreso también está disponible desde cualquier pantalla (indicador global en la cabecera o barra lateral que abre un panel).

**Contenido del progreso:**
- Lista de pasos con su estado: pendiente, en curso, hecho, hecho en modo automático por error, error, esperando revisión.
  - Pasos del estudio en vivo (si aplica): ejecutar consultas, clasificar fuentes.
  - Pasos del análisis: ficha, detección, juez, métricas, mercado, hallazgos, plan, redacción, revisión, exportación.
- En pasos largos (consultas en vivo, juez), barra con «214 de 624».
- Tiempo transcurrido, llamadas a IA y coste acumulado.
- Al llegar a un punto de control con el modo «parar»: aviso «Esperando tu revisión» con botón que lleva a la pantalla correspondiente.
- Si un paso cae a modo automático por un error de la API (sin saldo, límite de peticiones), aviso en ámbar con el motivo y opción de reintentar ese paso.
- Si se interrumpe (se cerró el servidor), estado «interrumpido» y botón «Reanudar» (los pasos hechos no se repiten y la caché evita pagar dos veces).

**Comportamiento:** se puede navegar por el resto de pantallas mientras corre. Las pantallas cuyo contenido aún no existe muestran «Disponible cuando termine el paso X».

### A4.4 Resumen del proyecto
Página de entrada de cada proyecto.
- Cabecera: marca, tipo, sector, origen de datos, fecha, coste total.
- Estado de los 4 puntos de control y siguiente acción recomendada («Revisa la competencia»).
- 4 a 6 indicadores clave en cuanto existan: score espontáneo de la marca y puesto, % de aparición espontánea, % de recomendación activa, nº de hallazgos, coste del plan frente al presupuesto, sello del revisor (cifras trazables).
- Acceso directo a la propuesta y a la descarga si ya existe.

### A4.5 Ficha (punto de control 0)
- Formulario con todos los campos de `FichaMarca` agrupados: identidad (marca, web, sector, subsector), oferta (servicios, prioritarios, diferenciales), mercado (públicos, ciudades, ciudad principal, ciudad de crecimiento, competidores declarados), situación y objetivos (situación digital, hipótesis del cliente, objetivo principal, KPIs de negocio, horizonte), recursos (presupuesto mínimo y máximo, equipo), comunicación (restricciones normativas, tono, audiencia, formato).
- Campos que faltan resaltados, con el texto del brief del que se extrajo cada campo cuando exista.
- Panel lateral con el brief original (texto) para consultarlo mientras se edita.
- Acciones: «Guardar cambios» y «Aprobar ficha». Si se cambia la ficha después de que existan pasos posteriores, aviso de qué se va a recalcular y su coste antes de confirmar.

### A4.6 Datos del estudio
Explorador de las ejecuciones (subidas o generadas).
- Tabla con filtros por motor, familia, intención, instanciación (espontánea / asistida), ciudad, repetición, y búsqueda de texto.
- Al abrir una ejecución: prompt, motor, respuesta completa con las marcas resaltadas (color propio para la marca del proyecto), fuentes citadas con su tipo y calidad, y la evaluación por marca (aparece, posición, tipo de mención, fuerza, sentimiento, fuente, juez que lo decidió y confianza).
- Es el destino de todos los enlaces «Ver evidencia» del resto de pantallas: se abre filtrado por los `ejecucion_id` de la evidencia.

### A4.7 Competencia (punto de control 1)
- Tabla de marcas con rol (marca del proyecto, líder, competidor directo, referencia, contexto), si estaba declarada en el brief, si aparece en los datos y su % de aparición espontánea.
- Avisos de discrepancia brief/datos, cada uno con su cifra y origen («El brief no menciona a X, que aparece en el 41 % de las respuestas espontáneas, n=240»).
- Marcas candidatas no catalogadas detectadas en las respuestas, con opción de añadirlas al estudio (recalcula detección y siguientes).
- Acciones: cambiar rol, excluir marca del análisis competitivo, aprobar.

### A4.8 Diagnóstico
- Conmutador principal **Espontánea / Asistida**, siempre visible. Nunca se mezclan en un mismo gráfico.
- Indicadores: score de la marca y puesto, componentes del score (aparición, posición, fuerza, fuente), % recomendación activa, % negativo.
- Gráficos (todos con el color de la marca del proyecto destacado y el líder en un segundo color fijo; el resto en neutro):
  - Ranking de marcas por score (T1).
  - Marca × motor (T2), como mapa de calor.
  - Embudo de la marca frente al líder y a la media de competidores (T3/T11).
  - Marca × ciudad (T4), si el estudio tiene prompts de ciudad.
  - Marca × familia de prompt (T5).
  - Perfil de fuentes por marca (T6), barras apiladas por tipo de fuente.
  - Dominios más citados (T7).
  - Duelos 1 a 1 (T8), solo en asistida.
  - Calidad de la mención asistida y objeciones recurrentes (T9).
  - Consistencia entre repeticiones (T10).
  - % de ejecuciones sin búsqueda por motor (T12).
- Cada cifra muestra su origen (tabla y n) al pasar el ratón, y cada gráfico tiene «Ver evidencia».
- Gráficos que no aplican (p. ej. sin prompts de ciudad) no se muestran; en su lugar, una línea que dice por qué.

### A4.9 Hallazgos (punto de control 2)
- Tarjetas H1-H7 ordenadas por prioridad: título, descripción con cifras, tipo, fase del embudo, motores, impacto, confianza, n, y evidencias desplegables con enlace al explorador.
- Acciones por hallazgo: aprobar, descartar (con motivo), editar el título. La descripción con cifras no se edita a mano (la genera el código); si el consultor discrepa, descarta y añade una nota.
- Botón «Aprobar hallazgos» que desbloquea el plan.

### A4.10 Plan (punto de control 3)
- Objetivos: KPI, valor actual (calculado), rango objetivo, plazo, hallazgos que lo justifican.
- Tabla de acciones editable: título, descripción, hallazgos relacionados, palanca, fase del embudo, motores, ciudades, esfuerzo, impacto, responsable, dependencias, entregables, semana de inicio, duración, coste, KPI, fase del plan.
- Al editar, revalidación inmediata en el backend (presupuesto, capacidad del equipo del cliente, dependencias sin ciclos, toda acción con hallazgo) y avisos en línea.
- Matriz esfuerzo/impacto, cronograma por semanas (tipo Gantt) con las 4 fases, barra de presupuesto usado frente al rango del brief, carga semanal del equipo del cliente frente a su capacidad.
- **Simulador** de escenarios: controles de aparición espontánea por ciudad y motor, fuerza media y % de fuentes de calidad; muestra score y puesto actuales frente a simulados, con la etiqueta «Escenario hipotético, no una predicción» y botón «Usar como objetivos del plan».
- Acciones: guardar, aprobar plan.

### A4.11 Propuesta
- **Cliente:** vista previa del documento por secciones (las 10 del formato del entregable), con tablas generadas por código y párrafos redactados. Índice lateral.
- **Prospecto:** gancho, oportunidad (3 hallazgos), qué haríamos (3 acciones) y correo comercial con asunto, listo para copiar.
- **Sello del revisor:** «X/X cifras trazables», «0 incidencias normativas», «0 entidades fuera del catálogo». Si hay incidencias: lista con el texto, el motivo y la sugerencia, en rojo si bloquean.
- Acciones: regenerar redacción (con coste previsto), descargar `.docx` y `.md`, copiar el correo.
- Etiquetas de origen por bloque según la regla 0.1.

### A4.12 Calidad y trazas
- **Validación del juez:** si hay muestra evaluada por humanos, exactitud y kappa por campo (tipo de mención, fuerza, sentimiento, tipo de fuente) y matrices de confusión. Si no la hay, explicación y opción de **evaluar a mano 15 ejecuciones** desde la web (formulario por marca) para obtener la validación. Las etiquetas humanas se guardan como `muestra_evaluada.csv` del proyecto.
- **Cola de discrepancias:** filas donde reglas y LLM no coinciden, con la respuesta y la marca resaltada; el consultor elige el valor correcto y se recalculan métricas y siguientes.
- **Traza:** tabla por paso con proveedor, modelo, duración, llamadas, aciertos de caché, tokens, coste, degradación y error.
- **Registro de aprobaciones** de los puntos de control.

### A4.13 Ajustes (global)
- **Conexión:** clave de OpenRouter (campo de contraseña; se muestra enmascarada si ya existe), «Probar conexión» (valida la clave, muestra gasto y límite de la clave, hace una llamada mínima y da latencia y coste). Enlace a la página de claves de OpenRouter.
- **Modelos por rol:** juez/intake/revisor, estrategia/redacción, propuesta de marcas y banco de prompts, y los 4 motores del estudio en vivo. Selectores con búsqueda alimentados por el catálogo de OpenRouter, mostrando precio por millón de tokens de entrada y salida. Aviso si un modelo guardado ya no existe.
- **Límites:** concurrencia, tope de llamadas por proyecto, tope de gasto por proyecto en €, tipo de cambio USD/EUR.
- **Datos:** carpeta donde se guardan los proyectos (solo lectura) y botón para abrirla.

## A5. Requisitos no funcionales
- Idioma: **español de España** en toda la interfaz y las salidas. Números con formato español (`39,4 %`, `24.300 €`).
- Arranque con un comando (`make app` o el lanzador) que abre el navegador.
- Funciona sin red para todo lo que no sea IA real: tipografías y recursos servidos en local.
- La clave solo vive en `.env` (permisos 600). Nunca en respuestas de la API, logs, trazas ni exportaciones.
- Un solo análisis en ejecución a la vez (evita mezclar contadores de coste y gastar el doble).
- Accesible: navegación por teclado, foco visible, contraste AA, gráficos con texto alternativo o tabla equivalente.
- Pantallas de 1280 px como objetivo principal; usable en 1024 px. No hace falta versión móvil completa, pero nada se rompe en una tablet.
- Tiempo de carga de una pantalla de proyecto terminado: < 1 s en local.

## A6. Principios de diseño (la dirección visual la elige Claude Code)
1. **Herramienta de trabajo, no página de marketing.** Densidad calma, jerarquía clara, sin decoración que no informe.
2. **Cada cifra dice de dónde sale** (tabla y n) y quién la produjo (cálculo, IA, consultor).
3. **Espontánea y asistida nunca se mezclan**, y cada una tiene una identidad visual constante en toda la web.
4. **Un color para la marca del proyecto y uno para el líder**, constantes en todos los gráficos. El resto, neutros.
5. **Los puntos de control son el pulso del flujo:** siempre se ve cuál toca y cuál está aprobado.
6. **El coste se ve antes de gastarlo.** Ninguna acción con coste sin estimación y confirmación.
7. **Claro y oscuro.**
8. Sin emojis, sin lenguaje de marketing, sin ilustraciones genéricas.

**Entregable de diseño obligatorio antes de construir pantallas** (fase W1, con el proceso de H4): `DESIGN.md` en la raíz del repo (donde lo leen Impeccable y Taste Skill) con la dirección elegida y por qué, los tokens (color, tipografía, espaciado, radios, sombras) en claro y oscuro, la escala tipográfica y una página `/_kit` que muestre todos los componentes compartidos. El equipo revisa la página `/_kit` y las capturas antes de que se construyan las pantallas finales.

---

# PARTE B · Comportamiento clave

## B1. Modo de referencia (caso del kit)

### B1.1 Qué es
Cuando el proyecto usa el brief del kit (Clínica Alborada Visión) o los datos del kit, el sistema entra en **modo de referencia**:
- Los datos del estudio son siempre los del kit (`ejecuciones.csv`, `marcas.csv`, `banco_prompts.csv`, `fuentes_catalogo.csv`, `muestra_evaluada.csv`), aunque el consultor haya elegido «Generar en vivo» o haya subido otros CSV.
- El proveedor de IA se fuerza a `mock` en todos los pasos: intake por parser de plantilla, juez por reglas, estrategia por reglas y plantillas, redacción por plantillas, revisor normativo por reglas.
- No se hace ninguna llamada de red. Coste 0.
- El resultado es idéntico al que produce hoy `Run(provider="mock")` con el brief del kit (hay un test de regresión que lo garantiza, F-B2).

### B1.2 Cómo se detecta
Módulo `geo/reference.py`:

```python
REFERENCE_DIR: Path            # carpeta con los archivos del kit dentro del backend (ver C4)
REFERENCE_BRAND = "Clínica Alborada Visión"
REFERENCE_DOMAIN = "alboradavision.example"

def normalize_for_fingerprint(text: str) -> str
    # NFKC → minúsculas → quitar tildes → quitar marcas markdown (*, #, _, `, >, |, -) →
    # quitar todos los espacios y saltos de línea → quitar puntuación.
def fingerprint_text(text: str) -> str            # sha256 de lo anterior
def fingerprint_csv(path: Path) -> str            # sha256 de las filas leídas con pandas (utf-8-sig),
                                                  # columnas ordenadas, valores como texto, sin BOM ni finales de línea
REFERENCE_FINGERPRINTS: dict[str, set[str]]       # {"brief": {...}, "ejecuciones": {...}, "marcas": {...}, ...}
                                                  # constante generada por scripts/compute_reference_fingerprints.py
def detect_reference(*, brief_text: str | None, csv_paths: dict[str, Path] | None,
                     prospect_brand: str | None, prospect_domain: str | None) -> tuple[bool, str]
    # Devuelve (es_referencia, motivo). Motivo ∈ {"huella_brief", "huella_datos", "marca", "dominio", ""}.
```

Reglas de `detect_reference` (en este orden; basta una):
1. La huella del brief está en `REFERENCE_FINGERPRINTS["brief"]`. El conjunto incluye la huella del `.md` y la del `.docx` del kit (el texto extraído de ambos puede diferir).
2. La huella de `ejecuciones.csv` subido está en `REFERENCE_FINGERPRINTS["ejecuciones"]`.
3. El texto normalizado del brief contiene la marca normalizada (`clinicaalboradavision`) o el dominio de referencia.
4. En modo prospecto: la marca o el dominio indicados coinciden con cualquiera de las 10 marcas o dominios de `marcas.csv` del kit **y** los datos subidos son los del kit (regla 2), o el consultor no ha subido datos y elige generar en vivo para una marca del kit (las marcas del kit son ficticias: un estudio en vivo no tendría sentido).

`REFERENCE_FINGERPRINTS` es una constante en el código (la detección es «fija», como se pidió). El script `scripts/compute_reference_fingerprints.py` la genera a partir de los archivos del kit y la imprime para pegarla. Un test recalcula las huellas y falla si no coinciden con la constante.

### B1.3 Dónde se aplica
- Se evalúa en cada subida de brief o de CSV y en el momento de lanzar. El resultado se guarda en `state.json` → `"modo_referencia": {"activo": true, "motivo": "huella_brief", "detectado_en": "<iso>"}` y en la primera línea de `trace.jsonl` (`{"step": "reference_check", ...}`).
- **Ningún endpoint de la API devuelve este campo**, salvo el de trazas técnicas (que muestra el contenido de `trace.jsonl` tal cual). Los modelos de respuesta de la API (C5) no lo incluyen.
- Las etiquetas de origen siguen la regla 0.1: como el proveedor real del paso es `mock`, la etiqueta es «Generado automáticamente».
- Estimaciones de coste en el asistente: se calculan igual que para un proyecto real (con los modelos configurados). El coste real final es 0 € y así se muestra.
- Pasos del estudio en vivo en modo de referencia: «Proponer marcas» devuelve las 10 marcas de `marcas.csv` del kit; «Proponer banco» devuelve las 25 plantillas de `banco_prompts.csv`; «Ejecutar consultas» copia `ejecuciones.csv` del kit al proyecto. Son instantáneos: no se añade ninguna espera artificial.

### B1.4 Tests obligatorios
- Brief `.md` del kit → referencia (motivo `huella_brief`).
- Brief `.docx` del kit → referencia (motivo `huella_brief`).
- Brief del kit con una frase cambiada → referencia (motivo `marca`).
- Brief de otra marca de otro sector → no referencia.
- CSV del kit subidos con un brief distinto → referencia (motivo `huella_datos`), y los datos usados son los del kit.
- Prospecto «Vistalia Oftalmología» sin datos → referencia.
- En modo de referencia, el contador de llamadas reales a OpenRouter es 0 (monkeypatch de `requests.post` que falla si se llama).
- La respuesta JSON de `GET /api/projects/{id}` no contiene las cadenas `referencia` ni `reference`.

## B2. Estudio en vivo
Pipeline previo al análisis, solo para proyectos que no son de referencia y eligen «Generar en vivo». Su salida son los mismos CSV que el kit, en la carpeta del proyecto, de modo que el análisis posterior es el mismo para datos subidos y generados.

### B2.1 Paso «proponer marcas» (`geo/study/brands.py`)
- Entrada: `FichaMarca`.
- LLM con búsqueda web (modelo «propuesta», con `web_search=True`) que devuelve JSON validado:
  ```python
  class MarcaPropuesta(BaseModel):
      nombre: str
      nivel: Literal["foco", "contexto"]
      rol: str                 # "MARCA DEL BRIEF", "competidor declarado", "competidor detectado", "líder de mercado", "contexto"
      dominio: str             # dominio propio sin www
      alias: list[str]         # 0-4 alias reales con los que la nombran
      motivo: str              # por qué se incluye (≤ 200 caracteres)
      fuente_url: str | None   # URL que lo respalda
  class PropuestaMarcas(BaseModel):
      marcas: list[MarcaPropuesta]
  ```
- Validación por código: la marca del brief siempre presente y `foco`; los competidores declarados siempre presentes; máximo 4 `foco`; dominios normalizados con `extract_domain`; sin duplicados por nombre normalizado ni por dominio.
- Salida: `study/marcas.csv` con las columnas del kit (`Marca, Nivel, Rol, Dominio_propio, Alias`).

### B2.2 Paso «proponer banco de prompts» (`geo/study/prompt_bank.py`)
- Entrada: ficha + marcas aprobadas.
- LLM (modelo «propuesta», sin búsqueda) que devuelve plantillas para las **9 familias** de la metodología del kit (`02_Metodologia_GEO.md`, sección 4), respetando su intención:

  | Código | Familia | Intención | Instanciación habitual |
  |---|---|---|---|
  | DG | Descubrimiento genérico | Descubrimiento | generico |
  | DP | Descubrimiento por perfil | Descubrimiento | generico |
  | LO | Localización | Descubrimiento | ciudad |
  | CO | Comparación de opciones | Comparación | generico |
  | CM | Comparación de marcas | Comparación | par / marca |
  | VR | Validación reputacional | Validación | marca |
  | FU | Fuentes y citación | Validación | generico |
  | DF | Decisión final | Decisión | generico / marca |
  | PR | Precio y valor | Decisión | generico |

- Número orientativo: 20-28 plantillas, como el kit (3 DG, 4 DP, 2 LO, 3 CO, 3 CM, 3 VR, 2 FU, 3 DF, 2 PR).
- Validación por código: marcadores válidos según la instanciación (`[CIUDAD]` solo en `ciudad`, `[MARCA_A]` en `marca`, `[MARCA_A]` y `[MARCA_B]` en `par`); ningún prompt `generico` o `ciudad` nombra una marca (si lo hace, se rechaza: rompería la visibilidad espontánea); `Prompt_ID` con formato `<SECTOR3>-<FAMILIA>-<nn>`.
- **Instanciación por código** (`instantiate(bank, marcas, ficha) -> list[PromptInstanciado]`):
  - `generico`: 1 prompt; evalúa todas las marcas.
  - `ciudad`: 1 por ciudad de la ficha (máx. 3); evalúa todas.
  - `marca`: 1 por marca `foco`; evalúa esa marca.
  - `par`: pares estratégicos: marca del proyecto contra cada `foco` y el líder contra cada `foco` (como en el kit), máx. 6; evalúa las dos.
- Salida: `study/banco_prompts.csv` con las columnas del kit.

### B2.3 Paso «ejecutar consultas» (`geo/study/runner.py`)
- Para cada prompt instanciado × motor × repetición: `engines.openrouter_engine.run(motor, prompt, repeticion)` con búsqueda web.
- Paralelo con `LLM_CONCURRENCY`, progreso por eventos, caché por (modelo, repetición, prompt), tolerancia a fallos por llamada (una llamada fallida se reintenta y, si sigue fallando, se registra y se excluye; si fallan más del 20 %, el paso termina en error).
- Tope de gasto: se comprueba antes de cada llamada.
- Salida: `study/ejecuciones.csv` con las columnas exactas del kit (`Ejecucion_ID, Sector, Prompt_ID, Familia, Intención, Prompt ejecutado, Motor, Repetición, Marcas a evaluar, Respuesta completa, Fuentes citadas, Fecha/hora`) y `study/ejecuciones_meta.jsonl` con modelo, coste y tokens por fila.

### B2.4 Paso «clasificar fuentes» (`geo/study/sources.py`)
- Dominios citados en `ejecuciones.csv` que no estén en el catálogo del proyecto.
- Regla por código primero: si el dominio es el propio de alguna marca → `Web propia`.
- Resto: LLM por lotes de 30 dominios → `TipoFuente` (los 6 tipos del kit). Calidad por tipo con `SOURCE_QUALITY_BY_TYPE` (código, no LLM).
- Caché global por dominio en `data/cache/dominios.json` (un dominio se clasifica una vez para todos los proyectos).
- Salida: `study/fuentes_catalogo.csv`.

### B2.5 Coste orientativo (mostrar siempre la estimación real del catálogo)
`n_llamadas = prompts_instanciados × motores × repeticiones`. Con el banco del kit (52 instanciados), 4 motores y 2 repeticiones = 416 llamadas; con 3 repeticiones = 624. Coste por llamada = tokens × precio del modelo + búsqueda web (~0,005-0,012 $ según motor). La estimación sale de `GET /api/estimates/study`.

## B3. Puntos de control configurables
- Campo del proyecto `revision: "pausas" | "continuo"`.
- `pausas`: el backend llama a `run_all(stop_at_checkpoint=True, auto_approve=False)`. Al llegar a un punto de control, el paso queda en `awaiting_human`, el trabajo termina con estado `esperando_revision` y la web lo indica. Al aprobar (`POST /checkpoints/{n}/approve`), el backend relanza el trabajo, que retoma desde el siguiente paso.
- `continuo`: `run_all(auto_approve=True)` con nota de aprobación «Aprobación automática (modo continuo)». El consultor puede revisar y editar después.
- **Edición después de aprobar** (en ambos modos): editar la ficha, la competencia, los hallazgos o el plan marca como `pending` todos los pasos posteriores. La web muestra qué se va a recalcular y su coste, y el consultor confirma con «Recalcular». Mapa de invalidación:

  | Edito | Se recalcula |
  |---|---|
  | Ficha | mercado, hallazgos, plan, redacción, revisión, exportación (detección, juez y métricas no dependen de la ficha salvo la marca del proyecto; si cambia la marca o las ciudades, también métricas) |
  | Competencia (roles, exclusiones, marcas añadidas) | si se añaden marcas: detección, juez, métricas y todo lo posterior; si solo roles: hallazgos y posteriores |
  | Hallazgos | plan, redacción, revisión, exportación |
  | Plan | revalidación de presupuesto, redacción, revisión, exportación |
  | Discrepancia del juez resuelta | métricas y todo lo posterior |

## B4. Sectores genéricos
Ver Parte D. Resumen: nada del sector del kit en el código de producto; lo sectorial sale de la ficha, de los datos y, cuando hace falta texto (acciones del plan, reglas normativas), de un LLM con plantillas genéricas o de perfiles de sector configurables.

---

# PARTE C · Arquitectura técnica

## C1. Visión general

```
┌──────────────────────── navegador ────────────────────────┐
│  React + TS (Vite)                                         │
│  React Router · TanStack Query · cliente API generado      │
│  EventSource (SSE) para progreso                           │
└───────────────┬───────────────────────────────▲────────────┘
                │ HTTP JSON /api/*              │ SSE /api/projects/{id}/events
┌───────────────▼───────────────────────────────┴────────────┐
│  FastAPI (backend/)                                         │
│  routers: projects · inputs · study · run · checkpoints ·   │
│           results · exports · settings · estimates · traces │
│  services: ProjectStore · JobRunner · EventBus · reference  │
└───────────────┬─────────────────────────────────────────────┘
                │ llamadas Python
┌───────────────▼─────────────────────────────────────────────┐
│  geo/ (motor actual, generalizado)                          │
│  loader(project) · detection · judge · metrics · findings · │
│  market · strategy · budget · reviewer · writer · export ·  │
│  simulate · llm · openrouter · settings · study/* · reference│
└───────────────┬─────────────────────────────────────────────┘
                │
        data/projects/<id>/  ·  data/cache/  ·  .env
```

En producción local, FastAPI sirve también el frontend compilado (`frontend/dist`) en `/`, así que hay **un solo proceso y un solo puerto**. En desarrollo, Vite (5173) hace proxy de `/api` al backend (8000).

## C2. Estructura del repositorio objetivo

```
geo-copilot/
├── CLAUDE.md
├── GUIA_WEB.md                    # este documento
├── PRODUCT.md                     # contexto de producto (lo escribe /impeccable init en W0)
├── DESIGN.md                      # dirección visual y tokens (W1)
├── .mcp.json                      # MCP de proyecto: figma, playwright, lovable (H1)
├── .claude/skills/                # skills de proyecto versionadas (H1)
├── coord/reviews/                 # informes obligatorios de las puertas de calidad (H6)
├── README.md · ARQUITECTURA.md
├── Makefile                       # install, dev, build, app, test, e2e, fingerprints
├── .env.example
├── contracts/
│   ├── openapi.yaml               # CONTRATO de la API (fuente de verdad)
│   └── events.md                  # formato de los eventos SSE
├── backend/
│   ├── main.py                    # crea la app, monta routers y sirve frontend/dist
│   ├── deps.py                    # dependencias comunes (store, runner)
│   ├── api_models.py              # modelos Pydantic de petición/respuesta (≠ geo/schemas.py)
│   ├── routers/
│   │   ├── projects.py · inputs.py · study.py · run.py · checkpoints.py
│   │   ├── results.py · exports.py · settings.py · estimates.py · traces.py
│   └── services/
│       ├── store.py               # ProjectStore: CRUD de proyectos en disco
│       ├── runner.py              # JobRunner: un trabajo a la vez, hilos, reanudación
│       ├── events.py              # EventBus: pub/sub en memoria + SSE
│       └── invalidation.py        # mapa B3 de qué recalcular
├── geo/                           # motor (se conserva y generaliza)
│   ├── reference.py               # NUEVO (B1)
│   ├── study/                     # NUEVO (B2): brands.py, prompt_bank.py, runner.py, sources.py, csv_io.py
│   ├── sector_profiles/           # NUEVO (D3): salud.yaml, general.yaml
│   └── reference_data/            # copia de solo lectura de los datos y briefs del kit (B1)
├── frontend/
│   ├── lovable_import/            # cuarentena del código traído de Lovable (H5); nunca se importa desde src/
│   ├── index.html · vite.config.ts · tsconfig.json · package.json
│   └── src/
│       ├── api/                   # cliente generado desde contracts/openapi.yaml + hooks de TanStack Query
│       ├── components/            # kit compartido (W1); CONTRACT.md con sus props
│       ├── features/              # una carpeta por pantalla
│       │   ├── projects/ · wizard/ · overview/ · ficha/ · data/ · competition/
│       │   ├── diagnosis/ · findings/ · plan/ · proposal/ · quality/ · settings/
│       ├── lib/                   # formato es-ES, colores de marca, utilidades
│       ├── routes.tsx · main.tsx · App.tsx
│       └── styles/
├── scripts/
│   ├── compute_reference_fingerprints.py
│   ├── fake_openrouter.py         # se conserva y amplía
│   ├── real_smoke.py
│   └── geo_copilot.py             # lanzador: arranca backend y abre el navegador
├── tests/                         # pytest (motor + API)
│   └── api/ · reference/ · study/
├── frontend/tests/                # vitest (unitarios)
├── e2e/                           # Playwright contra backend + fake_openrouter
└── data/                          # .gitignore: projects/, cache/
```

**Se elimina:** `app/` (Streamlit), `runs_backup/`, `GEO Copilot.command` (se sustituye por el lanzador nuevo), la dependencia `streamlit` y todo lo que asume una demo en `runs/demo/` (`ensure_demo_run_ready`, botones «Cargar demo»). La carpeta `Kit Participantes Hackaton/` duplicada en la raíz queda fuera del repo; el kit vive en `kit/` como documentación y sus datos se copian a `geo/reference_data/`.

## C3. Stack del frontend
| Pieza | Elección | Motivo |
|---|---|---|
| Build | Vite + React 18 + TypeScript estricto | Rápido y estándar |
| Rutas | React Router | Rutas anidadas por proyecto |
| Datos | TanStack Query | Caché, reintentos e invalidación tras mutaciones |
| Tipos de la API | `openapi-typescript` generando `src/api/schema.d.ts` desde `contracts/openapi.yaml` + `openapi-fetch` | El contrato manda; si cambia, los tipos fallan en compilación |
| Componentes base | **shadcn/ui** (sobre Radix UI) | Accesibilidad sin imponer estética y **mismo stack que genera Lovable** (H3), para que su código se pueda importar |
| Estilos | **Tailwind CSS** con los tokens del `DESIGN.md` como variables CSS (claro/oscuro) | Compatible con Lovable y con las reglas de Impeccable y Taste Skill; la estética la decide W1 |
| Movimiento | Transiciones CSS con los tokens de easing y duración de H2.1; librería de animación solo si `review-animations` la justifica | Reglas de Emil Kowalski |
| Gráficos | Apache ECharts (`echarts` + envoltorio propio) | Mapa de calor, barras apiladas, dispersión y cronograma en una sola librería, con tema propio |
| Tablas | TanStack Table | Filtros, ordenación, edición en línea del plan |
| Formularios | React Hook Form + Zod | Validación de la ficha y del plan |
| Markdown | `react-markdown` + `remark-gfm` | Vista previa de la propuesta |
| Tipografía | Servida en local (sin Google Fonts en producción) | Funciona sin red |
| Tests | Vitest + Testing Library; Playwright para e2e | |

Versiones: fijar versiones exactas en `package.json` (sin `^`) al instalar.

## C4. Almacenamiento en disco

```
data/
├── projects/
│   └── <project_id>/                       # p_20261021_153012_ab12cd
│       ├── project.json                    # metadatos públicos del proyecto (ver C5 Project)
│       ├── inputs/
│       │   ├── brief_original.<ext>
│       │   ├── brief.txt                   # texto extraído
│       │   └── uploads/*.csv               # CSV tal y como se subieron
│       ├── study/                          # formato canónico del kit (subido normalizado o generado)
│       │   ├── marcas.csv · banco_prompts.csv · ejecuciones.csv · fuentes_catalogo.csv
│       │   ├── muestra_evaluada.csv        # opcional
│       │   ├── propuesta_marcas.json · propuesta_banco.json   # lo que propuso la IA antes de editar
│       │   └── ejecuciones_meta.jsonl      # solo estudio en vivo
│       ├── run/                            # artefactos del orquestador actual (antes runs/<id>/)
│       │   ├── state.json · trace.jsonl · progress.json
│       │   ├── ficha.json · faltantes.json · detection.parquet · evaluaciones.parquet
│       │   ├── metrics.json · tablas/*.parquet · market.json · findings.json
│       │   ├── plan.json · propuesta.json · revision.json
│       └── exports/  propuesta_cliente.docx · .md · propuesta_prospecto_<slug>.docx · .md
└── cache/
    ├── llm/       (antes cache/)
    ├── engines/
    └── dominios.json
```

- `project_id`: `p_<fecha>_<hora>_<6 hex>`.
- **Formato canónico:** dentro de `study/`, los CSV siempre tienen el formato del kit (UTF-8 con BOM, separadores ` | ` y `, `). Los CSV subidos se normalizan al copiarlos. Así `geo/loader.py` solo sabe leer un formato.
- `Run` del orquestador pasa a recibir `run_dir = data/projects/<id>/run` y `study_dir = data/projects/<id>/study`.
- `geo/reference_data/` contiene una copia de los 5 CSV y los 2 briefs del kit. Es la única ubicación de la que se leen en modo de referencia.

## C5. Contrato de la API (resumen; el detalle va en `contracts/openapi.yaml`)

Todas las rutas bajo `/api`. Errores con forma `{"error": {"code": "string", "message": "texto en español", "detail": {...}}}` y códigos HTTP coherentes (400 validación, 404 no existe, 409 conflicto de estado, 422 entrada inválida, 423 hay un trabajo en curso).

### Modelos principales
```yaml
Project:
  id: string
  nombre: string
  tipo: cliente | prospecto
  marca: string | null
  sector: string | null
  origen_datos: csv | vivo | null
  revision: pausas | continuo
  estado: borrador | listo_para_lanzar | en_ejecucion | esperando_revision | completado | error | interrumpido
  punto_control_pendiente: 0 | 1 | 2 | 3 | null
  checkpoints: {ficha: bool, competencia: bool, hallazgos: bool, plan: bool}
  coste_eur: number
  creado: datetime
  actualizado: datetime
  archivado: bool
  # NO incluye ningún campo de modo de referencia

Progress:
  estado: en_ejecucion | esperando_revision | completado | error | interrumpido
  paso_actual: string | null
  pasos: [{id, nombre, estado: pendiente|en_curso|hecho|hecho_automatico|error|esperando_revision,
           duracion_s, llamadas, coste_eur, error}]
  contador: {paso: string, hechos: int, total: int} | null
  llamadas: int
  coste_eur: number
  coste_real: bool
  transcurrido_s: number

Estimate:
  pasos: [{id, nombre, llamadas, tokens_in, tokens_out, eur}]
  total_llamadas: int
  total_eur: number
  minutos: number
  supera_tope: bool
  tope_eur: number

OriginTag: calculado | ia | automatico | editado
  # en cada bloque redactado o artefacto: {origen: OriginTag, modelo: string | null}
```

### Rutas
| Método y ruta | Qué hace |
|---|---|
| `GET /projects` | Lista (filtros `estado`, `q`, `archivados`) |
| `POST /projects` | Crea borrador `{nombre, tipo}` |
| `GET /projects/{id}` | Detalle `Project` |
| `PATCH /projects/{id}` | Renombrar, `revision`, archivar |
| `DELETE /projects/{id}` | Borrar (requiere `?confirm=<nombre>`) |
| `POST /projects/{id}/duplicate` | Duplicar entradas y configuración |
| `POST /projects/{id}/brief` | Subir archivo (`multipart`) o texto (`{texto}`); devuelve vista previa de ficha y faltantes |
| `POST /projects/{id}/prospect` | Datos de la marca prospecto `{marca, dominio, sector, ciudad, competidores[]}` |
| `POST /projects/{id}/study/upload` | Subir CSV (`multipart`, varios); devuelve informe de validación por archivo y resumen del estudio |
| `GET /projects/{id}/study/summary` | Resumen del estudio cargado o generado |
| `POST /projects/{id}/study/brands/propose` | Propuesta de marcas (trabajo corto, síncrono con timeout 90 s) |
| `PUT /projects/{id}/study/brands` | Guardar marcas editadas |
| `POST /projects/{id}/study/prompts/propose` | Propuesta de banco |
| `PUT /projects/{id}/study/prompts` | Guardar banco editado |
| `GET /projects/{id}/study/prompts/instances` | Vista previa de la instanciación |
| `PUT /projects/{id}/study/config` | `{tamano: rapido|estandar|completo, motores[], repeticiones}` |
| `GET /estimates/study?project_id=` | Estimación del estudio en vivo |
| `GET /estimates/analysis?project_id=` | Estimación del análisis |
| `POST /projects/{id}/run` | Lanzar (`{confirmo_coste: bool}`); 423 si hay otro trabajo |
| `POST /projects/{id}/run/resume` | Reanudar tras interrupción o tras aprobar |
| `POST /projects/{id}/run/retry-step` | `{paso}` reintentar un paso degradado |
| `POST /projects/{id}/run/cancel` | Cancelar (termina tras la llamada en curso) |
| `GET /projects/{id}/progress` | `Progress` |
| `GET /projects/{id}/events` | SSE (ver C6) |
| `GET /projects/{id}/ficha` · `PUT` | Ficha (`FichaMarca`) |
| `GET /projects/{id}/market` · `PUT` | Competencia (`ContrasteMercado`) |
| `GET /projects/{id}/findings` · `PATCH /findings/{hid}` | Hallazgos; aprobar/descartar/título |
| `GET /projects/{id}/plan` · `PUT` | Plan; `PUT` devuelve el plan revalidado + avisos |
| `POST /projects/{id}/plan/simulate` | Simulador `{cambios}` → resultado |
| `POST /projects/{id}/checkpoints/{n}/approve` | Aprobar punto de control `{nota}` |
| `GET /projects/{id}/invalidation?cambio=ficha|market|findings|plan` | Qué se recalcula y estimación |
| `POST /projects/{id}/recompute` | `{desde_paso}` recalcula |
| `GET /projects/{id}/diagnosis?ambito=espontanea|asistida` | Indicadores y datos de todos los gráficos ya agregados |
| `GET /projects/{id}/tables/{tid}` | Tabla T1-T12 en JSON (filas y `evidencia_ids`) |
| `GET /projects/{id}/executions` | Ejecuciones paginadas con filtros (`motor`, `familia`, `intencion`, `ambito`, `ciudad`, `ids`, `q`) |
| `GET /projects/{id}/executions/{eid}` | Detalle con evaluación por marca y fragmentos para resaltar |
| `GET /projects/{id}/proposal` | `Propuesta` + etiquetas de origen por sección |
| `POST /projects/{id}/proposal/regenerate` | Rehacer redacción y revisión |
| `GET /projects/{id}/exports/{fmt}` | Descarga `docx` o `md` |
| `GET /projects/{id}/quality` | Validación del juez, discrepancias, aprobaciones |
| `POST /projects/{id}/quality/labels` | Etiquetas humanas de la muestra |
| `PATCH /projects/{id}/quality/discrepancies/{eid}/{marca}` | Resolver discrepancia |
| `GET /projects/{id}/traces` | `trace.jsonl` como lista |
| `GET /settings` · `PUT /settings` | Ajustes (la clave nunca se devuelve: solo `clave_configurada: bool` y `clave_mascara`) |
| `POST /settings/test` | Probar conexión |
| `GET /settings/models` | Catálogo de OpenRouter (caché 1 h) |
| `GET /health` | `{"ok": true, "version": "..."}` |

### Reglas de la API
- **Ninguna ruta `GET` provoca llamadas de pago.** Solo `POST /run`, `/run/resume`, `/run/retry-step`, `/proposal/regenerate`, `/recompute`, `/study/brands/propose`, `/study/prompts/propose` y `/settings/test` pueden llamar a OpenRouter, y todas salvo `/settings/test` y las dos de propuesta exigen `confirmo_coste: true` cuando la estimación es > 0.
- Las respuestas de `diagnosis`, `tables` y `executions` llevan los datos ya agregados: el frontend no recalcula cifras.
- Todos los textos de error en español.

## C6. Eventos en tiempo real (SSE)
`GET /api/projects/{id}/events` con `text/event-stream`. Al conectar, el servidor envía primero un evento `snapshot` con el `Progress` completo. Después:

| Evento | `data` |
|---|---|
| `step` | `{paso, estado, duracion_s?, llamadas?, coste_eur?, error?}` |
| `counter` | `{paso, hechos, total}` (máx. 4 por segundo) |
| `cost` | `{llamadas, coste_eur, coste_real}` (máx. 1 por segundo) |
| `checkpoint` | `{n, nombre}` cuando se para esperando revisión |
| `done` | `{estado: completado|error|esperando_revision|interrumpido, error?}` |
| `ping` | `{}` cada 15 s |

El frontend reconecta con `EventSource` y, al reconectar, se apoya en `snapshot`. Si SSE falla, cae a sondeo de `GET /progress` cada 2 s. El `JobRunner` sigue escribiendo `run/progress.json` para sobrevivir a reinicios (lógica actual de `geo/jobs.py`).

## C7. Configuración
`.env.example` (se amplía el actual):
```ini
LLM_PROVIDER=openrouter            # openrouter | mock (mock solo para desarrollo y tests)
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=                          # juez, intake, revisor
LLM_MODEL_WRITER=                   # estrategia y redacción
LLM_MODEL_PROPOSER=                 # propuesta de marcas y banco de prompts (con búsqueda web)
ENGINE_MODEL_CHATGPT=
ENGINE_MODEL_GEMINI=
ENGINE_MODEL_CLAUDE=
ENGINE_MODEL_PERPLEXITY=
LLM_CONCURRENCY=8
MAX_LLM_CALLS=3000
MAX_BUDGET_EUR=15.0
USD_EUR=0.92
GEO_DATA_DIR=./data
GEO_HOST=127.0.0.1
GEO_PORT=8000
```
Los modelos se dejan vacíos en el ejemplo y se eligen en Ajustes desde el catálogo (los IDs cambian con frecuencia).

---

# PARTE D · Cambios en el motor `geo/`

El motor funciona y está validado contra el kit. Se cambia lo mínimo para que (1) lea de un proyecto en lugar de rutas fijas y (2) no dependa del sector del kit. **Regla de oro:** en modo de referencia la salida debe ser idéntica a la actual (test de regresión F-B2).

## D1. Valores fijos detectados en el código (comprobados en el zip actual)

| Archivo | Qué hay fijo | Cambio |
|---|---|---|
| `geo/config.py` | `KIT_DIR`, `DATA_DIR`, `BRIEF_MD`, `BRIEF_DOCX`, `MARCAS_CSV` … `MUESTRA_EVALUADA_CSV` apuntan al kit | Se mantienen solo como rutas de `reference_data/`. El resto del código recibe rutas del proyecto. |
| `geo/config.py` | `CIUDADES_CONOCIDAS` (Madrid, Barcelona, Valencia…) | La lista sale de la ficha del proyecto + ciudades detectadas en los prompts del banco. |
| `geo/config.py` | `ACTION_LIBRARY` con textos de oftalmología (cirugía refractiva, cataratas, miopía infantil, sede de Barcelona abierta en 2024, «dirección médica») y dominios del catálogo del kit | Pasa a plantillas genéricas con marcadores (`{servicios_prioritarios}`, `{ciudad_crecimiento}`, `{diferencial}`, `{dominios_medios}`…) rellenados con la ficha y el catálogo del proyecto. Los textos actuales se mueven a `sector_profiles/salud.yaml` como ejemplos. |
| `geo/config.py` | Léxico del juez por reglas (`FUERZA_3`, `FUERZA_2`, `NEGATIVO`, `DESCONOCIMIENTO`) ajustado al texto sintético del kit | Se mantiene (sirve de respaldo y de primer voto). Con datos reales el juez principal es el LLM; ver D2. |
| `geo/loader.py` | Todas las funciones leen las rutas fijas por defecto | Firma nueva `load_*(study_dir: Path)`; sin valor por defecto en el código de producto. |
| `geo/findings.py` | `default_ficha_alborada()`; `ciudad_crecimiento or "Barcelona"`, `ciudad_principal or "Madrid"`; R9 con texto «miopía infantil, refractiva, cataratas y pilotos» | Sin ficha por defecto (la ficha es obligatoria). Ciudades de la ficha; si faltan, R1 compara las dos ciudades con más n. R9 usa los servicios prioritarios de la ficha y solo se evalúa si existe la familia «Descubrimiento por perfil». |
| `geo/writer.py` | 12 referencias a la marca/kit (defaults, ficha de prospecto) | Ficha de prospecto construida con los datos que da el consultor (A4.2 paso 2). |
| `geo/strategy.py`, `geo/simulate.py`, `geo/reviewer.py`, `geo/metrics.py`, `geo/market.py`, `geo/budget.py`, `geo/export.py`, `geo/schemas.py`, `geo/orchestrator.py` | 1-3 referencias cada uno (marca del kit, líder por defecto, rutas) | Revisar una a una con `grep -n "Alborada\|Valdecruz\|Barcelona\|Madrid\|BRIEF_MD\|DATA_DIR"`; todas deben salir del proyecto. |
| `geo/orchestrator.py` | `run_all()` llama a `load_marcas()`, `load_ejecuciones()`, `load_fuentes()` sin rutas | Pasa `self.study_dir`. |
| `geo/reviewer.py` | `verify_entities` valida contra `marcas.csv`, `fuentes_catalogo.csv` y `banco_prompts.csv` del kit | Contra los del proyecto. |
| `geo/reviewer.py` | Reglas normativas sanitarias fijas | Perfiles de sector (D3). |
| `geo/schemas.py` | `Motor = Literal["ChatGPT", "Gemini", "Perplexity", "Claude"]` | Se mantiene (son los 4 motores del método). `Ejecucion.ciudad` sigue siendo opcional. **No cambiar contratos** salvo lo indicado en D4. |

## D2. Juez con datos reales
- El juez por reglas está ajustado a frases plantilla del texto sintético. Con respuestas reales acertará poco en fuerza y tipo de mención.
- En proyectos que no son de referencia: el LLM es el juez principal. El ensemble se mantiene, pero cuando reglas y LLM discrepan prevalece el LLM (ya es así) y la discrepancia va a la cola de revisión. Si el proyecto tiene `muestra_evaluada.csv` (subida o etiquetada en la web), la validación se calcula igual que hoy.
- Ajuste opcional del prompt del juez a `judge_v2.md`: ejemplos few-shot genéricos (no del kit) y la escala de fuerza de la metodología. `judge_v1.md` se queda para el modo de referencia.

## D3. Perfiles de sector (`geo/sector_profiles/*.yaml`)
Un perfil define lo que depende del sector y no puede deducirse de los datos:
```yaml
id: salud
detectar_si: ["clínica", "hospital", "médic", "sanitari", "oftalm", "dental", "fisioterap", "farmac"]
normativa:
  descripcion: "Publicidad sanitaria regulada: sin promesas de resultados ni comparativas denigratorias."
  prohibidas_regex: ["garantiza(mos)?", "resultados asegurados", "sin riesgo", "100 ?%", "la mejor clínica", ...]
responsables: [cliente_marketing, cliente_comunicacion, cliente_medico, agencia, tercero]
ejemplos_acciones: [...]       # los textos actuales de ACTION_LIBRARY como ejemplos para el LLM
```
`general.yaml` es el perfil por defecto (publicidad general: sin promesas de resultados, sin comparativa denigratoria, sin superlativos absolutos no demostrables). La ficha elige el perfil por `sector` y `restricciones_normativas`; el consultor puede cambiarlo en la Ficha.

**Nota sobre `schemas.py`:** `Responsable` es un `Literal` con `cliente_medico`. Se mantiene: en el perfil general simplemente no se usa. No se toca el contrato.

## D4. Únicos cambios de contrato permitidos en `schemas.py`
Ninguno obligatorio. Si un agente necesita uno, lo pide al líder (E4). Los modelos de la API van en `backend/api_models.py`, no en `geo/schemas.py`.

---

# PARTE E · Organización multiagente

## E1. Agentes

| Agente | Nombre | Qué construye | Ola |
|---|---|---|---|
| **L** | Líder e integrador | W0: reestructuración del repo, contratos (`openapi.yaml`, `events.md`, `CONTRACT.md` de componentes), stubs, huellas de referencia; integraciones I1-I4 | 0 y puntos de integración |
| **A** | Backend API | FastAPI: app, routers, `ProjectStore`, `JobRunner`, `EventBus` (SSE), invalidación, servir el frontend | 1 |
| **B** | Motor y modo de referencia | Generalización de `geo/` (Parte D), `geo/reference.py`, perfiles de sector, test de regresión del kit | 1 |
| **C** | Estudio en vivo | `geo/study/*` (B2), validación e importación de CSV, ampliación del servidor falso | 1 |
| **D** | Frontend base y diseño | W1: dirección visual, tokens, kit de componentes, `/_kit`; después: shell, Proyectos, Asistente, Ajustes, progreso global | 1 |
| **E** | Frontend análisis | Resumen, Ficha, Datos del estudio, Competencia, Diagnóstico, Hallazgos | 1 (lógica) y 2 (con el kit de D) |
| **F** | Frontend estrategia | Plan (con simulador), Propuesta, Calidad y trazas | 1 (lógica) y 2 |
| **Q** | Verificador independiente | e2e con Playwright y revisión de capturas, en sesión limpia | 3 |
| **H** | Documentación y lanzador | README, ARQUITECTURA, guion de demo, `scripts/geo_copilot.py`, `Makefile` | 3 |

Con 4 personas: cada una supervisa 2 agentes (lee los planes en modo plan, aprueba, vigila los archivos que tocan). Reparto sugerido: Alejandro → L; Persona 1 → A y B; Persona 2 → C y H; Persona 3 → D y Q; Persona 4 → E y F.

## E2. Matriz de propiedad de archivos
`E` = escribe en exclusiva. `L` = solo lectura. Ningún agente escribe fuera de sus `E`.

| Ruta | L | A | B | C | D | E | F | Q | H |
|---|---|---|---|---|---|---|---|---|---|
| `contracts/*`, `CLAUDE.md`, `.gitignore`, `Makefile` (W0) | E | L | L | L | L | L | L | L | L |
| `backend/**` | stub | E | L | L | L | L | L | L | L |
| `geo/reference.py`, `geo/reference_data/**`, `scripts/compute_reference_fingerprints.py` | E (W0) | L | E (tests y ajustes) | L | — | — | — | L | L |
| `geo/*.py` existentes, `geo/sector_profiles/**`, `geo/prompts/**` | — | L | E | L | — | — | — | — | L |
| `geo/study/**`, `geo/engines/**`, `scripts/fake_openrouter.py`, `tests/fixtures/fake_openrouter/**` | — | L | L | E | — | — | — | L | — |
| `geo/llm.py`, `geo/openrouter.py`, `geo/settings.py`, `geo/jobs.py` | — | E (`jobs.py` pasa a `backend/services/runner.py`) | L | L | — | — | — | — | — |
| `tests/api/**` | — | E | — | — | — | — | — | — | — |
| `tests/reference/**`, `tests/test_*.py` del motor | — | — | E | — | — | — | — | — | — |
| `tests/study/**` | — | — | — | E | — | — | — | — | — |
| `frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/routes.tsx` | stub | — | — | — | E | L | L | L | — |
| `DESIGN.md`, `frontend/src/components/**`, `src/styles/**`, `src/lib/**`, `tailwind.config.*`, `components.json` | stub | — | — | — | E | L | L | L | — |
| `PRODUCT.md`, `.mcp.json`, `.claude/skills/**`, `.claude/settings.json` | E (W0) | L | L | L | L | L | L | L | L |
| `frontend/lovable_import/D/**` y proyecto Lovable base | — | — | — | — | E | — | — | — | — |
| `frontend/lovable_import/E/**` y su remix de Lovable | — | — | — | — | — | E | — | — | — |
| `frontend/lovable_import/F/**` y su remix de Lovable | — | — | — | — | — | — | E | — | — |
| `coord/reviews/<agente>_*.md` | — | — | — | — | E (suyos) | E (suyos) | E (suyos) | E (`Q_*`) | — |
| `frontend/src/api/**` (cliente generado + hooks) | E (generación) | — | — | — | E (hooks comunes) | L | L | L | — |
| `src/features/projects/**`, `wizard/**`, `settings/**`, `src/features/progress/**` | — | — | — | — | E | — | — | L | — |
| `src/features/overview/**`, `ficha/**`, `data/**`, `competition/**`, `diagnosis/**`, `findings/**` | — | — | — | — | — | E | — | L | — |
| `src/features/plan/**`, `proposal/**`, `quality/**` | — | — | — | — | — | — | E | L | — |
| `frontend/tests/**` | — | — | — | — | E (components, projects, wizard) | E (sus features) | E (sus features) | — | — |
| `e2e/**` | — | — | — | — | — | — | — | E | — |
| `README.md`, `ARQUITECTURA.md`, `docs/**`, `scripts/geo_copilot.py`, `scripts/real_smoke.py` | — | — | — | — | — | — | — | — | E |
| Borrado de `app/` y dependencias de Streamlit | E (en I3, al final) | — | — | — | — | — | — | — | — |

Notas:
- `src/routes.tsx` es de D. E y F exportan desde su carpeta un `routes.ts` con sus rutas, y D las incluye. En W0 el líder deja `routes.tsx` ya importando `features/*/routes.ts` con stubs, así D no tiene que tocarlo por cada pantalla.
- Hooks de la API: cada feature tiene su `features/<x>/api.ts` con sus hooks de TanStack Query sobre el cliente generado. D solo escribe los comunes (`useProject`, `useProgress`, `useSettings`).
- `app/` (Streamlit) no se borra hasta I3, para tener plan B mientras tanto.

## E3. Contratos que fija W0 (líder)
1. `contracts/openapi.yaml` completo con todas las rutas y modelos de C5 (FastAPI lo generará después; en W0 se escribe a mano y es la referencia hasta que A lo sustituya por el generado, comprobando que no cambia nada).
2. `contracts/events.md` con C6.
3. `frontend/src/components/CONTRACT.md`: nombres y props de los componentes compartidos que E y F usarán, para que puedan programar antes de que D los diseñe:

   | Componente | Props mínimas |
   |---|---|
   | `PageHeader` | `title`, `description?`, `actions?`, `checkpoint?: {n, approved}` |
   | `Panel` | `title?`, `source?`, `actions?`, `children` |
   | `KpiStrip` | `items: {label, value, unit?, note?, source?, highlight?}[]`, `scope?: "espontanea"|"asistida"` |
   | `ScopeToggle` | `value`, `onChange` |
   | `Chip` | `tone: neutral|good|warn|bad|info|spont|assist|accent`, `dot?` |
   | `OriginTag` | `origen: calculado|ia|automatico|editado`, `modelo?` |
   | `SourceNote` | `tabla`, `n` (tooltip «Origen: T2 · n=60») |
   | `EvidenceLink` | `ids: string[]`, `label?` (abre Datos del estudio filtrado) |
   | `EmptyState` | `title`, `description`, `action?` |
   | `PendingState` | `step` («Disponible cuando termine el paso X») |
   | `ErrorState` | `error`, `onRetry?` |
   | `CheckpointBar` | `n`, `approved`, `onApprove`, `summary` |
   | `CostConfirm` | `estimate: Estimate`, `onConfirm`, `onCancel` |
   | `DataTable` | envoltorio de TanStack Table: `columns`, `data`, `filters?`, `onRowClick?`, `editable?` |
   | `Chart` | `option` (ECharts), `height?`, `ariaLabel`, `tableFallback?` |
   | `BrandColors` | `useBrandColors(marcaProyecto, lider)` → `(marca) => color` |
   | `ProgressPanel` | `projectId` (usa `useProgress`) |
   | `Markdown` | `source` |
   | `Drawer`, `Dialog`, `Tabs`, `Tooltip`, `Button`, `Input`, `Select`, `Textarea`, `Checkbox`, `Slider` | API estándar tipo Radix |

4. Stubs que compilan y arrancan:
   - `backend/main.py` con `/api/health` y los routers registrados devolviendo `501` con `{"error": {"code": "no_implementado"}}`.
   - Frontend Vite con rutas a todas las pantallas mostrando `EmptyState` provisional, cliente API generado desde el `openapi.yaml`, y componentes de `CONTRACT.md` como implementaciones mínimas sin estilo (para que E y F compilen).
   - **Servidor de API simulado para el frontend:** `frontend/mocks/` con MSW (Mock Service Worker) y respuestas de ejemplo en JSON para cada ruta `GET` (generadas a partir de una ejecución en mock del pipeline con el kit, ver W0 punto 6). Así D, E y F construyen pantallas con datos realistas sin esperar a A. Se activa con `VITE_MOCK_API=1`.
5. `geo/reference.py` con la detección completa y `REFERENCE_FINGERPRINTS` calculada (es corto y bloquea a B y a A).
6. Fixtures de datos para el frontend: ejecutar el pipeline actual en mock con el kit y volcar el JSON de cada `GET` de la API a `frontend/mocks/fixtures/*.json`. Ojo: estas fixtures son **solo para desarrollo** y no se sirven en producción.
7. Puertos por agente:

   | Agente | Backend | Vite | Servidor falso |
   |---|---|---|---|
   | L | 8000 | 5173 | 8760 |
   | A | 8001 | — | 8761 |
   | B | — | — | — |
   | C | — | — | 8763 |
   | D | 8004 | 5174 | 8764 |
   | E | 8005 | 5175 | 8765 |
   | F | 8006 | 5176 | 8766 |
   | Q | 8009 | 5179 | 8769 |

## E4. Reglas de coordinación
1. Contratos (`contracts/*`, `CONTRACT.md` de componentes, firmas públicas de `geo/`) solo los cambia L. Peticiones en `coord/peticiones/<agente>.md` con el cambio y el motivo. L decide, actualiza, etiqueta `contratos-vN` y avisa a los afectados para que hagan rebase.
2. Cada agente trabaja en `ag/<letra>-<nombre>`, sin merge a `main`. Commits pequeños con prefijo de fase (`WB2: ...`).
3. Antes de cada informe final: tests propios en verde y `git diff --name-only contratos-v1` solo con archivos propios.
4. Si un agente rompe algo ajeno, para y lo reporta. No arregla archivos de otros.
5. El frontend no recalcula cifras: si necesita un dato agregado, lo pide en `coord/peticiones/` para que la API lo devuelva.

## E5. Olas y calendario

T = inicio de W0. Duraciones orientativas.

```
T+0:00 ── OLA 0 ─────────────────────────────────────────────────────────────────
          L: W0 (repo, contratos, stubs back y front, MSW con fixtures, referencia)   [bloquea]
T+1:15 ── OLA 1 (6 agentes en paralelo) ─────────────────────────────────────────
          A: WA1 ProjectStore + routers de proyectos/entradas → WA2 JobRunner + SSE
             → WA3 resultados/exports/ajustes/estimaciones → WA4 invalidación
          B: WB1 loader por proyecto + Run con study_dir → WB2 regresión del kit
             → WB3 de-hardcode (D1) → WB4 perfiles de sector y juez v2
          C: WC1 import/validación CSV → WC2 propuesta de marcas y banco
             → WC3 runner del estudio en vivo → WC4 clasificador de fuentes + fake ampliado
          D: W1 con Taste Skill + Impeccable (shape) → DESIGN.md → proyecto base en Lovable
             → kit de componentes + /_kit → captura a Figma                    (≈ 2 h)
          E: WE1 lógica y datos de sus pantallas contra MSW con componentes provisionales
             (en paralelo: borrador visual de sus pantallas en su remix de Lovable cuando D lo publique)
          F: WF1 igual que E
T+3:15 ── REVISIÓN DE DISEÑO (equipo, 15 min, en Figma) ─────────────────────────
          Se revisa el archivo de Figma «GEO Copilot · Revisión» (capturado con el MCP de Figma)
          y los informes de Impeccable/Taste de D. Se aprueba o se pide un ajuste concreto.
T+3:30 ── I1 · integración del backend (L): A → B → C ───────────────────────────
          HITO: proyecto con CSV del kit desde la API (curl) hasta exports, en mock;
                proyecto con brief real contra el servidor falso, con estudio en vivo.
T+3:45 ── OLA 2 ─────────────────────────────────────────────────────────────────
          D: WD2 shell, Proyectos, Asistente (4 pasos), Ajustes, progreso global
          E: WE2 aplica el kit de D, importa su borrador de Lovable con la SEGUNDA PASADA (H5),
             cambia MSW por API real y pasa las puertas de H6
          F: WF2 igual que E
          A: soporte a frontend (ajustes de API pedidos en coord/peticiones/)
          B y C: correcciones de I1; C prueba el estudio en vivo con clave real (céntimos) en el Mac
T+6:15 ── I2 · integración del frontend (L): D → E → F ──────────────────────────
          L no integra ninguna rama de frontend sin sus informes de H6 completos
          build del frontend servido por FastAPI; recorrido manual completo
T+6:30 ── OLA 3 ─────────────────────────────────────────────────────────────────
          Q: verificación e2e en sesión limpia (≈ 1 h)
          H: documentación, lanzador, guion de demo (≈ 1 h)
          L: prueba real en el Mac: proyecto con brief real de otro sector, estudio «Rápido»
T+7:30 ── I3 · arreglos del informe de Q por los dueños; L borra app/ (Streamlit) ─
T+8:15 ── I4 · ensayo de la demo con el kit y congelación ────────────────────────
```

**Cadena crítica:** W0 → D (W1) → revisión de diseño → D/E/F (ola 2) → I2 → Q → I3. Si D se retrasa con el diseño, E y F no se paran: siguen con componentes provisionales y aplican el kit en cuanto llegue.

**Puntos de control del líder:**
- T+2:15: ¿A tiene `POST /projects` + subida de brief + `GET /progress`? Si no, D sigue con MSW.
- T+2:45: ¿B ha pasado el test de regresión del kit (WB2)? Sin eso no se integra B.
- T+3:30: si I1 no pasa en 20 min, se integra A + B (CSV) y el estudio en vivo (C) pasa a ola 2.
- T+6:15: si la UI no integra completa, se prioriza: Proyectos, Asistente con CSV, Diagnóstico, Hallazgos, Plan, Propuesta. Datos del estudio, Calidad y el estudio en vivo pueden quedar fuera de la demo.

**Orden de recorte si falta tiempo** (de lo primero que se quita a lo último): etiquetado humano de la muestra en Calidad → cola de discrepancias → simulador → estudio en vivo «Completo» (dejar solo «Rápido») → duplicar/archivar proyectos → modo oscuro. **No se recorta:** asistente con subida de CSV, modo de referencia, puntos de control, Diagnóstico, Hallazgos, Plan, Propuesta con exportación, Ajustes.

## E6. Cómo lanzar los agentes

**Con varias personas (recomendado): una terminal de Claude Code por agente, cada una en su worktree.**
```bash
cd geo-copilot                    # tras W0, en main con la etiqueta contratos-v1
for a in A-backend B-motor C-estudio D-front-base E-front-analisis F-front-estrategia; do
  git worktree add "../gc-$a" -b "ag/$a" contratos-v1
  ln -s "$PWD/.venv" "../gc-$a/.venv"
  cp .env.example "../gc-$a/.env"
done
# frontend: cada worktree necesita su node_modules
for a in D-front-base E-front-analisis F-front-estrategia; do (cd "../gc-$a/frontend" && npm ci); done
```
Las skills (`.claude/skills/`) y los MCP (`.mcp.json`) van versionados en el repo desde W0, así que cada worktree los hereda. La primera vez, cada persona aprueba los MCP del proyecto al abrir Claude Code y se autentica en Figma y Lovable (OAuth en el navegador). Comprobar con `/mcp` que aparecen `figma`, `playwright` y `lovable`, y con `/skills` (o pidiendo a Claude que liste sus skills) que están las de H1.

Cada persona: `cd ../gc-<agente> && claude`, y pega el prompt de su agente (Parte F).

**Una sola persona:** en la sesión del líder, tras W0:
```
Lanza en paralelo y en segundo plano, cada uno con isolation "worktree", los agentes A, B, C, D, E y F
con sus prompts de la Parte F de GUIA_WEB.md copiados literalmente. No escribas código tú.
Cuando cada uno termine: resume qué hizo, si sus tests pasan y comprueba con
git diff --name-only contratos-v1 que solo tocó archivos suyos según E2. Avísame para integrar.
```

## E7. Protocolo de integración (L)
Para cada rama, en el orden de E5:
```bash
git diff --name-only contratos-v1 ag/<rama>      # comparar con E2; si hay archivos ajenos, se devuelve
git merge --no-ff ag/<rama> -m "I<n>: integra <agente>"
make test                                          # pytest + vitest + typecheck del frontend
```
Si falla: `git revert -m 1 HEAD` y el error vuelve al dueño. Después: leer `coord/peticiones/`, actualizar contratos si procede, etiquetar y avisar de rebase.

---

# PARTE F · Fases con prompts

Todas las sesiones de agente empiezan con esta cabecera (se pega delante de cada prompt):

```
Eres el agente <X> del equipo descrito en GUIA_WEB.md (Partes 0, A, B, C, D y E).
Lee entero GUIA_WEB.md antes de empezar. Lee también contracts/openapi.yaml, contracts/events.md,
frontend/src/components/CONTRACT.md y coord/peticiones/.
Solo escribes en los archivos marcados con E para tu agente en la matriz E2. Todo lo demás es de solo lectura.
No cambias contratos. Si necesitas un cambio, escríbelo en coord/peticiones/<X>.md y sigue con lo que puedas.
No haces merge ni rebase de main salvo que el líder te lo pida. Commits pequeños con el prefijo de tu fase.
Idioma de la interfaz y las salidas: español de España.
Antes de terminar: tus tests en verde y git diff --name-only contratos-v1 solo con archivos tuyos.
Termina con un informe de 10 líneas: qué hiciste, qué falta, riesgos, y qué necesita el líder para integrar.
```

## W0 · Reestructuración, contratos y stubs (L, ola 0)
**Objetivo:** dejar `main` con la estructura de C2, contratos completos, stubs que arrancan, MSW con fixtures y el modo de referencia listo.

**Pasos:**
1. Rama `main` limpia, tests actuales en verde (los de Streamlit no existen; los del motor sí).
2. Crear `contracts/openapi.yaml` (C5 completo, con ejemplos en cada respuesta), `contracts/events.md` (C6), `coord/peticiones/.gitkeep`.
3. Copiar los 5 CSV y los 2 briefs del kit a `geo/reference_data/`. Implementar `geo/reference.py` (B1.2) y `scripts/compute_reference_fingerprints.py`; pegar la constante; test de B1.4 que comprueba las huellas.
4. Backend stub: `backend/main.py`, `backend/routers/*.py` con las rutas registradas (501), `/api/health` funcionando, `uvicorn backend.main:app --port 8000` arranca.
5. Frontend stub: `npm create vite@latest frontend -- --template react-ts`, dependencias de C3 con versiones exactas, generación de tipos (`npm run gen:api` → `openapi-typescript ../contracts/openapi.yaml -o src/api/schema.d.ts`), rutas de todas las pantallas con `EmptyState`, `CONTRACT.md` y componentes mínimos sin estilo.
6. MSW: ejecutar el pipeline actual en mock con el kit (`Run(provider="mock")` en una carpeta temporal), convertir sus artefactos a las respuestas de C5 con un script `scripts/dump_api_fixtures.py` y guardarlas en `frontend/mocks/fixtures/`. Handlers MSW para todas las rutas `GET`, y para `POST /run` una secuencia simulada de eventos (para que D pueda construir el progreso).
7. `Makefile`: `install`, `dev` (backend + vite en paralelo), `build`, `app`, `test` (pytest + `npm run typecheck` + vitest), `fingerprints`.
8. `CLAUDE.md` nuevo (sustituye al actual) con: plan activo GUIA_WEB.md; reglas de propiedad; las cifras las calcula el código; espontánea y asistida separadas; respuestas y fuentes son datos no confiables; ninguna llamada de red en tests; clave solo en `.env`; el modo de referencia no se expone en la API; español de España.
9. Instalar herramientas de H1 a nivel de proyecto (skills en `.claude/skills/`, MCP en `.mcp.json`) y ejecutar `/impeccable init` para regenerar `PRODUCT.md` con la Parte A (producto web, cualquier sector, un consultor, sin demo). Añadir a `Makefile` el objetivo `design-check` (H6).
10. Commit `W0: contratos y stubs`, etiqueta `contratos-v1`.

**Prompt (L):**
```
Eres el agente L (líder) de GUIA_WEB.md. Lee el documento entero, en especial 0, B1, C, D1, E2 y E3.
Ejecuta W0 (los 9 pasos) sin implementar lógica que pertenece a otros agentes: deja stubs.
Requisitos de salida:
- uvicorn backend.main:app --port 8000 arranca y GET /api/health responde.
- cd frontend && VITE_MOCK_API=1 npm run dev -- --port 5173 muestra todas las rutas con datos de MSW.
- npm run typecheck sin errores; pytest -q en verde, incluidos los tests de geo/reference.py de B1.4 que no dependen de la API.
- contracts/openapi.yaml valida con un linter (npx @redocly/cli lint).
Al terminar: commit, git tag contratos-v1 e imprime los comandos de E6 para lanzar la ola 1.
```

## WA · Backend API (A, ola 1)
**Objetivo:** implementar `contracts/openapi.yaml` sobre el motor.

**WA1 · Proyectos y entradas**
- `ProjectStore` (`backend/services/store.py`): crear, listar, leer, actualizar, archivar, duplicar, borrar; escritura atómica de `project.json` (`.tmp` + `replace`); lock por proyecto.
- Rutas `projects`, `brief`, `prospect`, `study/upload` (esta última delega en `geo.study.csv_io` de C; hasta que exista, usa el stub y devuelve 501 controlado).
- En cada subida: `geo.reference.detect_reference(...)` y guardado interno en `run/state.json` (nunca en `project.json` ni en la respuesta).
- Extracción del brief: `geo.intake.read_brief_text` (añadir soporte `.pdf` con `pypdf` si no existe, pidiéndoselo a B en `coord/peticiones/A.md` porque `intake.py` es de B).

**WA2 · Ejecución**
- `JobRunner` (`backend/services/runner.py`), basado en `geo/jobs.py`: un trabajo a la vez (423 si hay otro), hilo por trabajo, `progress.json` atómico, reanudación, cancelación cooperativa (flag que el orquestador comprueba entre pasos y el runner del estudio entre llamadas), estados de `Progress` (C5).
- Secuencia de un trabajo: (si `origen_datos == vivo` y no es referencia) estudio en vivo B2.3 → B2.4 → análisis (`Run.run_all`) con `stop_at_checkpoint` según `revision`.
- Si es referencia: `provider="mock"` forzado, datos de `geo/reference_data/`, sin estudio en vivo.
- `EventBus` en memoria con suscriptores por proyecto; SSE en `/events` con `snapshot` inicial, `ping` cada 15 s y limitación de frecuencia de C6.

**WA3 · Resultados, exportaciones, ajustes, estimaciones, trazas**
- `diagnosis` agrega en el backend todo lo que pinta la pantalla (indicadores y series de cada gráfico) a partir de `run/tablas/*.parquet` y `metrics.json`.
- `executions` paginado con filtros, fragmentos para resaltar y evaluación por marca.
- `proposal` con `OriginTag` por sección según la traza del paso (`write` y `review`): `ia` + modelo si `provider == "openrouter"` y no degradado; `automatico` en otro caso; `editado` si el consultor lo cambió.
- `settings`: nunca devolver la clave; `PUT` usa `geo.settings.save`.
- `estimates`: `Run.estimate()` / `estimate_pipeline()` y la estimación del estudio de C.
- `traces`: `trace.jsonl` tal cual.

**WA4 · Invalidación**
- `backend/services/invalidation.py` con el mapa de B3; `GET /invalidation` devuelve pasos y estimación; `POST /recompute` marca `pending` desde el paso y relanza.

**Tests (`tests/api/`, con `httpx`/`TestClient`, sin red):**
- CRUD de proyectos; duplicar; borrar con confirmación.
- Flujo completo con el brief `.md` del kit + CSV del kit: crear → brief → upload → run → esperar `completado` → `diagnosis`, `findings`, `plan`, `proposal`, `exports/docx` (abrir con python-docx).
- Mismo flujo con `revision=pausas`: se para en el punto de control 0; aprobar 0, 1, 2 y 3 lo lleva a `completado`.
- Ninguna respuesta contiene `referencia`/`reference` ni la clave.
- `GET` de cualquier ruta no llama a OpenRouter (monkeypatch que falla si se llama).
- SSE: recibe `snapshot`, eventos `step` en orden y `done`.
- 423 al lanzar dos trabajos.

**Prompt (A):**
```
[cabecera común con X = A]
Implementa el backend de C5 y C6 en backend/, fases WA1 → WA2 → WA3 → WA4, con los tests de WA.
El motor geo/ es de B y el estudio en vivo (geo/study/) es de C: llámalos por sus firmas de contrato.
Mientras B no haya integrado Run(study_dir=...), usa la firma actual con un adaptador en backend/services/runner.py y déjalo marcado con un TODO de I1.
El modo de referencia (geo/reference.py) ya existe desde W0: úsalo y no expongas nunca su resultado fuera de run/state.json y trace.jsonl.
Arranca con uvicorn en el puerto 8001 y el servidor falso de OpenRouter en el 8761 para las pruebas manuales.
```

## WB · Motor y modo de referencia (B, ola 1)
**WB1 · Lectura por proyecto**
- `geo/loader.py`: todas las funciones `load_*(study_dir: Path)`; `load_ejecuciones` obtiene la lista de ciudades de la ficha si se pasa (`ciudades: list[str] | None`) y, si no, de un detector de ciudades sobre los prompts `ciudad` del banco (comparando el prompt instanciado con la plantilla).
- `Run.__init__(..., run_dir: Path, study_dir: Path)`; `run_all()` carga con `self.study_dir`.
- `verify_entities` y `market` contra el estudio del proyecto.

**WB2 · Regresión del kit (bloqueante para integrar)**
- `tests/reference/test_regression_kit.py`: ejecutar el pipeline en mock con `study_dir = geo/reference_data` y el brief del kit, y comparar con una instantánea generada **antes** de tocar nada (`tests/reference/snapshot/`: `metrics.json`, `findings.json`, `plan.json` sin fechas, tablas T1-T12 en CSV, número de cifras trazables del revisor). Igualdad exacta (tolerancia 1e-9 en flotantes).
- La instantánea se genera en el primer commit de B, antes de cualquier cambio.

**WB3 · Quitar valores fijos (D1)**
- Revisar una a una las coincidencias de `grep -rn "Alborada\|Valdecruz\|Tramuntana\|Barcelona\|Madrid\|oftalm\|miop\|catarat\|BRIEF_MD\|DATA_DIR" geo/` y moverlas a la ficha, a los datos del proyecto o a `sector_profiles/`.
- `ACTION_LIBRARY` → plantillas genéricas con marcadores, rellenadas con la ficha y el catálogo del proyecto. La regresión del kit (WB2) debe seguir exacta: para eso, el perfil `salud` con la ficha de Alborada tiene que producir los mismos textos que hoy (si alguno no puede, se acepta el cambio de texto solo si las cifras, costes, semanas y vínculos con hallazgos son idénticos, y se documenta en el informe).
- `findings.py` sin ficha por defecto.

**WB4 · Perfiles de sector y juez v2**
- `geo/sector_profiles/salud.yaml` y `general.yaml` (D3), cargador y selección por ficha.
- `reviewer.compliance` usa las reglas del perfil.
- `geo/prompts/judge_v2.md` (D2) para proyectos que no son de referencia.
- Test con un brief de otro sector (p. ej. una academia de idiomas en Valencia, escrito en `tests/fixtures/briefs/academia_idiomas.md`) y un `ejecuciones.csv` pequeño escrito a mano (12 filas, 2 motores) que recorre el pipeline en mock sin errores y sin ninguna mención a oftalmología en la propuesta.

**Prompt (B):**
```
[cabecera común con X = B]
Tu trabajo es la Parte D y las fases WB1 → WB4.
Primer commit, antes de tocar código: genera la instantánea de WB2 con el código actual.
Después WB1, y no sigas a WB3 hasta que WB2 pase con igualdad exacta.
geo/reference.py lo creó el líder en W0: puedes ampliar sus tests, no su API.
No toques backend/, geo/study/, geo/engines/, geo/llm.py, geo/openrouter.py ni geo/settings.py.
Si intake.py necesita leer .pdf (petición de A), añádelo con pypdf.
```

## WC · Estudio en vivo (C, ola 1)
**WC1 · Importación y validación de CSV** (`geo/study/csv_io.py`)
```python
def identify(path: Path) -> Literal["ejecuciones", "marcas", "banco_prompts", "fuentes_catalogo", "muestra_evaluada"] | None
def validate(kind, path) -> ValidationReport   # filas, columnas, errores bloqueantes, avisos, ejemplos de filas con error
def normalize_into(study_dir: Path, files: dict[str, Path]) -> StudySummary
```
- Reconocimiento por columnas (tolerante a BOM, mayúsculas y tildes en las cabeceras).
- Errores bloqueantes: falta columna obligatoria, `Ejecucion_ID` duplicado, motor fuera de los 4, `Prompt_ID` de `ejecuciones` que no está en el banco, marca de `Marcas a evaluar` que no está en `marcas.csv`.
- Avisos: % de `Fuentes citadas` vacías, dominios fuera del catálogo, prompts del banco sin ejecuciones.
- `StudySummary`: ejecuciones, motores, repeticiones, prompts, marcas, espontáneas/asistidas, ciudades detectadas.

**WC2 · Propuestas** (`brands.py`, `prompt_bank.py`): B2.1 y B2.2 completos, con `complete_json` y validación por código. En modo de referencia devuelven los CSV del kit.

**WC3 · Runner del estudio** (`runner.py`): B2.3 con progreso (`on_progress`), cancelación, tope de gasto, caché y salida en formato del kit. Estimación `estimate_study(bank, marcas, ficha, config) -> Estimate`.

**WC4 · Fuentes** (`sources.py`): B2.4. **Servidor falso ampliado:** respuestas de motor con `annotations` `url_citation` y texto que menciona marcas de la propuesta, respuestas para `brands_v1` y `prompt_bank_v1`, y modos de fallo existentes.

**Tests (`tests/study/`):**
- `identify` y `validate` con los CSV del kit (0 errores) y con versiones rotas (cada error bloqueante).
- Propuesta de marcas con el servidor falso: la marca del brief y los competidores declarados siempre presentes; máximo 4 foco.
- Banco: ningún prompt espontáneo nombra marcas; marcadores correctos por instanciación; instanciación con 2 ciudades y 3 foco da el número esperado.
- Runner contra el servidor falso: 2 prompts × 2 motores × 2 repeticiones = 8 filas con el formato exacto del kit; `loader.load_ejecuciones` lo lee sin errores.
- Con `FAKE_OR_FAIL=429_once` termina bien; con `500_always` termina en error con > 20 % fallos.
- Referencia: las propuestas devuelven los CSV del kit sin llamadas de red.

**Prompt (C):**
```
[cabecera común con X = C]
Implementa B2 completo en geo/study/ (WC1 → WC4) y amplía scripts/fake_openrouter.py.
Usa geo.llm.complete_json y geo.engines.openrouter_engine (crea este último si no existe; es tuyo) y geo.openrouter.chat por sus firmas actuales; no los modifiques salvo openrouter_engine.
Los modelos de propuesta salen de settings LLM_MODEL_PROPOSER (petición a A si settings.py no tiene esa clave: escríbela en coord/peticiones/C.md y usa get() con valor por defecto mientras tanto).
Prompts nuevos en geo/prompts/brands_v1.md y prompt_bank_v1.md (pide a B que los acepte en su carpeta si hay conflicto; por defecto son tuyos).
Servidor falso en el puerto 8763.
```

Nota de propiedad: `geo/prompts/brands_v1.md` y `prompt_bank_v1.md` son de C aunque `geo/prompts/` sea de B. L lo deja anotado en E2 en W0.

## W1 y WD2 · Frontend base y diseño (D)
**W1 · Dirección visual (ola 1, ≈ 2 h).** Sigue el proceso obligatorio de H4.
1. Leer Parte A entera, en especial A4 y A6, `PRODUCT.md` y la Parte H.
2. Proponer 2 direcciones visuales distintas en `DESIGN.md` (nombre, idea, tipografía, paleta, cómo se ven espontánea/asistida, marca del proyecto y líder, densidad) y **elegir una** argumentando por qué sirve mejor a un consultor que defiende cifras ante un comité.
3. Tokens en variables CSS para claro y oscuro (color, tipografía, espaciado, radios, sombras, foco, movimiento) y escala tipográfica.
4. Implementar todos los componentes de `CONTRACT.md` con su estilo final, accesibles (teclado, foco, ARIA), con tema ECharts propio derivado de los tokens.
5. Página `/_kit` (solo en desarrollo) con todos los componentes en sus estados, en claro y oscuro, y un ejemplo de cada gráfico con datos de las fixtures.
6. Capturas con Playwright de `/_kit` en claro y oscuro a 1280 y 1024 px en `frontend/design-shots/`. Revisarlas y corregir antes del informe.

**WD2 · Pantallas base (ola 2)**
- Shell: navegación global (Proyectos, Ajustes) y navegación del proyecto (las 9 secciones de A3), indicador global de ejecución con `ProgressPanel`, estado de conexión de OpenRouter (sin llamadas de red: lee `GET /settings`).
- Proyectos (A4.1), Asistente (A4.2) con sus 4 pasos y las dos pestañas de datos, Ajustes (A4.13), `ProgressPanel` con SSE y caída a sondeo.
- Formato es-ES centralizado en `src/lib/format.ts` (`formatPct`, `formatEur`, `formatNum`, `formatDate`).

**Tests:** vitest de componentes clave (`KpiStrip`, `CostConfirm`, `ScopeToggle`, formato es-ES); Playwright del asistente contra MSW.

**Prompt (D):**
```
[cabecera común con X = D]
Antes de nada lee la Parte H: el proceso de diseño (H4), Lovable (H5) y las puertas (H6) son obligatorios.
Ola 1: W1 completo. Tienes libertad de dirección visual dentro de A6. Antes de implementar componentes, escribe DESIGN.md con las 2 direcciones y la elegida. Implementa todos los componentes de CONTRACT.md con su API exacta (E y F ya programan contra ella). Página /_kit y capturas revisadas.
Para cuando termines W1, el equipo revisará /_kit: deja en tu informe la lista de decisiones discutibles.
Ola 2 (cuando el líder te lo diga): WD2 contra la API real (backend en 8004 con el servidor falso en 8764) y, si algo falta, contra MSW.
Las pantallas de análisis y estrategia son de E y F: no las toques. Sus rutas llegan por features/*/routes.ts.
Cuando tengas el proyecto base de Lovable (H5.2), escribe su URL en coord/lovable.md para que E y F hagan su remix.
No entregues sin los informes de H6 en coord/reviews/D_*.md.
```

## WE · Frontend análisis (E)
**WE1 (ola 1, contra MSW y componentes provisionales):** hooks en `features/<x>/api.ts`, lógica, estados (vacío, cargando, error, pendiente de paso) y contenido de: Resumen (A4.4), Ficha (A4.5) con formulario completo, validación Zod y aviso de invalidación, Datos del estudio (A4.6) con tabla filtrable y cajón de detalle con resaltado, Competencia (A4.7), Diagnóstico (A4.8) con el conmutador y todos los gráficos como `option` de ECharts, Hallazgos (A4.9).

**WE2 (ola 2):** aplicar el kit de D, quitar estilos provisionales, conectar a la API real, revisar capturas.

**Reglas:** ninguna cifra se calcula en el frontend; todos los gráficos con `ariaLabel` y tabla equivalente; `EvidenceLink` en cada cifra con evidencia; colores de marca con `useBrandColors`.

**Tests:** vitest de los mapeos de datos a `option` de ECharts (que los valores pasan sin transformar) y del formulario de ficha; Playwright de Diagnóstico (cambio espontánea/asistida y apertura de evidencia) contra MSW.

**Prompt (E):**
```
[cabecera común con X = E]
Antes de nada lee la Parte H. Lovable (H5) y las puertas de calidad (H6) son obligatorios para ti.
Ola 1: WE1 contra MSW (VITE_MOCK_API=1, Vite en 5175) usando los componentes de CONTRACT.md tal como estén. No inventes estilos: si un componente provisional se ve mal, déjalo; D lo diseñará.
Ola 2 (cuando el líder te lo diga): rebase sobre main, WE2 contra la API real (backend 8005, servidor falso 8765) y capturas de tus 6 pantallas en claro y oscuro, revisadas.
Si necesitas un dato que la API no da ya agregado, pídelo en coord/peticiones/E.md; no lo calcules en el cliente.
Borrador visual: haz remix del proyecto base de Lovable (URL en coord/lovable.md) y genera tus 6 pantallas allí con datos de fixtures (H5.3). Lo que traigas pasa por la segunda pasada H5.5 antes de salir de frontend/lovable_import/E/.
No entregues sin los informes de H6 en coord/reviews/E_*.md.
```

## WF · Frontend estrategia (F)
**WF1 (ola 1):** Plan (A4.10) con tabla editable (TanStack Table), revalidación al guardar mostrando avisos del backend, matriz esfuerzo/impacto, cronograma por semanas con las 4 fases, barra de presupuesto, carga semanal del cliente, simulador con controles y resultado; Propuesta (A4.11) con índice, vista por secciones, `OriginTag`, sello del revisor, incidencias, regenerar con `CostConfirm`, descargas, pestaña de prospecto con correo y botón copiar; Calidad y trazas (A4.12) con validación, cola de discrepancias, formulario de etiquetado humano, traza y aprobaciones.

**WF2 (ola 2):** como WE2.

**Prompt (F):**
```
[cabecera común con X = F]
Antes de nada lee la Parte H. Lovable (H5) y las puertas de calidad (H6) son obligatorios para ti.
Ola 1: WF1 contra MSW (Vite en 5176). Ola 2: WF2 contra la API real (backend 8006, servidor falso 8766) y capturas revisadas de tus 3 pantallas en claro y oscuro.
OriginTag de cada sección de la propuesta: usa exactamente lo que devuelve la API; nunca pongas «IA» por defecto.
El simulador muestra siempre «Escenario hipotético, no una predicción».
Borrador visual: remix del proyecto base de Lovable (URL en coord/lovable.md) para tus 3 pantallas (H5.3). Segunda pasada H5.5 obligatoria antes de sacar nada de frontend/lovable_import/F/.
No entregues sin los informes de H6 en coord/reviews/F_*.md.
```

## WQ · Verificación (Q, ola 3, sesión limpia)
```
Eres el agente Q, verificador. No has participado en el desarrollo. Lee GUIA_WEB.md (0, A, B, C5, C6 y G) y trabaja sobre main tras I2.
No modificas código de producción. Tu salida: e2e/ con tests de Playwright y coord/informe_Q.md.
Arranca: backend en 8009 (make build && uvicorn sirviendo frontend/dist), servidor falso en 8769, GEO_DATA_DIR en una carpeta temporal.
Comprueba:
1. Primer uso: la web arranca sin proyectos y sin ningún dato de ejemplo visible; no existe ningún botón ni texto «demo».
2. Proyecto del kit: brief .docx del kit + 5 CSV del kit, modo pausas. Para en los 4 puntos de control, se aprueban, termina; Diagnóstico muestra Alborada con aparición espontánea 38,8 % y puesto 7 en espontánea; la propuesta se descarga y abre; el coste final es 0,00 €; cuenta las peticiones al servidor falso: 0.
3. Ninguna pantalla ni respuesta de la API (revisa la pestaña de red) contiene «referencia», «reference», «mock» o «demo», salvo la vista de trazas técnicas.
4. Las etiquetas de origen del proyecto del kit dicen «Generado automáticamente», nunca «Redactado por IA».
5. Proyecto real: brief de tests/fixtures/briefs/academia_idiomas.md, estudio en vivo «Rápido» contra el servidor falso, modo continuo. Propone marcas y banco, se editan, estima, lanza, termina; la propuesta no menciona oftalmología.
6. Errores: FAKE_OR_FAIL=402 durante el análisis → pasos en «hecho automático» con aviso; 429_once → termina bien.
7. Interrupción: matar el backend a mitad del juez, arrancarlo, «Reanudar» → termina sin repetir llamadas ya hechas (contador del servidor falso).
8. Ninguna GET dispara peticiones al servidor falso.
9. La clave falsa sk-or-test-123 no aparece en data/, en respuestas de la API ni en el HTML.
10. Capturas de todas las pantallas en claro y oscuro a 1280 y 1024 px con el MCP de Playwright; busca textos cortados, solapes, inglés, emojis, cifras sin origen.
11. Puertas de H6 por tu cuenta, sin fiarte de los informes de los agentes: make design-check en verde; /impeccable audit y /impeccable critique de cada pantalla; el inspector de app de Taste Skill a 3 anchos; review-animations y break-ui de Emil Kowalski. Guarda cada informe en coord/reviews/Q_*.md.
12. Busca restos de Lovable: grep de "lovable", "lovable-tagger", "supabase", "@/integrations" en frontend/src y package.json (deben ser 0) y ningún import desde frontend/lovable_import/.
13. Captura las pantallas finales al archivo de Figma «GEO Copilot · Entrega» con el MCP de Figma (generate_figma_design o, si no captura localhost, subiendo las capturas con upload_assets).
Cada fallo en el informe: pasos, captura, archivo responsable según E2 y agente dueño.
```

## WH · Documentación y lanzador (H, ola 3)
- `scripts/geo_copilot.py`: comprueba `.venv` y `frontend/dist` (si falta, `npm run build`), elige puerto libre desde 8000, arranca uvicorn, espera a `/api/health`, abre el navegador (Chrome/Edge en modo `--app` si existe), cierra limpio con Ctrl+C. `make app` lo usa.
- `README.md`: instalación (Python + Node), configuración de OpenRouter en Ajustes, crear el primer proyecto con CSV, generar un estudio en vivo, coste orientativo, solución de problemas.
- `ARQUITECTURA.md`: diagrama de C1, decisiones (React+FastAPI frente a Streamlit, SSE frente a sondeo, formato canónico del kit, perfiles de sector, juez con datos reales), cómo se evita inventar cifras, validación del juez, coste, seguridad, limitaciones. El modo de referencia se documenta en la sección técnica como «perfil de datos de referencia para reproducibilidad del caso del kit».
- `docs/demo_guion.md`: el guion de G1 de este documento.

**Prompt (H):**
```
[cabecera común con X = H]
Implementa WH. Las cifras de coste y tiempo solo pueden venir de ejecuciones reales registradas en data/projects/*/run/trace.jsonl o de la salida de scripts/real_smoke.py; si aún no hay, escribe PENDIENTE y lista qué falta.
```

---

# PARTE G · Demo, riesgos y checklist

## G1. Cómo hacer la demo con el caso del kit
Preparación (la noche anterior):
1. `make app` en el portátil de la presentación. La web arranca vacía.
2. Ajustes: clave de OpenRouter configurada (para enseñar que la herramienta está conectada) y modelos elegidos.
3. Tener a mano en el escritorio: `Brief_de_ejemplo_Clinica_Alborada.docx` y la carpeta `caso_oftalmologia` con los 5 CSV.
4. Ensayar el recorrido completo dos veces y borrar esos proyectos de ensayo (o archivarlos) para empezar la demo con la lista vacía o con un proyecto de otro sector creado de verdad.
5. Opcional, para enseñar el funcionamiento real: un proyecto de otro sector ya ejecutado con estudio en vivo «Rápido», con su coste real.

Recorrido (5 min):
1. **Nuevo proyecto** → Cliente → subir el brief `.docx` → vista previa de la ficha.
2. **Datos del estudio** → subir los 5 CSV → informe de validación (624 ejecuciones, 4 motores, 3 repeticiones).
3. **Ejecución** → modo «Parar en cada punto de control» → lanzar.
4. Punto de control 0: revisar la ficha y aprobar. Punto de control 1: la web avisa de que el brief no menciona a Vistalia y de que el líder real es Valdecruz; aprobar.
5. **Diagnóstico**: conmutador espontánea/asistida, Barcelona frente a Madrid, ChatGPT y Claude; abrir una evidencia.
6. Punto de control 2: hallazgos con evidencia; aprobar. Punto de control 3: plan dentro del presupuesto, cronograma, simulador; aprobar.
7. **Propuesta**: sello del revisor, descargar el `.docx`.
8. Si sobra tiempo: abrir el proyecto real de otro sector y enseñar el estudio en vivo y su coste.

## G2. Riesgos
| Riesgo | Mitigación |
|---|---|
| La regresión del kit cambia cifras al generalizar el motor | WB2 bloquea la integración de B hasta igualdad exacta |
| La reescritura del frontend no llega a tiempo | E y F construyen contra MSW desde la ola 1; orden de recorte de E5; `app/` (Streamlit) no se borra hasta I3 |
| El diseño se discute demasiado | Una sola revisión de 15 min en T+3:15 con decisión cerrada |
| Contratos que cambian a mitad | Solo L, con etiqueta nueva y rebase de los afectados |
| Detección de referencia con falsos negativos (el brief se exporta distinto) | Huellas de `.md` y `.docx` + respaldo por marca y dominio + huella de los CSV |
| Detección con falsos positivos (un cliente real se llama parecido) | La marca debe coincidir completa y normalizada; dominio `.example` |
| Estudio en vivo caro | Tamaños Rápido/Estándar/Completo, estimación con precios reales, tope por proyecto, confirmación obligatoria |
| Juez por reglas inútil con datos reales | LLM como juez principal fuera del modo de referencia y cola de discrepancias |
| Prompts espontáneos que nombran marcas (sesgo) | Validación por código en B2.2 |
| SSE cortado por proxies o reinicios | Reconexión con `snapshot` y caída a sondeo |
| Fugas de la clave | Nunca en respuestas; tests de A y de Q |
| Gasto inesperado al navegar | Ninguna `GET` llama a OpenRouter; test de A y comprobación de Q |
| Código de Lovable con su propio backend (Supabase), dependencias o estilo genérico | Cuarentena en `lovable_import/`, segunda pasada obligatoria (H5.5) y comprobación de restos por Q |
| Las tres skills de diseño se contradicen | Orden de precedencia de H2.4 |
| Créditos de Lovable agotados a mitad | Un proyecto base + un remix por agente, mensajes en modo plan primero, y el camino sin Lovable (H5.7) sigue disponible |
| El MCP de Figma no captura `localhost` | Alternativa con capturas de Playwright subidas con `upload_assets` (H3.1) |

## G3. Checklist final
- [ ] La web arranca vacía; no hay demo, botón de demo ni datos de ejemplo visibles.
- [ ] Proyecto con brief y CSV del kit: mismas cifras que el motor actual (aparición espontánea de Alborada 38,8 %, Barcelona 4,2 %, Madrid 54,2 %, plan 24.300 €), coste 0 €, 0 llamadas de red.
- [ ] Ninguna pantalla ni respuesta de la API delata el modo de referencia; sí queda en la traza técnica.
- [ ] Ninguna etiqueta dice «Redactado por IA» si el paso no lo hizo un LLM real.
- [ ] Proyecto de otro sector con estudio en vivo funciona contra el servidor falso y, en el Mac, contra OpenRouter real.
- [ ] Los 4 puntos de control funcionan en modo pausas y en modo continuo; editar después recalcula lo necesario con aviso de coste.
- [ ] Diagnóstico con espontánea y asistida separadas y evidencia en cada cifra.
- [ ] Plan editable con revalidación, cronograma, presupuesto y simulador.
- [ ] Propuesta con sello del revisor y descarga `.docx` y `.md`.
- [ ] Ajustes: clave, prueba de conexión, modelos con precio, límites.
- [ ] Progreso en vivo, navegación libre durante la ejecución, reanudación tras reinicio.
- [ ] `make test` en verde (pytest, typecheck, vitest) y e2e de Q en verde.
- [ ] Claro y oscuro revisados en capturas.
- [ ] `app/` de Streamlit eliminado y `streamlit` fuera de `requirements.txt`.
- [ ] README, ARQUITECTURA y guion de demo actualizados con cifras reales.
- [ ] `make design-check` en verde y todos los informes de H6 en `coord/reviews/` sin filas abiertas.
- [ ] Ningún archivo de `frontend/src` viene de Lovable sin su informe de segunda pasada (H5.5).
- [ ] Archivo de Figma «GEO Copilot · Entrega» con las pantallas finales.

---

# PARTE H · Herramientas obligatorias de diseño y verificación

Todas las herramientas de esta parte son **obligatorias**. Cada una tiene un papel concreto, un momento del flujo y una puerta de calidad que se tiene que cumplir para integrar. Si una herramienta no está disponible (sin cuenta, sin créditos, sin red), el agente lo apunta en su informe y aplica la alternativa indicada; nunca se salta la puerta en silencio.

## H1. Instalación (la hace L en W0, versionada en el repo)

Requisitos: Node 22+ (Taste Skill lo exige), Chrome o Chromium, Python 3.11+, cuenta de Figma (plan Starter o superior; escribir fuera de borradores pide asiento Full) y cuenta de Lovable con créditos.

**Skills (a nivel de proyecto, en `.claude/skills/`):**
```bash
# Emil Kowalski · diseño de interacción y animación
npx skills@latest add emilkowalski/skills
#   obligatorias: emil-design-eng, review-animations, improve-animations,
#                 animation-performance, break-ui
#   el resto del paquete puede quedarse instalado pero no se usa salvo petición

# Impeccable · sistema de diseño, auditoría y anti-patrones
npx impeccable install            # elegir Claude Code, ámbito de proyecto
#   (alternativa: /plugin marketplace add pbakaus/impeccable  y luego /plugin)

# Taste Skill · dirección de arte y control de «aspecto de IA»
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"
#   (alternativa: /plugin marketplace add Leonxlnx/taste-skill
#                 /plugin install taste-skill@taste-skill)
```
Tras instalar, comprobar que las skills quedan dentro de `.claude/skills/` del repo (no en `~/.claude`) y hacer commit. Si alguna se instala como plugin global, cada persona la instala igual en su máquina y se anota en `coord/herramientas.md`.

**MCP (a nivel de proyecto, en `.mcp.json`):**
```bash
claude mcp add --scope project --transport http figma https://mcp.figma.com/mcp
claude mcp add --scope project --transport http lovable https://mcp.lovable.dev
claude mcp add --scope project playwright -- npx @playwright/mcp@latest --isolated --headless
```
- Figma: alternativa recomendada por Figma, que añade sus skills de canvas: `claude plugin install figma@claude-plugins-official`.
- Lovable: alternativa con comandos propios: `/plugin install lovable@claude-plugins-official`.
- Playwright: `--isolated` (perfil temporal, sin estado entre sesiones) y `--headless`. Para mirar a mano, quitar `--headless` en local. Modo por defecto de instantánea de accesibilidad; `--caps=vision` solo si hace falta para gráficos de canvas (ECharts pinta en canvas: ver H3.2).

Figma y Lovable se autentican con OAuth la primera vez que se usan. Lovable no acepta claves de API.

## H2. Qué aporta cada skill y cómo se combinan

### H2.1 Emil Kowalski (`emilkowalski/skills`)
Criterio de interacción y animación. Reglas que pasan a ser **tokens del `DESIGN.md`** y reglas de revisión:

| Regla | Valor |
|---|---|
| Entrada y salida de elementos | `ease-out` = `cubic-bezier(0.23, 1, 0.32, 1)` |
| Movimiento dentro de la pantalla | `cubic-bezier(0.77, 0, 0.175, 1)` |
| Cajones laterales (detalle de ejecución, panel de progreso) | `cubic-bezier(0.32, 0.72, 0, 1)` |
| Hover y color | `ease`; progreso continuo: `linear` |
| Prohibido | `ease-in` en interfaz; animar desde `scale(0)` (empezar en `scale(0.95)` + `opacity: 0`) |
| Duraciones | pulsación 100-160 ms; tooltips 125-200 ms; menús 150-250 ms; modales y cajones 200-500 ms; interfaz en general < 300 ms; salidas más rápidas que entradas; escalonado 30-80 ms |
| Sin animación | acciones que se repiten cientos de veces (atajos, paleta de comandos, cambiar de pestaña en el diagnóstico, filtros de tablas) |
| Pulsables | `transform: scale(0.97)` en `:active` |
| Origen | popovers desde su disparador; modales desde el centro |
| Rendimiento | solo `transform` y `opacity`; transiciones CSS para lo interrumpible |
| Accesibilidad | con `prefers-reduced-motion: reduce` se quitan desplazamientos y se mantienen opacidad y color; hover solo con `@media (hover: hover) and (pointer: fine)` |

Skills que se usan y cuándo:
- `emil-design-eng`: siempre activa al escribir componentes con estados o movimiento.
- `review-animations`: puerta de H6. Salida en tabla `Antes | Después | Por qué`.
- `improve-animations`: para aplicar lo que sale de la revisión.
- `animation-performance`: en el `ProgressPanel`, el cajón de evidencias y los gráficos (lo que más se repinta).
- `break-ui`: puerta de H6. Probar cada pantalla con datos en el peor caso (ver H6).

### H2.2 Impeccable (`pbakaus/impeccable`)
Contexto de producto, sistema de diseño, crítica y auditoría técnica. Comandos (todos como `/impeccable <comando>`):

| Comando | Quién y cuándo |
|---|---|
| `init` | L en W0: escribe `PRODUCT.md` con la Parte A |
| `shape` | D en W1, antes de escribir código: plan de UX/UI de las pantallas clave |
| `extract` | D al cerrar W1: saca tokens y componentes al sistema de diseño |
| `document` | D al cerrar W1: genera o actualiza `DESIGN.md` desde el código |
| `critique` | D, E y F por pantalla; Q al final: jerarquía, claridad |
| `audit` | D, E y F por pantalla; Q al final: accesibilidad, rendimiento, adaptación |
| `harden` | E y F: errores, desbordes de texto, casos límite, i18n (formatos es-ES) |
| `onboard` | D: estados vacíos y primer uso (A4.1 sin proyectos) |
| `clarify` | E y F: textos de interfaz confusos (sobre todo avisos de coste y de puntos de control) |
| `typeset`, `layout`, `colorize`, `quieter` | cuando `critique` señale problemas de tipografía, ritmo, color o exceso |
| `polish` | último paso de cada agente antes de su informe |
| `live` | opcional para iterar en el navegador |

Prohibidos en este producto: `delight`, `overdrive` y `bolder` (una herramienta para defender cifras ante un comité no necesita efectos; si `critique` dice que algo está apagado, se resuelve con `typeset`, `layout` o `colorize`).

Detector sin LLM (61 reglas deterministas): `npx impeccable detect <carpeta|archivo|URL>`. Código de salida 0 sin hallazgos, 2 con hallazgos, 1 si no puede analizar. Se usa en la puerta H6 sobre el código y sobre cada pantalla servida.

### H2.3 Taste Skill (`Leonxlnx/taste-skill`, skill `design-taste-frontend`)
Dirección de arte y control final contra el aspecto genérico. Para aplicaciones y paneles tiene una ruta propia (desde v2.1): elige un estilo de aplicación sacado de productos reales y construye barra, datos, gráficos y tablas con esas medidas. Reglas de app: paneles tranquilos, cifras alineadas, color sobre los datos y no como decoración, navegación que se pliega en pantallas estrechas.

Uso obligatorio:
- **W1 (D):** pedir explícitamente la **ruta de aplicación** («esto es una herramienta de trabajo con tablas y gráficos, no una landing»). La skill reparte tres direcciones y elige una; D documenta en `DESIGN.md` las tres que salieron, la elegida y por qué encaja con A6. Si la skill propone fotografía o vídeo de stock, se descarta: este producto no usa imágenes decorativas.
- **Revisión:** su comprobación en navegador real a tres anchos (1024, 1280 y 1440 px) con el inspector en modo app (`inspect.mjs --app`, dentro de la carpeta de la skill) y su ciclo de «revisar capturas y arreglar los tres peores problemas», hasta tres rondas.
- Si en algún momento se usa una versión con diales (v1 o v2-experimental), fijar: `DESIGN_VARIANCE=3`, `MOTION_INTENSITY=2`, `VISUAL_DENSITY=7`. Sin diales (v2), dejarlo escrito en el prompt: varianza baja, movimiento mínimo, densidad alta.

### H2.4 Orden de precedencia cuando chocan
1. **Esta guía**: reglas de producto (A6), regla de origen 0.1, contratos y requisitos no funcionales (A5).
2. **Accesibilidad y rendimiento**: lo que marque `/impeccable audit` y las reglas de accesibilidad de Emil Kowalski.
3. **Movimiento**: Emil Kowalski. Si Taste Skill propone movimiento de scroll o efectos de «sitio premiado», se ignora.
4. **Tipografía, color, espaciado, textos de interfaz y anti-patrones**: Impeccable.
5. **Dirección de arte y composición de pantallas**: Taste Skill en ruta de aplicación.

Cualquier conflicto que no resuelva este orden se anota en `coord/peticiones/<agente>.md` y lo decide L.

## H3. MCP

### H3.1 Figma (`https://mcp.figma.com/mcp`)
Papel: **revisión visual del equipo y archivo de entrega**, no herramienta de diseño principal (el diseño se hace en código).

Herramientas que se usan:
| Herramienta | Para qué |
|---|---|
| `whoami` | Comprobar cuenta y asiento al empezar |
| `create_new_file` | Crear «GEO Copilot · Revisión» (W1) y «GEO Copilot · Entrega» (Q) |
| `generate_figma_design` | Llevar la interfaz viva (página `/_kit` y pantallas) a capas de Figma para revisarla y comentarla |
| `upload_assets` | Alternativa: subir capturas de Playwright si `generate_figma_design` no captura `localhost` |
| `get_variable_defs`, `get_design_context`, `get_screenshot` | Si el equipo ajusta algo en Figma durante la revisión (un color, un espaciado), D lo lee de vuelta desde ahí, sin copiar valores a mano |
| `create_design_system_rules` (prompt) | D lo ejecuta tras W1 para dejar reglas que alinean futuros diseños con el código |

Momentos:
- **W1 (D):** capturar `/_kit` (claro y oscuro) y 3 pantallas de muestra (Proyectos, Diagnóstico, Plan) con datos de MSW en «GEO Copilot · Revisión». La revisión de diseño de T+3:15 se hace sobre ese archivo, con comentarios. D aplica lo acordado.
- **Ola 3 (Q):** capturar todas las pantallas finales en «GEO Copilot · Entrega» (sirve también para la presentación).

Comprobar al empezar si `generate_figma_design` acepta `http://localhost`. Si no, exponer el servidor de desarrollo un momento con un túnel (`npx localtunnel --port 5174`) solo durante la captura y con datos de MSW, o usar la alternativa de `upload_assets`.

### H3.2 Playwright (`@playwright/mcp`)
Papel: **los ojos de los agentes**. Cada agente de frontend comprueba en un navegador real lo que acaba de construir antes de darlo por hecho; Q lo usa para la verificación final. Complementa, no sustituye, a los tests de Playwright de `e2e/` (que son código que se ejecuta en `make test`).

Uso obligatorio por pantalla (D, E, F, Q):
1. `browser_navigate` a la pantalla, en claro y en oscuro.
2. `browser_resize` a 1024 y 1280 px.
3. `browser_snapshot` para revisar estructura y accesibilidad (roles, nombres, orden de foco).
4. `browser_take_screenshot` y revisar la captura (las de los gráficos, porque ECharts pinta en canvas y la instantánea de accesibilidad no ve su contenido: por eso cada gráfico tiene `ariaLabel` y tabla equivalente).
5. `browser_console_messages`: 0 errores y 0 avisos de React.
6. `browser_network_requests`: ninguna petición a `openrouter.ai` ni al servidor falso al abrir la pantalla (solo `POST` explícitos la pueden disparar).
7. Recorrer con teclado (`browser_press_key` Tab/Enter/Escape) los controles principales.

Las capturas se guardan en `frontend/design-shots/<agente>/<pantalla>-<tema>-<ancho>.png` y se enlazan desde el informe.

Coste: cada navegación añade una instantánea al contexto y las sesiones largas consumen muchos tokens. Una sesión de Playwright por pantalla, y `/clear` entre pantallas si el contexto crece.

### H3.3 Lovable (`https://mcp.lovable.dev`)
Papel: **acelerar el primer borrador visual de las pantallas**. Lovable genera proyectos con TypeScript, Tailwind y shadcn/ui, el mismo stack del frontend (C3), con vista previa en vivo. No sustituye a nuestro frontend: es una mesa de bocetos cuyo código se importa a cuarentena y se reescribe en la segunda pasada.

Limitaciones a tener en cuenta:
- La vista previa de Lovable corre en su nube: **no puede llamar a nuestro backend local**. Se trabaja con los datos de las fixtures de MSW copiados como JSON estáticos.
- Por defecto, los proyectos nuevos usan el backend propio de Lovable (base de datos y autenticación). **Prohibido activarlo**: ni `enable_database`, ni autenticación, ni funciones de servidor.
- `create_project` y `send_message` consumen créditos; el resto de herramientas son gratis.
- La sincronización con GitHub crea siempre un repositorio nuevo (no se puede enlazar con el nuestro).
- Las llamadas cambian proyectos reales: ningún agente usa `deploy_project` ni hace público un proyecto.

## H4. Proceso de diseño obligatorio (W1, agente D)

1. Leer `PRODUCT.md` (escrito por `/impeccable init` en W0) y la Parte A.
2. `/impeccable shape` sobre las 4 pantallas que más pesan en la demo: Asistente, Diagnóstico, Plan y Propuesta. Guardar el resultado en `coord/reviews/D_shape.md`.
3. Taste Skill en ruta de aplicación: tres direcciones, elegir una, justificarla contra A6. Las dos direcciones que pide W1 son la elegida y la segunda mejor de esas tres.
4. Escribir `DESIGN.md`: dirección, tokens de color (claro y oscuro, con marca del proyecto, líder, espontánea y asistida), tipografía y escala, espaciado, radios, sombras, foco y **tokens de movimiento de H2.1**.
5. Crear el **proyecto base de Lovable** (H5.2) con ese `DESIGN.md`: shell, navegación y página de componentes.
6. Implementar los componentes de `CONTRACT.md` en nuestro repo (puede partir del código del proyecto base de Lovable **solo** a través de la segunda pasada H5.5).
7. `/impeccable extract` y `/impeccable document` para que `DESIGN.md` y el código coincidan.
8. `/_kit` con todos los componentes y un ejemplo de cada gráfico. Verificación con Playwright (H3.2).
9. Captura a Figma «GEO Copilot · Revisión» (H3.1).
10. Puertas de H6 sobre `/_kit` y las 3 pantallas de muestra.
11. `create_design_system_rules` de Figma y commit.

## H5. Lovable y la segunda pasada obligatoria

### H5.1 Regla
**Ningún archivo generado en Lovable entra en `frontend/src/` sin la segunda pasada completa con Impeccable, Taste Skill y las skills de Emil Kowalski, y sin su informe en `coord/reviews/`.** El código llega primero a `frontend/lovable_import/<agente>/<fecha>/`, que está fuera del árbol de compilación (excluido en `tsconfig.json` y en ESLint), y solo sale de ahí archivo a archivo cuando pasa H5.5.

### H5.2 Proyecto base (D)
- `list_workspaces` → elegir el del equipo.
- `create_project` con este mensaje inicial (rellenar las partes entre `<>`):
  ```
  Proyecto de BOCETO para una herramienta interna de consultoría GEO llamada GEO Copilot. Solo frontend.
  Stack: Vite + React + TypeScript + Tailwind + shadcn/ui. NO actives base de datos, autenticación,
  funciones de servidor ni ningún backend. Los datos vienen de archivos JSON en src/fixtures/.
  Idioma de toda la interfaz: español de España. Formato numérico es-ES (39,4 %, 24.300 €). Sin emojis.
  Dirección visual y tokens: <pegar DESIGN.md>.
  Construye: 1) el shell con navegación global (Proyectos, Ajustes) y navegación de proyecto
  (Resumen, Ficha, Datos del estudio, Competencia, Diagnóstico, Hallazgos, Plan, Propuesta, Calidad y trazas);
  2) una página /_kit con estos componentes y estas props exactas: <pegar CONTRACT.md>.
  Movimiento: <pegar tabla de H2.1>.
  ```
- `set_project_knowledge` con: la Parte A6, la regla 0.1, la tabla de H2.1 y «nunca actives base de datos ni autenticación; nunca recalcules cifras: muestra las de las fixtures».
- `get_file_upload_url` para subir las fixtures de `frontend/mocks/fixtures/` (o pedir en el mensaje que cree `src/fixtures/` con su contenido pegado).
- Primero `send_message` con `plan_mode=true`, revisar el plan, y luego el mensaje de construcción. Revisar cada cambio con `get_diff`.
- `set_project_visibility` en privado. Anotar la URL del editor en `coord/lovable.md`.

### H5.3 Remix por agente (E y F)
- `remix_project` del proyecto base (hereda dirección y componentes, y evita que dos agentes escriban a la vez en el mismo proyecto).
- Un `send_message` por pantalla, en modo plan primero, describiendo la pantalla con su apartado de A4, los datos de las fixtures que usa y los estados (vacío, cargando, error, pendiente de paso).
- Máximo 3 iteraciones por pantalla en Lovable. Lo que no salga bien en 3, se termina en código propio.

### H5.4 Traer el código
- Opción A: conectar la sincronización con GitHub del proyecto de Lovable (crea un repo nuevo privado), clonarlo fuera del nuestro y copiar solo `src/` a `frontend/lovable_import/<agente>/<fecha>/`.
- Opción B: `list_files` + `read_file` del MCP y escribir los archivos en la carpeta de cuarentena.
- Nunca se copia `package.json`, ni configuraciones, ni dependencias de Lovable sin revisarlas una a una.

### H5.5 Segunda pasada (obligatoria, en este orden, por archivo o pantalla)
1. **Limpieza estructural (sin skills todavía):**
   - Quitar todo lo de Lovable: `lovable-tagger`, imports de `@/integrations/*`, clientes de Supabase, autenticación, telemetría.
   - Sustituir los JSON de `src/fixtures` por los hooks de `features/<x>/api.ts` sobre el cliente generado.
   - Sustituir componentes ad hoc por los de `CONTRACT.md` con su API exacta.
   - Quitar cálculos de cifras en el cliente (regla de C5): todo dato agregado sale de la API.
   - Textos en español de España; formatos con `src/lib/format.ts`.
2. **Impeccable:** `npx impeccable detect` sobre los archivos traídos (exit 0) → `/impeccable critique` → `/impeccable audit` → `/impeccable harden` → los comandos que pida la crítica (`typeset`, `layout`, `colorize`, `quieter`, `clarify`) → `/impeccable polish`.
3. **Taste Skill (ruta de aplicación):** revisión en navegador a 1024, 1280 y 1440 px con el inspector de app; arreglar los tres peores problemas; repetir hasta 3 rondas o hasta que pase.
4. **Emil Kowalski:** `review-animations` (tabla Antes | Después | Por qué) → `improve-animations` → `animation-performance` en lo que se repinta → `break-ui` con los datos del peor caso de H6.
5. **Playwright MCP:** verificación de H3.2 completa.
6. **Informe** `coord/reviews/<agente>_lovable_<pantalla>.md` con: archivos traídos, qué se quitó, hallazgos de cada skill y cómo se resolvieron, capturas antes y después.
7. Solo entonces se mueve el archivo a `frontend/src/features/<x>/` y se borra de la cuarentena.

### H5.6 Qué no se hace nunca con Lovable
`deploy_project`, `enable_database`, `query_database`, conectores (`add_connector`), proyectos públicos, subir la clave de OpenRouter o cualquier dato que no sea de las fixtures del kit.

### H5.7 Si Lovable no está disponible
Sin cuenta o sin créditos, el agente construye directamente en código y aplica igualmente los pasos 2 a 6 de H5.5 sobre su propio código (son las puertas de H6). Lo anota en su informe.

## H6. Puertas de calidad (definición de hecho del frontend)

Ningún agente de frontend (D, E, F) entrega, y L no integra su rama, sin estos informes en `coord/reviews/`:

| Puerta | Cómo | Criterio | Informe |
|---|---|---|---|
| Detector de anti-patrones | `make design-check` = `npx impeccable detect frontend/src --json` + `npx impeccable detect http://localhost:<puerto>/<ruta>` por pantalla | Código de salida 0. Excepciones solo justificadas en `coord/reviews/<agente>_excepciones_impeccable.md` y aprobadas por L | `<agente>_impeccable_detect.json` |
| Crítica y auditoría | `/impeccable critique` y `/impeccable audit` por pantalla | Sin problemas de prioridad alta abiertos | `<agente>_impeccable.md` |
| Dirección y acabado | Taste Skill, inspector de app a 1024/1280/1440 | Pasa; máximo 3 rondas de «tres peores problemas» | `<agente>_taste.md` con capturas |
| Movimiento | `review-animations` | Tabla `Antes | Después | Por qué` con todas las filas resueltas; todas las duraciones y curvas salen de tokens | `<agente>_animaciones.md` |
| Peor caso | `break-ui` con: marca de 60 caracteres, 12 marcas, 0 resultados, 3.000 ejecuciones en la tabla, plan de 25 acciones, ficha con todos los campos vacíos, errores 4xx/5xx de la API, SSE cortado | Nada se rompe ni se desborda; estados de error y vacío correctos | `<agente>_break_ui.md` |
| Navegador real | Playwright MCP, H3.2 completo | 0 errores de consola, 0 peticiones de pago en `GET`, teclado operativo, claro y oscuro correctos | `<agente>_playwright.md` + capturas |
| Lovable | H5.5 | Informe por cada pantalla traída | `<agente>_lovable_<pantalla>.md` |

`Makefile`:
```make
design-check:
	npx impeccable detect frontend/src --json > coord/reviews/detect_src.json
	# por cada ruta en frontend/design-routes.txt, con el servidor de desarrollo levantado:
	while read r; do npx impeccable detect "http://localhost:$${PORT:-5173}$$r" || exit $$?; done < frontend/design-routes.txt
```
(`frontend/design-routes.txt` lo mantiene D con la lista de rutas a revisar.)

## H7. Resumen: quién usa qué y cuándo

| Agente | Ola | Emil Kowalski | Impeccable | Taste Skill | Figma MCP | Playwright MCP | Lovable MCP |
|---|---|---|---|---|---|---|---|
| L | 0 | instala | instala, `init` | instala | configura | configura | configura |
| D | 1 | tokens de movimiento; puertas | `shape`, `extract`, `document`, `onboard`, puertas | ruta de app, 3 direcciones; puertas | `whoami`, captura a «Revisión», `create_design_system_rules` | verificación de `/_kit` y pantallas | proyecto base (H5.2) + segunda pasada |
| D | 2 | puertas | puertas | puertas | lectura de ajustes acordados | verificación | — |
| E | 1-2 | puertas | `harden`, `clarify`, puertas | puertas | — | verificación | remix (H5.3) + segunda pasada |
| F | 1-2 | puertas (`animation-performance` en simulador y cronograma) | `harden`, `clarify`, puertas | puertas | — | verificación | remix (H5.3) + segunda pasada |
| Q | 3 | revisión independiente | revisión independiente | revisión independiente | captura a «Entrega» | verificación completa | comprobación de restos |
| A, B, C, H | — | — | — | — | — | A: prueba SSE y descargas en navegador | — |

## H8. Fuentes consultadas
- Emil Kowalski, skills: https://github.com/emilkowalski/skills (skill principal `emil-design-eng`: https://raw.githubusercontent.com/emilkowalski/skills/main/skills/emil-design-eng/SKILL.md)
- Impeccable: https://github.com/pbakaus/impeccable
- Taste Skill: https://github.com/leonxlnx/taste-skill
- Figma MCP: https://help.figma.com/hc/en-us/articles/32132100833559 · https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/ · https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/
- Playwright MCP: https://github.com/microsoft/playwright-mcp · https://www.morphllm.com/playwright-mcp
- Lovable MCP: https://docs.lovable.dev/integrations/lovable-mcp-server · https://docs.lovable.dev/integrations/github

Los comandos de instalación y nombres de herramientas se comprobaron en esas páginas en octubre de 2026. Si alguno ha cambiado, manda la documentación oficial y el agente L actualiza esta parte.
