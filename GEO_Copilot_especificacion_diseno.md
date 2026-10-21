# GEO Copilot · Especificación de diseño UX/UI

Versión 1.0 · 20 de octubre de 2026 · Hackathon UFV × reload. (20-22 oct. 2026)
Documento de diseño. No contiene código: todos los valores (colores, medidas, tipografías, tiempos) se expresan como datos.

---

## Índice

0. [Cómo leer este documento](#0-cómo-leer-este-documento)
1. [Concepto](#1-concepto)
2. [Arquitectura de información](#2-arquitectura-de-información)
   - 2.1 Mapa de pantallas y navegación
   - 2.2 Flujo del análisis y puntos de control
   - 2.3 Volver atrás e invalidación
   - 2.4 Representación del progreso
3. [Sistema de diseño](#3-sistema-de-diseño)
   - 3.1 Color
   - 3.2 Tipografía
   - 3.3 Espaciado, rejilla y layout
   - 3.4 Radios, bordes, sombras y elevación
   - 3.5 Iconografía
   - 3.6 Movimiento
   - 3.7 Formato de números, fechas y unidades
4. [Componentes](#4-componentes)
   - 4.A Componentes base
   - 4.B Componentes propios
5. [Visualizaciones de datos](#5-visualizaciones-de-datos)
6. [Pantallas](#6-pantallas)
   - Pantalla 3 · Diagnóstico
   - Pantalla 4 · Hallazgos (CP2)
   - Pantalla 5 · Plan (CP3)
   - Pantalla 0 · Inicio
   - Pantalla 1 · Brief → Ficha (CP0)
   - Pantalla 2 · Competencia (CP1)
   - Pantalla 6 · Propuesta
   - Pantalla 7 · Calidad y trazas
   - Pantalla 8 · Vista de solo lectura para el cliente
7. [Microcopy](#7-microcopy)
8. [Accesibilidad](#8-accesibilidad)
9. [Guion de la demo en la interfaz](#9-guion-de-la-demo-en-la-interfaz)
10. [Priorización para implementar](#10-priorización-para-implementar)
11. [Verificación](#11-verificación)
- [Anexo A · Datos pendientes que debe aportar el backend](#anexo-a--datos-pendientes-que-debe-aportar-el-backend)

---

## 0. Cómo leer este documento

**Fuentes de datos usadas.** Todas las cifras, marcas, dominios y ciudades proceden de: `ficha.json`, `market.json`, `metrics.json`, `findings.json`, `plan.json`, `revision.json`, `propuesta_cliente.md`, `schemas.py` y la tabla de la sección 3.6 del encargo. Cuando un dato no existe en esos archivos aparece como **[dato pendiente]** y está recogido en el Anexo A.

**Convenciones.**

| Convención | Significado |
|---|---|
| `token.nombre` | Token de diseño definido en la sección 3 |
| px | Píxeles CSS a escala 1 (1440×900 salvo que se indique otra resolución) |
| **[Imprescindible]** / **[Deseable]** / **[Recortable]** | Prioridad de implementación (sección 10) |
| «Texto» | Texto exacto de interfaz. Se copia literal |
| [dato pendiente] | Hueco que rellena el backend. No inventar |
| CP0…CP3 | Puntos de control humano: Ficha, Competencia, Hallazgos, Plan |
| T1…T12 | Tablas de diagnóstico del backend |
| EJ-0000 | Identificador de ejecución (respuesta de un chatbot) |

**Supuestos de implementación.** Librería de componentes estándar (por ejemplo, Radix o shadcn/ui, o MUI) y librería de gráficos estándar (por ejemplo, Recharts o Apache ECharts). Nada de este documento exige gráficos a medida: todos los tipos elegidos existen de serie en esas librerías o se montan con barras y puntos.

---

## 1. Concepto

### Dirección visual: «Cuaderno de auditoría»

GEO Copilot se presenta como el cuaderno de trabajo de un auditor, sin la estética de producto de IA. Fondo de papel cálido, tinta casi negra, tipografía de oficina técnica y un único principio cromático: **el color siempre significa algo**. Si un elemento no transmite un significado reservado (tu marca, el líder, espontánea, asistida, fortaleza, problema, origen del dato, estado del sistema), se pinta con tinta o gris. Eso hace que la marca del brief, en bermellón, se encuentre en cualquier gráfico en menos de un segundo.

El símbolo del producto es una **marca de registro de imprenta** (círculo con cruz centrada), la señal que usan los impresores para comprobar que cada capa está alineada. Es la metáfora del producto: cada cifra está alineada con su origen. El mismo símbolo, en pequeño, marca la marca del brief en tablas y gráficos.

### Principios de diseño

| Principio | Cómo se traduce en la interfaz |
|---|---|
| **Cada cifra tiene dirección** | Toda cifra lleva debajo su origen en tipografía mono («T1 · n = 240») y es clicable: abre el visor de evidencias con las ejecuciones que la forman. Nunca más de 2 clics hasta la respuesta original. |
| **Tres tintas de autoría** | Lo calculado por código va en grafito con borde sólido y símbolo Σ. Lo redactado por IA va en sepia con borde discontinuo y símbolo de pluma. Lo aprobado por una persona va en cobalto con doble línea y símbolo de persona con check. Las tres se reconocen sin leer. |
| **El modo manda** | Espontánea (petróleo) y asistida (violeta apagado) tiñen la franja superior del Diagnóstico, el conmutador y la etiqueta de cada gráfico. No existe ninguna vista que las mezcle sin etiqueta. |
| **La persona decide, rápido** | Cada punto de control es una barra fija inferior con un botón principal y un atajo. Aprobar cuesta 1 clic y deja registro de quién y cuándo. |
| **Honestidad visible** | Aviso de datos sintéticos fijo en todas las pantallas. Muestras pequeñas rayadas. Limitaciones del juez a la vista. Pasos degradados señalados sin alarma. |
| **Fortaleza y problema no se parecen** | Los hallazgos de fortaleza tienen franja verde y flecha ascendente. Los problemas tienen franja granate y flecha descendente. Además, el texto lo dice: «Fortaleza» o «Problema». |

### Referencias de estilo (descritas con palabras)

- **Informes anuales de auditoría y memorias de calidad hospitalaria**: tablas limpias, cifras grandes con nota al pie, papel blanco roto. Encaja con un comité de dirección médico y de negocio que desconfía del marketing llamativo.
- **Gráficos de prensa económica de calidad**: etiquetas directas en lugar de leyendas, un color de énfasis y el resto en gris, títulos que afirman lo que muestra el gráfico. Encaja con el jurado, que tiene que entender en 10 segundos dónde está la marca.
- **Cuadernos de laboratorio y hojas de control de calidad**: identificadores en tipografía mono, sellos de revisión, firmas con fecha. Encaja con la promesa de trazabilidad y con el humano en el bucle.

Por qué funciona aquí: el consultor necesita densidad sin ruido, el director necesita ver el ahorro, el cliente necesita leer un documento serio y el jurado necesita confiar en las cifras. Una estética sobria y documental refuerza la confianza. Los degradados, brillos y destellos la restarían.

---

## 2. Arquitectura de información

### 2.1 Mapa de pantallas y navegación

```text
GEO Copilot
│
├── 0 · Inicio (lista de análisis, nuevo análisis, «Cargar demo»)
│
└── Análisis {run_id}  ───────────────────────────────── carril «Recorrido» a la izquierda
    ├── 1 · Ficha ................ CP0 · Confirmar ficha
    ├── 2 · Competencia .......... CP1 · Aprobar competencia
    ├── 3 · Diagnóstico ........... (sin CP; se desbloquea tras CP1)
    ├── 4 · Hallazgos ............. CP2 · Aprobar hallazgos
    ├── 5 · Plan .................. CP3 · Aprobar plan
    ├── 6 · Propuesta ............. (se desbloquea tras CP3)
    │      ├── Modo cliente
    │      └── Modo prospecto
    └── 7 · Calidad y trazas ...... (siempre accesible dentro del análisis)

8 · Vista de solo lectura para el cliente (enlace independiente, sin carril ni edición)

Capa global (toda pantalla): aviso de datos sintéticos · barra superior · visor de evidencias (panel lateral)
```

**Navegación.**

| Elemento | Ubicación | Comportamiento |
|---|---|---|
| Logotipo «GEO Copilot» | Barra superior, izquierda | Lleva a Inicio |
| Carril «Recorrido» | Columna izquierda fija, 248 px | Lista los pasos 1-7 con su estado. Clic en un paso navega a él si está desbloqueado |
| Migas | Ninguna. El carril cumple esa función | |
| Botones de avance | Barra de punto de control (inferior) | «Aprobar…» aprueba y avanza al siguiente paso |
| Atajos | Alt + 1…7 | Saltan al paso correspondiente si está desbloqueado |
| Visor de evidencias | Panel lateral derecho, se abre sobre cualquier pantalla | No cambia la ruta principal; añade un parámetro de vista para poder compartir el enlace |

**Desbloqueo de pasos.** Un paso está desbloqueado si todos los puntos de control anteriores están aprobados. La pantalla 7 está siempre disponible. La pantalla 3 se desbloquea con CP1. La pantalla 6 se desbloquea con CP3. Un paso bloqueado se ve en el carril con candado y tooltip «Se desbloquea al aprobar {nombre del CP}».

### 2.2 Flujo completo del análisis con los 4 puntos de control

```text
[Inicio]
   │  Subir brief (.md .docx .txt o pegar)  ─o─  Elegir marca (modo prospecto)  ─o─  «Cargar demo»
   │  Elegir proveedor LLM (mock · anthropic · openai) y ver coste estimado
   ▼
[Extracción del brief] (en curso, segundos en mock)
   ▼
[1 Ficha] ── CP0 «Confirmar ficha» ──► registra persona + fecha
   ▼
[Contraste de mercado] (en curso)
   ▼
[2 Competencia] ── CP1 «Aprobar competencia» ──► registra persona + fecha
   ▼
[Evaluación de 624 respuestas · 12 tablas · métricas] (en curso)
   ▼
[3 Diagnóstico] (lectura y exploración; botón «Continuar a hallazgos»)
   ▼
[4 Hallazgos] ── CP2 «Aprobar hallazgos» ──► registra persona + fecha
   ▼
[Plan de acción] (en curso)
   ▼
[5 Plan] ── CP3 «Aprobar plan» ──► registra persona + fecha
   ▼
[Revisión automática + redacción] (en curso)
   ▼
[6 Propuesta] ── descargas .docx / .md · enlace de solo lectura
```

**En modo prospecto** el flujo se acorta: no hay brief ni CP0. Se elige una marca de la lista de 10 marcas, se ejecuta el contraste y el diagnóstico de esa marca, y CP1 y CP2 se mantienen; CP3 no existe porque no hay plan completo (la propuesta de prospecto incluye 3 acciones). El carril muestra solo los pasos aplicables y los demás atenuados con el texto «No aplica en modo prospecto».

**Estados de cada paso** (derivados de `state.json` y `trace.jsonl`):

| Estado | Origen | Icono | Color | Texto en carril |
|---|---|---|---|---|
| Pendiente | `pending` | círculo discontinuo | `color.text.tertiary` | «Pendiente» |
| En curso | `pending` con ejecución activa | anillo giratorio | `color.text.primary` | «Calculando…» |
| Esperando aprobación | `awaiting_human` | persona con reloj | `color.warning.fg` | «Te toca revisar» |
| Aprobado | `done` + aprobación registrada | persona con check | `color.human.fg` | «Aprobado · {iniciales} · {hh:mm}» |
| Hecho (sin CP) | `done` | check | `color.success.fg` | «Listo» |
| Degradado | `done` + `degradado: true` en traza | ruta bifurcada | `color.degraded.fg` | «Listo con reglas» |
| Error | `error` | octógono con X | `color.error.fg` | «Error · Reintentar» |
| Desactualizado | aprobación previa invalidada | flecha circular | `color.warning.fg` | «Desactualizado» |
| Bloqueado | CP previo sin aprobar | candado | `color.text.disabled` | «Bloqueado» |

### 2.3 Volver atrás e invalidación

Regla única: **cambiar algo aprobado invalida lo que depende de ello**.

| Si el usuario edita… | Pasos que pasan a «Desactualizado» | Qué se conserva |
|---|---|---|
| La ficha (tras CP0) | Competencia, Diagnóstico, Hallazgos, Plan, Propuesta | Evaluaciones ya calculadas si no cambian marcas ni ciudades |
| La competencia (tras CP1): rol o exclusión | Diagnóstico (solo vistas de roles), Hallazgos, Plan, Propuesta | Evaluaciones de las 624 ejecuciones |
| Los hallazgos (tras CP2): aprobar/descartar | Plan, Propuesta | Diagnóstico |
| El plan (tras CP3) | Propuesta | Todo lo anterior |

Comportamiento:

1. El usuario abre un paso ya aprobado. Ve el contenido en modo lectura con un aviso en la cabecera: «Aprobado por {nombre} el {fecha} a las {hora}. Si editas, tendrás que volver a aprobar este paso y los siguientes.» y el botón secundario «Editar».
2. Al pulsar «Editar» se abre un diálogo de confirmación (componente Modal, variante «aviso»):
   - Título: «¿Editar un paso aprobado?»
   - Cuerpo: «Se reabrirá {nombre del paso}. Estos pasos quedarán desactualizados y habrá que recalcularlos y aprobarlos de nuevo: {lista}.»
   - Botones: «Cancelar» (secundario) · «Editar y reabrir» (principal).
3. Tras confirmar, los pasos dependientes muestran el estado «Desactualizado» en el carril y una franja ámbar en su cabecera: «Este paso usa datos anteriores a tu último cambio. Recalcula para actualizarlo.» con el botón «Recalcular».
4. Volver atrás **sin editar** no invalida nada.
5. El registro de aprobaciones (pantalla 7) conserva las aprobaciones anteriores tachadas con la marca «Sustituida el {fecha}».

### 2.4 Representación del progreso y de lo pendiente

Tres niveles, siempre visibles:

1. **Carril «Recorrido»** (izquierda, 248 px). Lista vertical de pasos con estado (tabla 2.2). Encima, un resumen: «Puntos de control · 2 de 4 aprobados» con 4 segmentos (uno por CP) en una barra de 4 px de alto. Segmento aprobado: `color.human.fill`; pendiente: `color.border.default`; esperando: `color.warning.fill` con patrón de rayas.
2. **Barra superior**: chip de estado global del análisis. Variantes: «Calculando · paso 3 de 8», «Te toca revisar · CP1 Competencia», «Análisis completo», «Error en un paso».
3. **Barra de punto de control** (inferior, en pantallas con CP): indica qué CP es, qué falta y quién aprobó.

---

## 3. Sistema de diseño

### 3.1 Color

#### 3.1.1 Neutros y superficie · Tema claro (obligatorio)

| Token | Hex | Uso |
|---|---|---|
| `color.bg.canvas` | #F6F5F1 | Fondo de la aplicación (papel) |
| `color.bg.surface` | #FFFFFF | Tarjetas, tablas, paneles, modales |
| `color.bg.sunken` | #EEECE6 | Zonas hundidas: pista de barras, cabecera de tabla, código de origen |
| `color.bg.inverse` | #1A1D23 | Botón principal, tooltips |
| `color.border.subtle` | #E2DFD7 | Separadores internos de tabla |
| `color.border.default` | #CFCBC1 | Bordes de tarjeta (decorativos, no informativos) |
| `color.border.strong` | #858177 | Bordes de campos de formulario y controles (informativos) |
| `color.text.primary` | #1A1D23 | Texto principal, cifras |
| `color.text.secondary` | #474D57 | Texto de apoyo, etiquetas de eje |
| `color.text.tertiary` | #646A75 | Metadatos, origen de cifras, marcas de tiempo |
| `color.text.disabled` | #9A9EA6 | Texto deshabilitado (exento de contraste) |
| `color.text.inverse` | #FFFFFF | Texto sobre `color.bg.inverse` |
| `color.focus.ring` | #1A1D23 | Anillo de foco (2 px) con separación de 2 px en `color.bg.surface` |

#### 3.1.2 Colores semánticos reservados · Tema claro

Cada significado tiene cuatro tokens: `fg` (texto e iconos), `fill` (relleno de gráfico o marca sólida), `bg` (fondo tintado) y `border`.

| Significado | Token raíz | fg | fill | bg | border | Uso exclusivo |
|---|---|---|---|---|---|---|
| Marca del brief | `color.brand` | #B23A0B | #D9480F | #FDEDE4 | #B23A0B | Barras, puntos, filas y etiquetas de Clínica Alborada Visión (o la marca del brief del análisis). Siempre con el símbolo de registro |
| Líder | `color.leader` | #1F232B | #22262E | #ECEDEF | #1F232B | Grupo Hospitalario Valdecruz (o el líder detectado). Siempre con la etiqueta «Líder» |
| Resto de marcas | `color.rest` | #5B6270 | #7F8794 | #F1F2F4 | #CFCBC1 | Cualquier otra marca |
| Espontánea | `color.spont` | #0A6670 | #0A6670 | #E3F2F3 | #0A6670 | Conmutador, franja de modo, etiquetas de ámbito espontáneo |
| Asistida | `color.assist` | #5B4790 | #5B4790 | #EEEAF7 | #5B4790 | Conmutador, franja de modo, etiquetas de ámbito asistido |
| Fortaleza | `color.strength` | #1B6E35 | #1B6E35 | #E5F3E9 | #1B6E35 | Tarjetas de hallazgo de fortaleza, hipótesis refutada favorable |
| Problema | `color.problem` | #9E1C3B | #9E1C3B | #FBE8EC | #9E1C3B | Tarjetas de hallazgo de problema |
| Calculado por código | `color.code` | #3A3F47 | #3A3F47 | #ECEDEF | #3A3F47 (sólido) | Marca de origen Σ, tablas generadas |
| Redactado por IA | `color.ai` | #8A5524 | #8A5524 | #FAF0E4 | #8A5524 (discontinuo) | Marca de origen pluma, bloques de texto redactado |
| Aprobado por humano | `color.human` | #1E4C9A | #1E4C9A | #E6EEFB | #1E4C9A (doble) | Marca de origen persona, sellos de aprobación |
| Degradado | `color.degraded` | #4F5D70 | #4F5D70 | #EDF0F4 | #4F5D70 (discontinuo) | Paso que usó reglas o mock |
| Error | `color.error` | #B42318 | #B42318 | #FDECEA | #B42318 | Fallos con reintento, incidencias bloqueantes |
| Aviso | `color.warning` | #835400 | #C98A00 | #FFF3D6 | #C98A00 | Avisos, desactualizado, n bajo, cambios sin guardar, aviso de datos sintéticos |
| Éxito | `color.success` | #1B6E35 | #1B6E35 | #E5F3E9 | #1B6E35 | Confirmaciones del sistema, sello del revisor sin incidencias |

Notas de uso:

- Fortaleza y éxito comparten verde porque ambos son positivos y nunca aparecen en el mismo componente: fortaleza es contenido del análisis; éxito es respuesta del sistema.
- Problema (granate) y error (rojo) se diferencian además por icono (flecha descendente frente a octógono) y por ubicación (tarjeta de hallazgo frente a mensaje de sistema).
- Ningún color reservado se usa como decoración. Los botones principales son de tinta (`color.bg.inverse`).

#### 3.1.3 Escalas para gráficos

**Escala secuencial «Calidad de fuente»** (7 pasos, de más a menos calidad; también sirve para el mapa de calor):

| Paso | Token | Claro | Texto encima (claro) | Oscuro | Texto encima (oscuro) | Tipo de fuente asociado |
|---|---|---|---|---|---|---|
| 1 | `color.seq.1` | #0F3B45 | blanco (12,13:1) | #E6EFF0 | #121418 (15,78:1) | Ranking / institución (calidad 1,00) |
| 2 | `color.seq.2` | #1F5C68 | blanco (7,53:1) | #B9D5DA | #121418 (11,93:1) | Medio (0,90) |
| 3 | `color.seq.3` | #3F7F8A | blanco (4,55:1) | #86B6BE | #121418 (8,30:1) | Web propia (0,70) |
| 4 | `color.seq.4` | #6FA3AC | #1A1D23 (6,04:1) | #5A949E | #121418 (5,41:1) | Directorio / comparador (0,60) |
| 5 | `color.seq.5` | #9DC2C8 | #1A1D23 (8,83:1) | #36707A | #ECEDEF (4,77:1) | Plataforma de reseñas (0,60) |
| 6 | `color.seq.6` | #C8DDE0 | #1A1D23 (11,96:1) | #285A64 | #ECEDEF (6,55:1) | Red social / foro (0,40) |
| 7 | `color.seq.7` | #E6EFF0 + rayado 45° de `color.rest.fill` | #1A1D23 (14,45:1) | #1C424A + rayado | #ECEDEF (9,30:1) | Sin fuente (0,20) |

Las calidades por tipo de fuente proceden de la columna «Calidad catálogo» de `propuesta_cliente.md`.

**Escala del mapa de calor** (aparición 0-100 %), 7 tramos: 0-14,9 → #F1F4F5 · 15-29,9 → #D3E3E6 · 30-44,9 → #A9CBD1 · 45-59,9 → #76AAB3 · 60-74,9 → #3F7F8A · 75-89,9 → #1F5C68 · 90-100 → #0F3B45. Texto: `color.text.primary` en los cuatro primeros tramos (≥ 6,57:1), blanco en los tres últimos (≥ 4,55:1).

**Consistencia entre repeticiones**: Consolidada 3/3 → `color.seq.1`; Azar 1-2/3 → `color.seq.4` con rayado 45°; Ausente 0/3 → `color.bg.sunken` con borde `color.border.strong`.

#### 3.1.4 Tema oscuro (opcional, **[Deseable]**)

| Token | Hex oscuro | Token | Hex oscuro |
|---|---|---|---|
| `color.bg.canvas` | #121418 | `color.text.primary` | #ECEDEF |
| `color.bg.surface` | #1A1D23 | `color.text.secondary` | #B4B9C2 |
| `color.bg.sunken` | #0E1013 | `color.text.tertiary` | #8F95A0 |
| `color.bg.inverse` | #ECEDEF | `color.text.inverse` | #121418 |
| `color.border.subtle` | #262A31 | `color.border.default` | #2E333B |
| `color.border.strong` | #6B717C | `color.focus.ring` | #ECEDEF |

| Significado | fg | fill | bg |
|---|---|---|---|
| Marca del brief | #FF8A50 | #F26B2A | #3A1E10 |
| Líder | #E6E8EC | #E6E8EC | #262A31 |
| Resto | #A3A9B3 | #6B717C | #22262D |
| Espontánea | #4FC1CC | #4FC1CC | #0E2E32 |
| Asistida | #B3A2E8 | #B3A2E8 | #262040 |
| Fortaleza / Éxito | #5CC57E | #5CC57E | #13301D |
| Problema | #F2768F | #F2768F | #3A1520 |
| Código | #C9CDD3 | #C9CDD3 | #262A31 |
| IA | #E0A469 | #E0A469 | #33251A |
| Humano | #8DB2F5 | #8DB2F5 | #18253D |
| Degradado | #A3B0C2 | #A3B0C2 | #232A33 |
| Error | #FF7A6E | #FF7A6E | #3A1614 |
| Aviso | #F0B848 | #F0B848 | #33280F |

En oscuro, el líder pasa a casi blanco (#E6E8EC) para mantener su papel de «máximo contraste», y las sombras se sustituyen por bordes `color.border.default`.

#### 3.1.5 Ratios de contraste (WCAG 2.1)

Umbrales: texto normal ≥ 4,5:1; texto grande (≥ 18,66 px negrita o ≥ 24 px) y objetos gráficos ≥ 3:1.

**Tema claro · texto sobre neutros**

| Texto | sobre canvas #F6F5F1 | sobre surface #FFFFFF | sobre sunken #EEECE6 | Resultado |
|---|---|---|---|---|
| text.primary #1A1D23 | 15,47 | 16,88 | 14,29 | AA ✔ (AAA) |
| text.secondary #474D57 | 7,80 | 8,51 | 7,21 | AA ✔ (AAA) |
| text.tertiary #646A75 | 4,99 | 5,44 | 4,60 | AA ✔ |
| brand.fg #B23A0B | 5,50 | 5,99 | 5,07 | AA ✔ |
| leader.fg #1F232B | 14,43 | 15,75 | 13,33 | AA ✔ |
| rest.fg #5B6270 | 5,62 | 6,13 | 5,19 | AA ✔ |
| spont.fg #0A6670 | 6,12 | 6,67 | 5,65 | AA ✔ |
| assist.fg #5B4790 | 7,00 | 7,64 | 6,47 | AA ✔ |
| strength.fg #1B6E35 | 5,78 | 6,31 | 5,34 | AA ✔ |
| problem.fg #9E1C3B | 7,17 | 7,83 | 6,63 | AA ✔ |
| code.fg #3A3F47 | 9,71 | 10,60 | 8,97 | AA ✔ |
| ai.fg #8A5524 | 5,65 | 6,17 | 5,22 | AA ✔ |
| human.fg #1E4C9A | 7,53 | 8,22 | 6,96 | AA ✔ |
| degraded.fg #4F5D70 | 6,15 | 6,70 | 5,68 | AA ✔ |
| error.fg #B42318 | 6,03 | 6,57 | 5,57 | AA ✔ |
| warning.fg #835400 | 5,95 | 6,50 | 5,50 | AA ✔ |

**Tema claro · texto sobre su propio fondo tintado**

| Par | fg sobre bg | text.primary sobre bg |
|---|---|---|
| brand.fg / brand.bg | 5,26 | 14,80 |
| spont.fg / spont.bg | 5,80 | 14,68 |
| assist.fg / assist.bg | 6,46 | 14,27 |
| strength.fg / strength.bg | 5,51 | 14,73 |
| problem.fg / problem.bg | 6,65 | 14,35 |
| code.fg / code.bg | 9,05 | 14,41 |
| ai.fg / ai.bg | 5,48 | 14,99 |
| human.fg / human.bg | 7,04 | 14,46 |
| degraded.fg / degraded.bg | 5,87 | 14,77 |
| error.fg / error.bg | 5,75 | 14,76 |
| warning.fg / warning.bg | 5,89 | 15,31 |
| text.tertiary / brand.bg (fila seleccionada) | 4,77 | · |

**Tema claro · texto blanco sobre rellenos sólidos (botones, chips sólidos)**

| Relleno | Ratio | Relleno | Ratio |
|---|---|---|---|
| bg.inverse #1A1D23 | 16,88 | strength #1B6E35 | 6,31 |
| brand.fg #B23A0B | 5,99 | problem #9E1C3B | 7,83 |
| brand.fill #D9480F | 4,30 (solo texto ≥ 18,66 px negrita) | error #B42318 | 6,57 |
| spont #0A6670 | 6,67 | human #1E4C9A | 8,22 |
| assist #5B4790 | 7,64 | leader.fill #22262E | 15,17 |

**Objetos gráficos (≥ 3:1 frente a `color.bg.surface`)**: brand.fill 4,30 ✔ · leader.fill 15,17 ✔ · rest.fill #7F8794 3,62 ✔ (3,32 sobre canvas) · border.strong #858177 3,89 ✔ (3,56 sobre canvas). Los pasos 4-7 de la escala secuencial no alcanzan 3:1 frente al blanco: por eso todo gráfico que los usa lleva separación blanca de 2 px entre segmentos, etiqueta directa del valor y alternativa en tabla (cumple 1.4.11 al no depender solo del relleno).

**Tema oscuro · texto**

| Texto | canvas #121418 | surface #1A1D23 | sunken #0E1013 |
|---|---|---|---|
| text.primary #ECEDEF | 15,74 | 14,41 | 16,26 |
| text.secondary #B4B9C2 | 9,36 | 8,57 | 9,67 |
| text.tertiary #8F95A0 | 6,12 | 5,61 | 6,33 |
| brand.fg #FF8A50 | 7,90 | 7,24 | 8,17 |
| spont.fg #4FC1CC | 8,63 | 7,90 | 8,92 |
| assist.fg #B3A2E8 | 8,12 | 7,44 | 8,39 |
| strength.fg #5CC57E | 8,55 | 7,83 | 8,84 |
| problem.fg #F2768F | 6,82 | 6,24 | 7,04 |
| code.fg #C9CDD3 | 11,55 | 10,58 | 11,94 |
| ai.fg #E0A469 | 8,50 | 7,78 | 8,79 |
| human.fg #8DB2F5 | 8,62 | 7,89 | 8,91 |
| degraded.fg #A3B0C2 | 8,38 | 7,67 | 8,66 |
| error.fg #FF7A6E | 7,25 | 6,64 | 7,50 |
| warning.fg #F0B848 | 10,23 | 9,37 | 10,57 |

Tintados oscuros (fg sobre su bg): brand 6,56 · spont 6,76 · assist 6,79 · strength 6,64 · problem 5,94 · code 9,02 · ai 6,82 · human 7,16 · degraded 6,58 · error 6,33 · warning 8,03. Todos AA.

### 3.2 Tipografía

**Familias** (todas gratuitas en Google Fonts, licencia OFL):

| Familia | Uso | Pesos cargados |
|---|---|---|
| IBM Plex Sans | Toda la interfaz | 400, 500, 600 |
| IBM Plex Mono | Identificadores (run_id, EJ-…, T1…), origen de cifras («T1 · n = 240»), dominios | 400, 500 |
| Source Serif 4 | Cuerpo de la Propuesta y de la vista de solo lectura (documento para comité) | 400, 600, 400 cursiva |

**Cifras tabulares**: activar la función OpenType de cifras tabulares (tnum) en IBM Plex Sans para todas las cifras de tablas, tarjetas de cifra, ejes y etiquetas de gráficos. En cuerpo de texto corrido se mantienen las cifras proporcionales.

**Escala** (1440 px como referencia; a ≥ 1800 px de ancho se aplica la columna «1920»):

| Token | Familia | Tamaño / interlineado 1440 | 1920 | Peso | Uso |
|---|---|---|---|---|---|
| `type.display.xl` | Plex Sans | 56 / 60 | 72 / 76 | 600 | Cifra protagonista (score del Diagnóstico) |
| `type.display.l` | Plex Sans | 40 / 44 | 48 / 52 | 600 | Cifras de tarjetas KPI |
| `type.display.m` | Plex Sans | 32 / 36 | 40 / 44 | 600 | Cifra principal de hallazgo, sello del revisor |
| `type.h1` | Plex Sans | 28 / 36 | 32 / 40 | 600 | Título de pantalla |
| `type.h2` | Plex Sans | 22 / 28 | 26 / 32 | 600 | Título de sección |
| `type.h3` | Plex Sans | 18 / 24 | 20 / 28 | 600 | Título de tarjeta y de gráfico |
| `type.body.l` | Plex Sans | 16 / 24 | 18 / 28 | 400 | Texto destacado, descripciones de hallazgo |
| `type.body.m` | Plex Sans | 14 / 20 | 16 / 24 | 400 | Texto por defecto de la interfaz |
| `type.body.m.strong` | Plex Sans | 14 / 20 | 16 / 24 | 600 | Etiquetas de campo, celdas destacadas |
| `type.body.s` | Plex Sans | 13 / 18 | 15 / 20 | 400 | Tablas densas, ayudas |
| `type.caption` | Plex Sans | 12 / 16 | 14 / 20 | 500 | Metadatos, tooltips secundarios (mínimo absoluto en interfaz) |
| `type.overline` | Plex Sans | 12 / 16, espaciado +0,04 em, versalitas | 13 / 16 | 600 | Sobretítulos («PUNTO DE CONTROL 2 DE 4») |
| `type.mono.s` | Plex Mono | 12 / 16 | 14 / 20 | 500 | Origen de cifra, IDs en tablas |
| `type.mono.m` | Plex Mono | 14 / 20 | 16 / 24 | 400 | IDs en el visor de evidencias |
| `type.chart.axis` | Plex Sans tnum | 13 / 16 | 15 / 20 | 400 | Etiquetas de ejes |
| `type.chart.label` | Plex Sans tnum | 14 / 18 | 16 / 20 | 600 | Etiquetas directas de valor |
| `type.chart.label.brand` | Plex Sans tnum | 15 / 20 | 18 / 24 | 600 | Etiqueta directa de la marca del brief |
| `type.doc.title` | Source Serif 4 | 36 / 44 | 40 / 48 | 600 | Título de la Propuesta |
| `type.doc.h2` | Source Serif 4 | 24 / 32 | 26 / 34 | 600 | Secciones de la Propuesta |
| `type.doc.h3` | Source Serif 4 | 19 / 28 | 21 / 30 | 600 | Subsecciones |
| `type.doc.body` | Source Serif 4 | 17 / 28 | 18 / 30 | 400 | Cuerpo de la Propuesta (medida 68-72 caracteres) |
| `type.doc.table` | Plex Sans tnum | 14 / 20 | 15 / 22 | 400 | Tablas dentro de la Propuesta |

Reglas: nunca texto menor de 12 px en interfaz ni de 13 px dentro de gráficos. Máximo 2 pesos por componente. Mayúsculas solo en `type.overline`.

### 3.3 Espaciado, rejilla y layout

**Unidad base: 4 px.**

| Token | Valor | Token | Valor |
|---|---|---|---|
| `space.0_5` | 2 px | `space.6` | 24 px |
| `space.1` | 4 px | `space.8` | 32 px |
| `space.2` | 8 px | `space.10` | 40 px |
| `space.3` | 12 px | `space.12` | 48 px |
| `space.4` | 16 px | `space.16` | 64 px |
| `space.5` | 20 px | `space.20` | 80 px |

**Estructura fija de la aplicación (1440×900)**

```text
┌──────────────────────────────────────────────────────────────────────────────┐ 0
│ Aviso de datos sintéticos (28 px)                                            │
├──────────────────────────────────────────────────────────────────────────────┤ 28
│ Barra superior (56 px)                                                       │
├───────────────┬──────────────────────────────────────────────────────────────┤ 84
│ Carril        │ Contenido de la pantalla (scroll vertical propio)            │
│ «Recorrido»   │ margen interior 32 px                                        │
│ 248 px        │ ancho útil 1440 − 248 − 64 = 1128 px                         │
│ (fijo)        │                                                              │
│               ├──────────────────────────────────────────────────────────────┤ 828
│               │ Barra de punto de control (72 px, solo pantallas con CP)     │
└───────────────┴──────────────────────────────────────────────────────────────┘ 900
```

Altura útil de contenido: 900 − 28 − 56 = 816 px; con barra de CP, 744 px.

**Rejilla por resolución**

| Viewport | Carril | Columnas | Medianil | Margen lateral del contenido | Ancho máximo de contenido | Notas |
|---|---|---|---|---|---|---|
| 1920×1080 | 264 px | 12 | 24 px | 48 px | 1560 px (centrado) | Escala tipográfica «1920». Modo proyector por defecto |
| 1440×900 | 248 px | 12 | 24 px | 32 px | 1128 px | Referencia de diseño |
| 1024×768 (tablet horizontal) | 64 px (solo iconos; se expande a 248 px superpuesto al pulsar) | 12 | 16 px | 24 px | 912 px | Visor de evidencias a pantalla casi completa (ancho 100 % − 64 px) |
| 768×1024 (tablet vertical) | Oculto; botón «Recorrido» en la barra superior abre un panel desde la izquierda | 8 | 16 px | 24 px | 720 px | Barra de CP de 88 px con botones a ancho completo |
| 390×844 (móvil) | Solo vista 8 de solo lectura | 4 | 16 px | 16 px | 358 px | Sin carril ni edición |

Anchos de columna a 1440 (12 col, medianil 24, ancho 1128): columna = 72 px. Una tarjeta KPI ocupa 3 columnas (264 px). El gráfico principal ocupa 8 columnas (744 px) y el panel lateral de detalle 4 (360 px).

**Anchos máximos de lectura**: texto corrido 720 px; documento de la Propuesta 760 px de cuerpo con márgenes de 64 px en la hoja (hoja de 888 px).

### 3.4 Radios, bordes, sombras y elevación

| Token | Valor | Uso |
|---|---|---|
| `radius.s` | 4 px | Chips, etiquetas, celdas de mapa de calor, barras de gráfico (solo extremo libre) |
| `radius.m` | 6 px | Botones, campos, selectores, tooltips |
| `radius.l` | 10 px | Tarjetas, paneles, barra de CP |
| `radius.xl` | 14 px | Modales |
| `radius.full` | 999 px | Conmutador de modo, interruptores, avatares |

| Token | Valor | Uso |
|---|---|---|
| `border.thin` | 1 px sólido `color.border.default` | Tarjetas |
| `border.control` | 1 px sólido `color.border.strong` | Campos, selectores |
| `border.emphasis` | 2 px sólido | Fila de la marca del brief (`color.brand.border`), foco interno |
| `border.code` | 1 px sólido `color.code.border` | Bloques calculados |
| `border.ai` | 1,5 px discontinuo (trazo 4 px, hueco 3 px) `color.ai.border` | Bloques redactados por IA |
| `border.human` | doble: 1 px + hueco 2 px + 1 px, `color.human.border` | Sellos y bloques aprobados |
| `border.degraded` | 1 px discontinuo (2 px / 2 px) `color.degraded.border` | Paso degradado |

**Elevación** (tema claro; en oscuro se sustituye por borde `color.border.default` y superficie un paso más clara):

| Nivel | Sombra (desplazamiento Y · desenfoque · color con opacidad) | Uso |
|---|---|---|
| `elevation.0` | ninguna | Contenido sobre canvas |
| `elevation.1` | 1 px · 2 px · #1A1D23 al 6 % | Tarjetas |
| `elevation.2` | 4 px · 12 px · #1A1D23 al 10 % | Barra de CP, menús desplegables, tooltips |
| `elevation.3` | 12 px · 32 px · #1A1D23 al 14 % | Panel lateral (visor de evidencias) |
| `elevation.4` | 16 px · 48 px · #1A1D23 al 18 % | Modales |

Velo de fondo de modal y panel: #1A1D23 al 40 % (claro), #000000 al 60 % (oscuro).

### 3.5 Iconografía

Librería: **Lucide** (gratuita, trazo de contorno). Trazo 1,5 px. Esquinas redondeadas de serie. Tamaños: `icon.s` 14 px (dentro de chips y texto `body.s`), `icon.m` 16 px (por defecto), `icon.l` 20 px (carril, botones grandes), `icon.xl` 24 px (estados vacíos usan 40 px como excepción). Color: hereda el del texto contiguo. Ningún icono aparece solo sin texto o sin etiqueta accesible.

| Significado | Icono Lucide | Dónde |
|---|---|---|
| Marca del brief | `crosshair` | Junto al nombre de la marca del brief en tablas, gráficos y leyendas |
| Calculado por código | `sigma` | Marca de origen |
| Redactado por IA | `pen-line` | Marca de origen |
| Aprobado por humano | `user-check` | Marca de origen, carril, sellos |
| Esperando aprobación | `user-round-search` | Carril, chip de estado |
| Pendiente | `circle-dashed` | Carril |
| En curso | `loader-circle` (gira) | Carril, botones cargando |
| Hecho | `check` | Carril |
| Degradado | `split` | Carril, indicador de paso degradado |
| Error | `octagon-x` | Mensajes de error |
| Aviso | `triangle-alert` | Avisos, discrepancias del brief |
| Desactualizado | `refresh-ccw` | Carril |
| Bloqueado | `lock` | Carril, vista de solo lectura |
| Fortaleza | `trending-up` | Tarjeta de hallazgo |
| Problema | `trending-down` | Tarjeta de hallazgo |
| Hipótesis | `flask-conical` | Contraste de hipótesis |
| Confirmada | `circle-check` | Contraste de hipótesis |
| Refutada | `circle-x` | Contraste de hipótesis |
| Evidencias | `scan-search` | Botón «Ver evidencias», enlace de cifra |
| Fuente citada | `link-2` | Visor de evidencias |
| Motor (chatbot) | `message-square-text` | Filtros, visor |
| Ciudad | `map-pin` | Filtros, visor |
| Embudo | `filter` | Etiqueta de fase |
| Muestra pequeña | `info` en chip «n bajo» | Celdas y tarjetas con n < 15 |
| Presupuesto | `wallet` | Plan |
| Calendario | `calendar-range` | Gantt |
| Equipo / carga | `users` | Carga semanal |
| Simulador | `sliders-horizontal` | Simulador what-if |
| Hito de re-medición | `diamond` | Gantt |
| Editar | `pencil` | Tablas editables |
| Excluir | `circle-minus` | Competencia |
| Descargar | `download` | Propuesta |
| Copiar | `copy` | Correo comercial, run_id |
| Deshacer | `undo-2` | Toasts |
| Cerrar | `x` | Paneles, modales |
| Expandir / contraer | `chevron-down` / `chevron-up` | Evidencias desplegables |
| Coste | `euro` | Selector de proveedor |
| Documento | `file-text` | Brief, Propuesta |
| Subir archivo | `upload` | Inicio |
| Enlace de solo lectura | `link` | Propuesta |
| Atajos | `keyboard` | Barra superior |

### 3.6 Movimiento

| Token | Duración | Curva | Uso |
|---|---|---|---|
| `motion.instant` | 0 ms | · | Cambios de estado de foco |
| `motion.fast` | 120 ms | estándar (0,2 · 0 · 0 · 1) | Hover, pulsación, chips |
| `motion.base` | 200 ms | estándar | Desplegables, tooltips, cambio de pestaña, conmutador de modo |
| `motion.slow` | 320 ms | desaceleración (0 · 0 · 0,2 · 1) | Apertura de panel lateral y modal |
| `motion.exit` | 160 ms | aceleración (0,4 · 0 · 1 · 1) | Cierre de panel, modal, toast |
| `motion.chart` | 400 ms | estándar | Transición de valores al cambiar espontánea/asistida o filtros |

Reglas:

- Los gráficos **no** se animan en la carga inicial; solo interpolan valores al cambiar de modo o filtro, para que el ojo siga el cambio.
- El anillo de «En curso» gira a 1 vuelta cada 900 ms.
- Al aprobar un CP, el segmento del CP en el carril pasa a cobalto en `motion.base` y el sello aparece con un fundido de 200 ms. Nada de confeti ni rebotes.
- Con «Reducir movimiento» activado en el sistema operativo: todas las duraciones pasan a 0 ms salvo el anillo de carga, que se sustituye por puntos suspensivos estáticos con el texto «Calculando…».

### 3.7 Formato de números, fechas y unidades

| Dato | Formato | Ejemplo |
|---|---|---|
| Porcentaje | 1 decimal, coma, espacio fino no separable antes de % | 38,8 % |
| Score | 2 decimales | 27,97 |
| Fuerza media | 2 decimales sobre escala −1 a 3 | 1,21 |
| Calidad de fuente | 2 decimales | 0,69 |
| Euros | sin decimales, punto de miles, espacio fino antes de € | 24.300 € |
| Recuentos | punto de miles | 2.928 evaluaciones |
| Tamaño de muestra | «n = 240» (mono, espacios finos) | n = 240 |
| Puesto | «7.º de 10» | 7.º de 10 |
| Fecha | «20 oct. 2026» en tablas; «20 de octubre de 2026» en documentos | |
| Hora | 24 h | 23:00 |
| Semanas | «S12»; rango «S5–S8» | |
| Diferencia en puntos | «−50,0 p. p.» (puntos porcentuales) | |
| Rangos objetivo | «40,0 – 48,0» | |

Redondeo: el backend entrega los valores; la interfaz solo formatea. Si una cifra de `metrics.json` tiene más decimales (0,3875) se muestra como 38,8 % para coincidir con las tablas del backend.

---

## 4. Componentes

Plantilla de cada ficha: **Anatomía** (partes numeradas) · **Medidas** · **Tokens** · **Variantes** · **Estados** · **Comportamiento** · **Accesibilidad**. Los estados no aplicables se indican con «·».

Estados genéricos que se repiten (se aplican salvo que la ficha diga otra cosa):

| Estado | Tratamiento genérico |
|---|---|
| Por defecto | Según ficha |
| Hover | Fondo un paso más oscuro (claro) o más claro (oscuro); cursor de mano en elementos clicables; `motion.fast` |
| Foco (teclado) | Anillo de 2 px `color.focus.ring` con separación de 2 px; nunca se elimina |
| Activo (pulsado) | Desplazamiento visual nulo; fondo dos pasos más oscuro |
| Deshabilitado | Texto `color.text.disabled`, borde `color.border.subtle`, sin sombra, cursor no permitido; tooltip que explica por qué |
| Cargando | Esqueleto de bloques `color.bg.sunken` con pulso de opacidad 100 % ↔ 60 % cada 1,2 s (estático con movimiento reducido) |
| Error | Borde y texto de ayuda `color.error.fg` con icono `octagon-x` |
| Vacío | Icono 40 px `color.text.tertiary`, título `type.h3`, texto `type.body.m` secundario y una acción |

### 4.A Componentes base

#### 4.A.1 Botón **[Imprescindible]**

- **Anatomía**: (1) contenedor · (2) icono opcional a la izquierda · (3) etiqueta · (4) atajo opcional a la derecha en `type.mono.s` (por ejemplo «Ctrl ↵»).
- **Medidas**: alto 40 px (M, por defecto), 32 px (S, en tablas y barras densas), 48 px (L, barra de CP y «Cargar demo»). Relleno horizontal 16 px (M), 12 px (S), 20 px (L). Separación icono-texto 8 px. Ancho mínimo 88 px. Radio `radius.m`.
- **Variantes y tokens**:

| Variante | Fondo | Texto | Borde | Uso |
|---|---|---|---|---|
| Principal | `color.bg.inverse` | `color.text.inverse` | · | Una por vista: aprobar, lanzar, descargar |
| Secundario | `color.bg.surface` | `color.text.primary` | `border.control` | Acciones alternativas |
| Fantasma | transparente | `color.text.primary` | · | Acciones terciarias, en tablas |
| Aprobar (CP) | `color.human.fill` | blanco (8,22:1) | · | Solo botones de aprobación de CP |
| Peligro | `color.error.fill` | blanco (6,57:1) | · | Excluir marca, descartar hallazgo en confirmación |
| Enlace | transparente | `color.text.primary` subrayado 1 px | · | En texto corrido |

- **Estados**: Hover principal → #2C313A (blanco 13,06:1); secundario → fondo `color.bg.sunken`. Foco genérico. Activo: fondo un paso más. Deshabilitado genérico. Cargando: el icono se sustituye por `loader-circle` girando, la etiqueta cambia a gerundio («Aprobando…», «Calculando…»), el ancho se congela para que no salte. Error · (los botones no tienen estado de error; el error se muestra en el contexto). Vacío ·.
- **Comportamiento**: doble clic protegido (ignora pulsaciones durante «Cargando»). Los botones de aprobación muestran tras el éxito un check de 1 s antes de navegar.
- **Accesibilidad**: elemento botón nativo; etiqueta visible = nombre accesible; el atajo se anuncia en la descripción accesible («Atajo: Control más Intro»).

#### 4.A.2 Campo de texto y área de texto **[Imprescindible]**

- **Anatomía**: (1) etiqueta `type.body.m.strong` · (2) marca de obligatoriedad «(obligatorio)» en `type.caption` · (3) contenedor · (4) valor · (5) ayuda o error `type.caption` · (6) marca de origen opcional (Σ, pluma, persona) alineada a la derecha de la etiqueta · (7) contador opcional.
- **Medidas**: alto 40 px; área de texto mínimo 88 px, crece hasta 240 px y luego desplaza. Relleno 12 px horizontal. Etiqueta a 6 px del contenedor. Ayuda a 6 px debajo.
- **Tokens**: fondo `color.bg.surface`, borde `border.control`, texto `color.text.primary`, marcador de posición `color.text.tertiary`.
- **Variantes**: estándar · con prefijo/sufijo («€», «%») · numérica (alineada a la derecha, cifras tabulares) · **«No encontrado en el brief»** (ver estados).
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Por defecto | Como arriba |
| Hover | Borde `color.text.secondary` |
| Foco | Borde 2 px `color.text.primary` + anillo genérico |
| Deshabilitado / solo lectura | Fondo `color.bg.sunken`, sin borde; en solo lectura el texto sigue siendo `color.text.primary` |
| Error | Borde 2 px `color.error.border`, ayuda en `color.error.fg` con `octagon-x`: p. ej. «El presupuesto máximo debe ser mayor que el mínimo.» |
| No encontrado en el brief | Fondo `color.warning.bg`, borde 1 px discontinuo `color.warning.border`, marcador «Completa este campo: no aparece en el brief», chip «Falta en el brief» junto a la etiqueta |
| Editado por persona | Al modificar un valor extraído, la marca de origen pasa de pluma (IA) a persona (humano) y aparece «Editado por ti» en `type.caption` |
| Sin guardar | Punto ámbar de 6 px a la izquierda de la etiqueta |
| Cargando | Esqueleto del alto del campo |

- **Accesibilidad**: etiqueta asociada; ayuda y error vinculados como descripción; el error se anuncia con región en vivo educada; el chip «Falta en el brief» forma parte del nombre accesible.

#### 4.A.3 Selector (desplegable, combinado y multiselección) **[Imprescindible]**

- **Anatomía**: (1) etiqueta · (2) disparador con valor y `chevron-down` · (3) lista desplegable · (4) opción con check · (5) buscador (en combinado) · (6) chips de seleccionados (en multiselección).
- **Medidas**: disparador 40 px; opción 36 px; lista máximo 320 px de alto; ancho = disparador (mínimo 200 px).
- **Tokens**: igual que campo; lista en `color.bg.surface` con `elevation.2`; opción hover `color.bg.sunken`; seleccionada con check `color.text.primary` y peso 600.
- **Variantes**: simple · combinado con búsqueda (marcas, ciudades) · multiselección con chips (servicios, públicos, motores) · selector en celda (S, 32 px, para tablas editables).
- **Estados**: genéricos. Vacío: «No hay opciones que coincidan con “{texto}”.». Cargando: 3 filas esqueleto.
- **Comportamiento**: se abre con clic, Intro, Espacio o flecha abajo; Esc cierra; escribir filtra en combinados.
- **Accesibilidad**: patrón de lista desplegable accesible (combobox/listbox) de la librería de componentes.

#### 4.A.4 Chip y etiqueta **[Imprescindible]**

- **Anatomía**: (1) contenedor · (2) icono opcional 14 px · (3) texto · (4) botón quitar opcional (`x`, 14 px).
- **Medidas**: alto 24 px (M), 20 px (S); relleno 8 px (M) y 6 px (S); radio `radius.s`; texto `type.caption`.
- **Variantes**:

| Variante | Fondo / texto | Ejemplos de texto |
|---|---|---|
| Neutra | `color.bg.sunken` / `color.text.secondary` | «ChatGPT», «Madrid», «S12» |
| Semántica tintada | `{significado}.bg` / `{significado}.fg` | «Fortaleza», «Problema», «Espontánea», «Asistida», «Líder» |
| Semántica sólida | `{significado}.fill` / blanco | Solo para «Tu marca» en leyendas |
| Rol de competencia | ver tabla de roles en 4.B.18 | «Marca del brief», «Líder», «Competidor directo», «Referencia», «Contexto» |
| Impacto / confianza | contorno 1 px `color.border.strong`, texto primario, con 1-3 barras verticales de 3×10 px como icono de nivel | «Impacto alto», «Confianza media» |
| Talla | cuadrado de 24 px, mono 12 px | «S», «M», «L» |
| n bajo | `color.warning.bg` / `color.warning.fg` + `info` | «n bajo» |
| Falta en el brief | `color.warning.bg` / `color.warning.fg` + `triangle-alert` | «Falta en el brief» |

- **Estados**: Hover y foco solo si es interactivo (filtro o quitable). Seleccionado (filtro): borde 2 px `color.text.primary`. Deshabilitado genérico.
- **Accesibilidad**: los chips de filtro son botones conmutables con estado «pulsado»; los informativos son texto.

#### 4.A.5 Pestañas **[Imprescindible]**

- **Anatomía**: (1) lista de pestañas · (2) pestaña con etiqueta y contador opcional · (3) indicador inferior · (4) panel.
- **Medidas**: alto 44 px; relleno horizontal 16 px; separación 4 px; indicador 2 px de alto, ancho = pestaña.
- **Tokens**: texto inactivo `color.text.secondary`; activo `color.text.primary` 600; indicador `color.text.primary`; línea base 1 px `color.border.subtle`.
- **Variantes**: estándar · segmentada (fondo `color.bg.sunken`, pestaña activa en `color.bg.surface` con `elevation.1`, radio `radius.m`; se usa para «Cliente / Prospecto» y vistas de tabla/gráfico).
- **Estados**: hover texto primario; foco genérico; deshabilitado genérico con tooltip.
- **Accesibilidad**: patrón de pestañas; flechas izquierda/derecha cambian; Inicio/Fin a primera/última.

#### 4.A.6 Tabla de datos **[Imprescindible]**

- **Anatomía**: (1) cabecera fija · (2) celda de cabecera con orden · (3) fila · (4) celda · (5) celda numérica (derecha, tnum) · (6) pie con origen («T1 · n = 240 por marca · Espontánea») · (7) barra de acciones de fila opcional.
- **Medidas**: fila 44 px (normal), 36 px (densa); cabecera 40 px; relleno de celda 12 px horizontal; primera columna con 16 px.
- **Tokens**: cabecera `color.bg.sunken`, texto `type.caption` 600 `color.text.secondary`; filas `color.bg.surface`; separadores `color.border.subtle`; hover de fila `color.bg.canvas`.
- **Variantes**:
  - **Fila de la marca del brief**: fondo `color.brand.bg`, borde izquierdo 4 px `color.brand.fill`, nombre en 600 con icono `crosshair` y chip «Tu marca».
  - **Fila del líder**: nombre en 600 con chip «Líder» (`color.leader`).
  - **Fila excluida**: texto tachado `color.text.tertiary`, chip «Excluida».
  - **Celda con n bajo**: fondo rayado 45° (líneas de 1 px `color.warning.border` cada 6 px al 40 %), cifra en `color.text.secondary` y chip «n bajo».
  - **Celda clicable (cifra trazable)**: cifra con subrayado punteado 1 px `color.text.tertiary`; al pasar, icono `scan-search` 14 px a la derecha.
- **Estados**: cargando (5 filas esqueleto); vacío («No hay datos para este filtro.» + botón «Quitar filtros»); error («No se pudo cargar la tabla {T}.» + «Reintentar»); orden (flecha en cabecera, `aria-sort`).
- **Comportamiento**: ordenar por clic en cabecera; desplazamiento horizontal interno si no cabe (nunca de la página); la primera columna se fija.
- **Accesibilidad**: tabla semántica con cabeceras de fila y columna; las celdas clicables son botones con nombre «Ver evidencias de {métrica} {valor}, n = {n}».

#### 4.A.7 Tarjeta **[Imprescindible]**

- **Anatomía**: (1) contenedor · (2) cabecera (sobretítulo opcional, título `type.h3`, acciones a la derecha) · (3) cuerpo · (4) pie opcional con origen.
- **Medidas**: relleno 24 px (20 px en tablet); separación cabecera-cuerpo 16 px; radio `radius.l`; borde `border.thin`; `elevation.1`.
- **Variantes**: estándar · interactiva (toda la tarjeta clicable; hover `elevation.2`) · con franja lateral semántica de 4 px (fortaleza, problema, aviso, degradado) · hundida (`color.bg.sunken`, sin sombra).
- **Estados**: genéricos; cargando (esqueleto con la misma estructura); error (cuerpo sustituido por mensaje y «Reintentar»).

#### 4.A.8 Modal **[Imprescindible]**

- **Anatomía**: (1) velo · (2) contenedor · (3) título `type.h2` · (4) cuerpo · (5) pie con acciones a la derecha (secundaria a la izquierda de la principal) · (6) botón cerrar `x`.
- **Medidas**: ancho 520 px (S), 720 px (M); relleno 32 px; radio `radius.xl`; `elevation.4`.
- **Variantes**: confirmación · aviso (icono `triangle-alert` en `color.warning.fg` junto al título) · peligro (botón principal en variante Peligro).
- **Comportamiento**: foco atrapado; Esc cierra (salvo en operaciones en curso); el foco vuelve al disparador al cerrar.
- **Accesibilidad**: diálogo modal con título como nombre y cuerpo como descripción.

#### 4.A.9 Panel lateral **[Imprescindible]**

- **Anatomía**: (1) velo (solo en tablet) · (2) contenedor anclado a la derecha · (3) cabecera fija (título, subtítulo, cerrar) · (4) cuerpo con desplazamiento · (5) pie fijo opcional.
- **Medidas**: ancho 640 px a 1440; 760 px a 1920; 100 % − 64 px en 1024; 100 % en 768. Alto: desde debajo del aviso de datos sintéticos hasta el borde inferior (el aviso siempre visible). Cabecera 72 px. Relleno 24 px.
- **Tokens**: `color.bg.surface`, borde izquierdo `border.thin`, `elevation.3`.
- **Comportamiento**: entra desde la derecha en `motion.slow`; en escritorio **no** bloquea la pantalla (sin velo) para poder comparar; Esc cierra; un segundo clic en otra cifra reemplaza el contenido y lo anuncia.
- **Accesibilidad**: región complementaria con título; en tablet se comporta como diálogo modal.

#### 4.A.10 Toast **[Imprescindible]**

- **Anatomía**: (1) icono de estado · (2) mensaje `type.body.m` · (3) acción opcional («Deshacer») · (4) cerrar.
- **Medidas**: ancho 400 px; alto mínimo 56 px; relleno 16 px; posición abajo a la derecha a 24 px de los bordes, por encima de la barra de CP; radio `radius.l`; `elevation.2`; fondo `color.bg.inverse`, texto `color.text.inverse`.
- **Variantes**: éxito (icono `check` en #5CC57E), aviso (`triangle-alert` #F0B848), error (`octagon-x` #FF7A6E), información.
- **Comportamiento**: 5 s visible (10 s si tiene «Deshacer»); se pausa al pasar el ratón o con foco; máximo 3 apilados.
- **Accesibilidad**: región en vivo educada (asertiva para errores); la acción es alcanzable con teclado mediante el atajo F6 (mueve el foco a la región de notificaciones).

#### 4.A.11 Tooltip **[Imprescindible]**

- **Anatomía**: (1) contenedor · (2) título opcional `type.body.m.strong` · (3) texto `type.body.s` · (4) línea de origen `type.mono.s`.
- **Medidas**: ancho máximo 320 px; relleno 12 px; radio `radius.m`; fondo `color.bg.inverse`; texto `color.text.inverse`; origen en #B4B9C2.
- **Comportamiento**: aparece a los 300 ms de hover o al instante con foco; desaparece al salir; nunca contiene acciones (para eso, popover).
- **Accesibilidad**: vinculado como descripción; se puede cerrar con Esc sin mover el foco.

#### 4.A.12 Barra de progreso **[Imprescindible]**

- **Anatomía**: (1) etiqueta · (2) pista · (3) relleno · (4) valor textual («3 de 8 pasos»).
- **Medidas**: alto 4 px (fina), 8 px (normal); radio `radius.full`.
- **Variantes**: determinada · indeterminada (segmento de 30 % que recorre la pista en 1,4 s; estática con movimiento reducido) · segmentada (4 segmentos de CP separados 4 px).
- **Tokens**: pista `color.bg.sunken`; relleno `color.text.primary`; segmentos de CP: aprobado `color.human.fill`, esperando `color.warning.fill` rayado, pendiente `color.border.default`.
- **Accesibilidad**: barra de progreso con valor actual, mínimo y máximo y texto de valor.

#### 4.A.13 Indicador de pasos · carril «Recorrido» **[Imprescindible]**

- **Anatomía**: (1) cabecera del carril: nombre de la marca (`type.body.m.strong`) y run_id (`type.mono.s`) · (2) resumen de CP con barra segmentada · (3) lista de pasos · (4) paso: número en círculo de 24 px, nombre, chip de CP («CP2»), línea de estado · (5) separador · (6) enlace fijo «Calidad y trazas» al pie · (7) botón contraer.
- **Medidas**: ancho 248 px; relleno 16 px; paso 56 px de alto (nombre `type.body.m.strong` + estado `type.caption`); conector vertical de 2 px entre círculos.
- **Tokens**: fondo `color.bg.surface`; borde derecho `border.thin`; paso actual con fondo `color.bg.sunken` y barra izquierda de 3 px `color.text.primary`.
- **Estados del paso**: ver tabla 2.2. Hover: fondo `color.bg.canvas`. Foco genérico. Bloqueado: no navegable, tooltip.
- **Variante contraída** (1024): 64 px, solo círculos con icono de estado; tooltip con nombre y estado.
- **Accesibilidad**: navegación con lista ordenada; el paso actual tiene «página actual»; cada paso anuncia «Paso 4, Hallazgos, punto de control 2, te toca revisar».

#### 4.A.14 Deslizador (para el simulador) **[Imprescindible si se hace el simulador]**

- **Anatomía**: (1) etiqueta · (2) valor actual en caja numérica editable (64 px) · (3) pista · (4) tramo relleno · (5) tirador · (6) marca del valor actual de los datos («Hoy») como tic vertical de 12 px `color.brand.fill` · (7) mínimo y máximo.
- **Medidas**: pista 4 px; tirador 20 px; área de pulsación 44×44 px; ancho 100 % de la columna.
- **Tokens**: pista `color.bg.sunken`; relleno `color.text.primary`; tirador `color.bg.surface` con borde 2 px `color.text.primary`.
- **Comportamiento**: flechas ± 1 punto; Mayús + flechas ± 5; Re Pág/Av Pág ± 10; Inicio/Fin a mínimo/máximo.
- **Accesibilidad**: control deslizante con valor textual («54,2 %, valor actual de los datos 54,2 %»).

#### 4.A.15 Zona de carga de archivo **[Imprescindible]**

- **Anatomía**: (1) área con borde discontinuo 1,5 px `color.border.strong` · (2) icono `upload` 24 px · (3) texto · (4) botón «Elegir archivo» · (5) formatos aceptados · (6) archivo cargado (nombre, tamaño, quitar).
- **Medidas**: alto 160 px; radio `radius.l`.
- **Estados**: arrastrando encima (fondo `color.bg.sunken`, borde sólido 2 px `color.text.primary`, texto «Suelta el archivo para subirlo»); error de formato («Formato no admitido. Usa .md, .docx o .txt.»); error de tamaño («El archivo supera el tamaño máximo de [dato pendiente] MB.»); cargando (barra determinada).
- **Accesibilidad**: el botón «Elegir archivo» es la vía principal; arrastrar es una alternativa.

#### 4.A.16 Barra superior **[Imprescindible]**

- **Anatomía** (izquierda a derecha): (1) logotipo (símbolo de registro 20 px + «GEO Copilot» `type.h3`) · (2) separador · (3) nombre de la marca del análisis `type.body.m.strong` · (4) run_id en chip mono con botón copiar · (5) chip de modo («Modo cliente» / «Modo prospecto») · (6) chip de proveedor («Proveedor: mock») · (7) espacio flexible · (8) chip de estado global · (9) botón atajos `keyboard` · (10) selector de tema (claro / oscuro / sistema) · (11) iniciales del revisor en círculo de 32 px.
- **Medidas**: alto 56 px; relleno 24 px horizontal; separación entre chips 8 px.
- **Tokens**: fondo `color.bg.surface`; borde inferior `border.thin`.
- **Responsive**: en 1024 se ocultan (5) y (6) dentro de un popover «Detalles del análisis»; en 768 aparece a la izquierda el botón «Recorrido».

### 4.B Componentes propios

#### 4.B.1 Aviso de datos sintéticos **[Imprescindible]**

- **Anatomía**: (1) icono `triangle-alert` 14 px · (2) texto · (3) enlace «Qué significa».
- **Texto exacto**: «Datos sintéticos del kit · no representan el comportamiento real de ningún LLM» · enlace «Qué significa».
- **Medidas**: barra fija a todo el ancho, alto 28 px, texto `type.caption` centrado verticalmente, alineado a la izquierda con margen 24 px.
- **Tokens**: claro: fondo `color.warning.bg` #FFF3D6, texto #5C3B00 (9,15:1), borde inferior 1 px `color.warning.border`. Oscuro: fondo #2B2416, texto #F5E6C4 (12,44:1).
- **Comportamiento**: no se puede cerrar. Siempre visible, también sobre paneles y en la vista de solo lectura y en la Propuesta exportada (como primera línea). «Qué significa» abre un popover: «Este análisis usa un conjunto de respuestas generado para el reto UFV × reload. Reproduce patrones de estudios GEO, pero ninguna cifra describe lo que responde hoy un chatbot real sobre una clínica real.»
- **Accesibilidad**: región con nombre «Aviso de datos»; se lee al inicio de cada página.

#### 4.B.2 Marca de origen (código / IA / humano) **[Imprescindible]**

- **Anatomía**: (1) icono 14 px · (2) texto corto · (3) detalle opcional en tooltip.
- **Medidas**: chip S de 20 px de alto; radio `radius.s`; texto `type.caption`.

| Variante | Icono | Texto | Fondo / texto | Borde | Tooltip |
|---|---|---|---|---|---|
| Código | `sigma` | «Calculado» | `color.code.bg` / `color.code.fg` | sólido 1 px | «Calculado por código a partir de {tabla}. Sin intervención de IA.» |
| IA | `pen-line` | «Redactado por IA» | `color.ai.bg` / `color.ai.fg` | discontinuo 1,5 px | «Texto redactado por {modelo} con el prompt {versión}. Revísalo antes de aprobar.» (si mock: «Texto generado por plantilla en modo mock.») |
| Humano | `user-check` | «Aprobado · {iniciales}» | `color.human.bg` / `color.human.fg` | doble | «Aprobado por {nombre} el {fecha} a las {hora}.» |
| Editado | `pencil` | «Editado por {iniciales}» | `color.human.bg` / `color.human.fg` | sólido 1 px | «Valor cambiado manualmente. Original: {valor original}.» |

- **Aplicación a bloques** (no solo chips): un bloque de texto redactado por IA lleva el borde `border.ai` a la izquierda (3 px discontinuo) y el chip en su esquina superior derecha; una tabla calculada lleva el chip «Calculado» en su pie; un bloque aprobado lleva el borde `border.human` a la izquierda.
- **Regla de combinación**: si un bloque de IA se aprueba, conserva su chip «Redactado por IA» y añade el de «Aprobado». La persona aprueba, no se convierte en autora.
- **Accesibilidad**: el texto del chip es parte del contenido accesible; el borde nunca es la única señal.

#### 4.B.3 Conmutador Espontánea / Asistida **[Imprescindible]**

- **Anatomía**: (1) sobretítulo «ÁMBITO DE LAS PREGUNTAS» · (2) control segmentado de dos opciones · (3) opción con icono, nombre y tamaño de muestra · (4) texto explicativo bajo el control · (5) franja de modo a todo el ancho del contenido.
- **Medidas**: control 48 px de alto, ancho 440 px (cada opción 220 px), radio `radius.full`; borde 1,5 px del color del modo activo; opción activa rellena del color del modo con texto blanco; inactiva fondo `color.bg.surface`, texto `color.text.secondary`. Franja de modo: 4 px de alto, color del modo, pegada bajo la cabecera fija del Diagnóstico.
- **Contenido exacto**:
  - Opción 1: icono `message-square-text` · «Espontánea» · «n = 240 por marca».
  - Opción 2: icono `message-square-quote` · «Asistida» · «n = 108 (tu marca)».
  - Explicación (cambia con el modo):
    - Espontánea: «Preguntas que no nombran ninguna clínica. Mide si el chatbot conoce y recomienda tu marca por iniciativa propia.»
    - Asistida: «Preguntas que nombran tu marca o la enfrentan a otra. Mide qué dice el chatbot de ella cuando ya la conoce.»
- **Comportamiento**:
  - Afecta a **todo** el Diagnóstico: tarjetas de cifra, todos los gráficos, tablas y el visor de evidencias abierto (filtra por el ámbito).
  - Estado persistente por análisis (se recuerda al volver). Por defecto: Espontánea.
  - Al cambiar, los valores interpolan en `motion.chart` y un anuncio en vivo dice «Mostrando resultados de preguntas asistidas».
  - Los gráficos que no aplican en un ámbito muestran su estado «No aplica» (ver sección 5) en lugar de desaparecer, para que el layout no salte.
  - Cada título de gráfico y tarjeta lleva un chip del ámbito activo («Espontánea» / «Asistida»), de modo que una captura de pantalla nunca pierde la etiqueta.
- **Estados**: hover en opción inactiva: fondo `{modo}.bg`; foco genérico; deshabilitado (si un ámbito no tiene datos): tooltip «No hay ejecuciones asistidas en este análisis.».
- **Accesibilidad**: grupo de botones de opción con nombre «Ámbito de las preguntas»; atajos Alt + Mayús + E (espontánea) y Alt + Mayús + A (asistida).

#### 4.B.4 Tarjeta de cifra con origen y n **[Imprescindible]**

- **Anatomía**: (1) etiqueta `type.body.m` secundaria · (2) chip de ámbito · (3) cifra `type.display.l` · (4) unidad o contexto («de 10», «/ 100») `type.body.l` secundaria · (5) comparación opcional («Líder: 90,8 %») `type.body.s` · (6) línea de origen en `type.mono.s` `color.text.tertiary`: «{tabla} · n = {n}» · (7) botón «Ver evidencias» fantasma S con `scan-search` · (8) marca de origen «Calculado».
- **Medidas**: 264 × 168 px a 1440 (3 columnas); relleno 20 px; cifra a 8 px de la etiqueta.
- **Variantes**: estándar · protagonista (cifra `type.display.xl`, 6 columnas, borde izquierdo 4 px `color.brand.fill`) · compacta (en tarjetas de hallazgo: cifra `type.display.m`, sin botón, toda la tarjeta clicable) · con barra de componentes (para el score: barra apilada de 4 componentes debajo, ver 5.2).
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Por defecto | Como arriba |
| Hover | Fondo `color.bg.canvas`, aparece «Ver evidencias» si estaba oculto |
| Foco | Anillo genérico sobre toda la tarjeta |
| Cargando | Esqueleto: barra 60 % para etiqueta, bloque 120×40 para cifra |
| n bajo (n < 15) | Cifra en `color.text.secondary`, chip «n bajo» junto a la etiqueta, fondo rayado suave en la zona de la cifra, tooltip «Muestra pequeña (n = {n}). Interprétalo con cautela.» |
| Sin dato | Cifra «—» y texto «[dato pendiente]» en `type.caption` |
| Error | «No se pudo calcular esta cifra.» + «Reintentar» |

- **Comportamiento**: clic en la cifra o en «Ver evidencias» abre el visor filtrado por la métrica (1 clic).
- **Accesibilidad**: la tarjeta es un botón con nombre completo: «Aparición espontánea, 38,8 %, tabla T1, n = 240. Ver evidencias».

#### 4.B.5 Visor de evidencias **[Imprescindible]**

Componente reutilizable. Se abre desde cualquier cifra, celda, barra, punto o hallazgo.

- **Anatomía** (dentro de un Panel lateral de 640 px):
  1. **Cabecera** (72 px): sobretítulo «EVIDENCIAS» · título = métrica en lenguaje natural («Aparición espontánea · Clínica Alborada Visión · Barcelona») · línea de origen mono «T4 · n = 24 · tasa_aparicion_espontanea[ciudad=Barcelona]» · cerrar.
  2. **Resumen** (bloque `color.bg.sunken`, 64 px): valor grande («4,2 %») + frase de composición: «1 de 24 respuestas menciona la marca» (si el backend da numerador; si no, [dato pendiente]) + chip de ámbito.
  3. **Filtros** (fila de chips, 40 px): Motor (4 chips) · Repetición (1, 2, 3) · Ciudad · «Solo donde aparece la marca» (conmutador, activo por defecto si la métrica es de aparición).
  4. **Lista de ejecuciones**: tarjetas compactas ordenadas por ID.
  5. **Pie** (56 px): «{k} de {n} ejecuciones · Exportar CSV» y paginación (20 por página).
- **Tarjeta de ejecución** (contraída, 88 px):
  - Línea 1: ID mono («EJ-0406») · chip motor · chip «Rep. {r}» · chip ciudad (si aplica) · chip de ámbito.
  - Línea 2: pregunta ejecutada en `type.body.m`, recortada a 1 línea con puntos suspensivos: [dato pendiente: `prompt_ejecutado`].
  - Línea 3: resultado para la marca: «Aparece · posición {p} · {tipo de mención} · fuerza {f}» o «No aparece»; chip de sentimiento.
  - Indicador a la derecha: `chevron-down`.
- **Tarjeta de ejecución** (expandida):
  - **Pregunta** completa.
  - **Respuesta completa del chatbot** en `type.body.m`, interlineado 22 px, fondo `color.bg.canvas`, radio `radius.m`, relleno 16 px, alto máximo 360 px con desplazamiento interno. **Marca del brief resaltada**: fondo `color.brand.bg`, subrayado 2 px `color.brand.fill`, peso 600. Otras marcas evaluadas: subrayado 1 px `color.rest.fill`. El fragmento evaluado (campo `fragmento`) lleva además un corchete lateral de 3 px `color.brand.fill`.
  - **Evaluación** (tabla de 2 columnas, `type.body.s`): Aparece · Posición · Peso de posición (0-3) · Tipo de mención · Fuerza (−1 a 3) · Sentimiento · Tipo de fuente · Calidad de fuente · Desconocimiento · Juez («reglas», «llm», «ensemble», «humano») · Confianza del juez · Discrepancia (si es sí: chip aviso «Reglas y LLM no coinciden»).
  - **Fuentes citadas**: lista de dominios en mono con `link-2` y su tipo: p. ej. «comparaclinicas.example · Directorio / comparador». Los dominios de la demo son ficticios y no enlazan a ningún sitio: se muestran como texto, sin hipervínculo, con tooltip «Dominio ficticio del kit».
  - **Metadatos**: fecha de ejecución, familia de prompt, intención (fase del embudo), instanciación.
- **Ejemplo con datos de la demo** (H1, Barcelona): cabecera «Aparición espontánea · Clínica Alborada Visión · Barcelona», origen «T4 · n = 24», valor «4,2 %», ejecución de ejemplo «EJ-0406». Texto de la pregunta y de la respuesta: [dato pendiente], se leen de `evaluaciones.parquet` y del corpus de ejecuciones.
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Cargando | Cabecera real + 4 tarjetas esqueleto |
| Vacío por filtros | «Ninguna ejecución cumple estos filtros.» + «Quitar filtros» |
| Sin IDs (métrica sin evidencias) | «Esta cifra no tiene ejecuciones asociadas en los datos.» + chip error; se registra como incidencia de trazabilidad |
| Error | «No se pudieron cargar las respuestas.» + «Reintentar» |
| n bajo | Banda ámbar bajo el resumen: «Muestra pequeña (n = {n}). Una sola respuesta cambia la cifra en {100/n} puntos.» |
| Degradado | Si las evaluaciones vienen del juez por reglas por fallo del LLM: chip «Evaluado con reglas» en cada tarjeta |

- **Comportamiento**: 1 clic desde cualquier cifra abre el panel con la lista; 1 clic más expande la respuesta (2 clics en total). Si la métrica tiene una sola ejecución, se abre ya expandida. El panel respeta el conmutador de ámbito. Atajos dentro del panel: J/K siguiente/anterior ejecución (solo con foco en la lista), Intro expandir, Esc cerrar.
- **Accesibilidad**: lista de artículos; cada tarjeta es un disclosure con nombre «Ejecución EJ-0406, Perplexity, repetición 2, aparece en posición 3»; el resaltado de la marca usa además el elemento semántico de texto marcado para que los lectores lo anuncien.

#### 4.B.6 Tarjeta de hallazgo (problema / fortaleza) **[Imprescindible]**

- **Anatomía**:
  1. Franja lateral izquierda 6 px (`color.problem.fill` o `color.strength.fill`).
  2. Cabecera: ID en mono («H1») · chip de tipo («Problema» con `trending-down` / «Fortaleza» con `trending-up`) · chip de categoría (geografía, motor…) · a la derecha, estado de aprobación.
  3. Título `type.h3`.
  4. Cifra principal (tarjeta de cifra compacta) a la izquierda + descripción `type.body.m` a la derecha.
  5. Fila de metadatos: n · fase del embudo (`filter`) · motores (chips) · «Impacto alto» · «Confianza media».
  6. Contraste de hipótesis (si el hallazgo confirma o refuta una hipótesis del cliente).
  7. Evidencias desplegables: «Ver 2 evidencias» → lista de evidencias con métrica, valor, n, tabla y botón «Abrir respuestas».
  8. Pie: marca de origen «Calculado» (la descripción la redacta una plantilla de código según `schemas.py`) · acciones «Descartar» (fantasma) y «Aprobar» (secundario con `check`).
- **Medidas**: ancho completo de la columna principal (8 columnas, 744 px); alto contraído 232 px; relleno 24 px; radio `radius.l`.
- **Tokens**: fortaleza: franja `color.strength.fill`, chip `color.strength`, fondo de cabecera `color.strength.bg` 40 px; problema: franja `color.problem.fill`, chip `color.problem`, fondo de cabecera `color.problem.bg`.
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Propuesto (por defecto) | Botones «Descartar» y «Aprobar» visibles |
| Aprobado | Borde `border.human`, chip «Aprobado · {iniciales}», botón cambia a «Quitar aprobación» |
| Descartado | Opacidad de contenido 55 %, título tachado, chip neutro «Descartado», botón «Recuperar». Pasa al final de la lista |
| Hover | `elevation.2` |
| Foco | Anillo genérico |
| Evidencias abiertas | La sección 7 se despliega (`motion.base`) |
| Cargando | Esqueleto con franja gris |
| Confianza baja | Chip «Confianza baja» en `color.warning` y texto «Revisa las evidencias antes de aprobar.» |

- **Comportamiento**: al descartar, aparece un campo opcional «Motivo (opcional)» de una línea; se guarda en el registro de aprobaciones. Atajos con foco en la tarjeta: A aprobar, D descartar, E abrir evidencias (activos solo con foco dentro del componente, cumple 2.1.4).
- **Accesibilidad**: artículo con encabezado; el tipo «Problema»/«Fortaleza» está en texto, no solo en color; botones con nombre completo («Aprobar H2»).

#### 4.B.7 Contraste de hipótesis **[Imprescindible]**

- **Anatomía**: (1) icono `flask-conical` · (2) sobretítulo «HIPÓTESIS DEL CLIENTE» · (3) cita entre comillas españolas en `type.body.l` cursiva de Source Serif 4 · (4) veredicto (chip grande 28 px) · (5) explicación de una línea · (6) enlace a los hallazgos que la sustentan.
- **Medidas**: bloque de 100 % de ancho; relleno 16 px; fondo `color.bg.sunken`; radio `radius.m`.
- **Variantes de veredicto**:

| Veredicto | Icono | Chip | Uso |
|---|---|---|---|
| Confirmada | `circle-check` | fondo `color.code.bg`, texto `color.code.fg`, «Confirmada por los datos» | La hipótesis coincide con los datos |
| Refutada | `circle-x` | fondo `color.code.bg`, texto `color.code.fg`, «Refutada por los datos» | Los datos la contradicen |
| Matizada | `circle-dot` | igual, «Matizada» | Parte cierta, parte no |
| Sin datos | `circle-dashed` | neutro, «Sin datos suficientes» | |

Nota: el veredicto usa el color de «calculado» (no verde ni rojo) porque confirmar o refutar no es bueno ni malo en sí: lo que importa es la conclusión, que se escribe en el texto.

- **Contenido de la demo**:
  - «Con tan buenas reseñas deberíamos salir recomendados.» → **Refutada por los datos** · «Cuando la nombran, solo un 9,3 % de las menciones son negativas (n = 108). Pero solo la recomiendan activamente en un 6,7 % de las respuestas espontáneas (n = 240). Las reseñas no son el freno: el freno es que no la descubren.» · «Ver H2 y H5».
  - «En Barcelona nadie nos encuentra.» → **Confirmada por los datos** · «Aparece en un 4,2 % de las respuestas sobre Barcelona (n = 24), frente a un 54,2 % en Madrid (n = 24).» · «Ver H1».
- **Accesibilidad**: cita marcada como cita; veredicto en texto.

#### 4.B.8 Barra de punto de control (checkpoint de aprobación) **[Imprescindible]**

- **Anatomía**: (1) sobretítulo «PUNTO DE CONTROL {k} DE 4» · (2) nombre del CP · (3) resumen de lo que se aprueba («7 hallazgos: 6 aprobados, 1 descartado») · (4) avisos pendientes (chips) · (5) registro («Aprobado por {nombre} el {fecha}, {hora}» cuando ya está aprobado) · (6) acción secundaria «Volver a {paso anterior}» · (7) acción principal «Aprobar {objeto}» variante Aprobar, tamaño L, con atajo «Ctrl ↵».
- **Medidas**: fija en la parte inferior del área de contenido, alto 72 px, ancho del área de contenido, relleno 24 px horizontal; `elevation.2`; borde superior `border.thin`; fondo `color.bg.surface`.
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Esperando aprobación | Sobretítulo en `color.warning.fg` con `user-round-search`; botón principal activo |
| Con avisos no bloqueantes | Chips de aviso visibles («2 avisos»); el botón sigue activo; al pulsar, popover de confirmación «Hay 2 avisos sin resolver. ¿Aprobar igualmente?» con «Revisar avisos» y «Aprobar igualmente» |
| Con bloqueo | Botón deshabilitado; texto «Resuelve 1 conflicto para aprobar» en `color.error.fg`; clic en el texto lleva al conflicto |
| Aprobando | Botón en estado cargando «Aprobando…» |
| Aprobado | Fondo `color.human.bg`, borde superior doble `border.human`, texto «Aprobado por {nombre} · {fecha} · {hora}», botón principal cambia a «Continuar a {siguiente paso}» (principal tinta), secundario «Editar» |
| Desactualizado | Fondo `color.warning.bg`, texto «Este paso cambió después de aprobarse. Vuelve a aprobarlo.», botón «Aprobar de nuevo» |

- **Comportamiento**: aprobar = 1 clic (o Ctrl/⌘ + Intro); registra persona, fecha, hora, CP y resumen; muestra toast «{CP} aprobado. Calculando {siguiente paso}…» con «Deshacer» durante 10 s; navega automáticamente al siguiente paso cuando está listo (en mock, al instante).
- **Accesibilidad**: región con nombre «Punto de control»; el atajo funciona desde cualquier parte de la pantalla salvo dentro de campos de texto multilínea.

#### 4.B.9 Sello del revisor **[Imprescindible]**

- **Anatomía**: (1) icono grande 32 px (`shield-check` en éxito, `shield-alert` con incidencias) · (2) sobretítulo «REVISIÓN AUTOMÁTICA» · (3) tres contadores en fila separados por «·» · (4) estado («Lista para enviar» / «Bloqueada: {k} incidencias») · (5) enlace «Ver detalle de la revisión» · (6) marca de origen «Calculado».
- **Contenido de la demo**: «578/578 cifras trazables · 0 entidades no verificadas · 0 incidencias normativas» · «Lista para enviar».
- **Medidas**: ancho completo de la cabecera de la Propuesta; alto 96 px; relleno 20 px; contadores en `type.display.m` (578/578) y `type.body.m` (etiquetas); radio `radius.l`; borde doble.
- **Variantes y tokens**:

| Variante | Fondo | Borde | Texto de estado |
|---|---|---|---|
| Sin incidencias | `color.success.bg` | `color.success.border` doble | «Lista para enviar» |
| Con incidencias no bloqueantes | `color.warning.bg` | `color.warning.border` | «Revisa {k} avisos antes de enviar» |
| Con incidencias bloqueantes | `color.error.bg` | `color.error.border` | «Bloqueada: {k} incidencias que corregir» |
| Revisando | `color.bg.sunken` | `border.thin` | «Revisando cifras y textos…» con anillo |
| Degradado | `color.degraded.bg` | `border.degraded` | «Revisión hecha solo con reglas (sin LLM)» |

- **Comportamiento**: cada contador es clicable y filtra la lista de incidencias o abre el anexo de trazabilidad.
- **Accesibilidad**: región de estado; los tres contadores se leen como lista.

#### 4.B.10 Incidencia del revisor **[Imprescindible]**

- **Anatomía**: (1) chip de tipo (según enumerado `Incidencia.tipo`: «Cifra no trazable», «Promesa de resultado», «Comparativa denigratoria», «Tono», «Presupuesto», «Acción sin hallazgo», «Campo vacío») · (2) chip «Bloqueante» (`color.error`) o «Aviso» (`color.warning`) · (3) texto marcado: fragmento con la parte problemática resaltada (fondo `color.error.bg`, subrayado ondulado 1,5 px `color.error.fg`) · (4) «Sugerencia» con el texto propuesto (fondo `color.success.bg`) · (5) acciones: «Aplicar sugerencia» (secundario), «Editar a mano» (fantasma), «Ir al texto» (fantasma).
- **Medidas**: tarjeta de ancho completo; relleno 16 px; radio `radius.m`; franja izquierda 4 px del color de severidad.
- **Ejemplo ilustrativo del estado** (la demo tiene 0 incidencias; este ejemplo solo sirve para diseñar el estado): tipo «Promesa de resultado» · texto marcado «…con resultados **garantizados** en 12 meses…» · sugerencia «…con rangos objetivo a 12 meses, sin garantía de resultado…».
- **Estados**: abierta · resuelta (opacidad 60 %, chip «Resuelta», check) · aplicando (cargando).
- **Accesibilidad**: el fragmento marcado se anuncia como «texto con incidencia»; los cambios se anuncian en región en vivo.

#### 4.B.11 Tabla de acciones editable **[Imprescindible]**

- **Anatomía**: (1) barra de herramientas: búsqueda, filtros (fase, responsable, palanca), contador «14 acciones · 24.300 €», botón «Añadir acción» · (2) tabla con columnas · (3) fila expandible con detalle · (4) barra de cambios sin guardar.
- **Columnas** (en este orden, ancho a 1440): ID (56, mono) · Acción (title, 320) · Fase (64, chip «F0»…«F3») · Hallazgos (96, chips «H7» clicables) · Responsable (148, selector en celda) · Esfuerzo (64, chip talla) · Impacto (64, chip talla) · Inicio (64, «S1») · Plazo (64, «3 sem.») · Coste (96, «2.000 €» derecha) · Estado de validación (40, icono).
- **Detalle de fila** (expandida, 2 columnas): Descripción (área de texto) · Palanca (selector con los 7 valores de `Palanca`) · Fase del embudo (multiselección) · Motores (multiselección) · Ciudades (multiselección) · Dependencias (multiselección de IDs) · Entregables (lista editable) · KPI (campo) · marca de origen.
- **Etiquetas de enumerados** (texto en pantalla):

| Valor interno | Texto en pantalla |
|---|---|
| `autoridad_terceros` | Autoridad en terceros |
| `entidad_datos_estructurados` | Entidad y datos estructurados |
| `contenido` | Contenido |
| `reputacion_resenas` | Reputación y reseñas |
| `comunidades` | Comunidades |
| `tecnico` | Técnico |
| `medicion` | Medición |
| `cliente_marketing` | Cliente · Marketing |
| `cliente_comunicacion` | Cliente · Comunicación |
| `cliente_medico` | Cliente · Equipo médico |
| `agencia` | Agencia |
| `tercero` | Tercero |

- **Medidas**: fila 48 px; fila expandida ≈ 360 px; celdas editables con borde al pasar.
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Lectura | Celdas planas |
| Hover en celda editable | Borde 1 px `color.border.strong` y `pencil` 14 px |
| Edición | Celda convertida en campo/selector S con foco |
| Celda editada sin guardar | Punto ámbar 6 px en la esquina superior izquierda de la celda |
| Fila con conflicto | Fondo `color.error.bg`, icono `octagon-x` en la columna de validación, tooltip con el conflicto |
| Fila con aviso | Icono `triangle-alert` `color.warning.fg` |
| Validando | Icono `loader-circle` en la columna de validación |
| Vacío | «No hay acciones con estos filtros.» |

- **Barra de cambios sin guardar** (aparece sobre la barra de CP, 56 px, fondo `color.warning.bg`): «{k} cambios sin guardar» · «Descartar» · «Guardar y revalidar» (principal). Mientras haya cambios sin guardar, el botón «Aprobar plan» está deshabilitado con el texto «Guarda los cambios para aprobar».
- **Comportamiento**: Intro o doble clic edita; Tab pasa a la siguiente celda editable; Esc cancela la edición de la celda; al guardar, el sistema revalida presupuesto, dependencias y capacidad, y pinta los avisos en contexto (fila, Gantt, barra de presupuesto, carga).
- **Accesibilidad**: patrón de rejilla editable; cada celda anuncia «Coste de A6, 2.750 euros, editable».

#### 4.B.12 Gantt **[Imprescindible]**

- **Anatomía**: (1) cabecera de semanas S1-S52 con marcas cada 4 semanas y etiquetas «S1, S5, S9…» · (2) bandas de fase de fondo · (3) columna izquierda de 240 px con ID y título corto · (4) barra de acción · (5) flechas de dependencia · (6) hitos de re-medición (rombos en S12, S24, S36 y S48) con línea vertical discontinua · (7) línea «Hoy» opcional.
- **Medidas**: fila 32 px; barra 20 px de alto, radio `radius.s`; ancho de semana = (ancho disponible − 240) / 52 ≈ 15 px a 1440 (ancho total del gráfico 1064 px); rombo 12 px.
- **Codificación**:
  - Color de barra por **responsable** en escala de grises con patrón (no se gastan colores reservados): Agencia = `color.text.primary` sólido; Cliente · Marketing = `color.text.secondary` sólido; Cliente · Comunicación = `color.text.secondary` con rayado 45°; Cliente · Equipo médico = `color.text.tertiary` con punteado; Tercero = contorno 1,5 px sin relleno. Leyenda directa encima del gráfico.
  - Etiqueta dentro de la barra si cabe (ID en blanco, mono 12 px); si no, a la derecha en `color.text.primary`.
  - Bandas de fase: F0 S1-S4, F1 S5-S10, F2 S11-S36, F3 S12-S48 (F3 se solapa con F2; se dibuja como franja inferior de 6 px en `color.bg.sunken` con etiqueta «F3 · Medición» para no tapar F2). F0, F1, F2 alternan `color.bg.surface` y `color.bg.canvas`, con nombre de fase en `type.overline` en la parte superior.
  - Dependencias: línea de 1,5 px `color.text.tertiary` con codo y punta de flecha de 6 px, del final de la predecesora al inicio de la sucesora.
- **Datos de la demo** (de `plan.json`): A1 S1-S3 · A2 S1-S2 · A3 S2-S4 · A4 S4-S5 (depende de A1) · A5 S2-S3 · A6 S5-S8 (A1) · A7 S3-S5 · A8 S5-S8 (A1) · A9 S6-S8 · A10 S7-S9 · A11 S11-S15 (A8) · A12 S11-S22 (A6, A10) · A13 S12-S19 (A3) · A14 S12-S47 (A1, A6). Hitos S12, S24, S36, S48 con etiqueta «Re-medición 1…4» y en S24 además «Revisión de mitad (mes 6)».
- **Estados**: hover en barra: tooltip («A6 · Páginas locales en Barcelona… · S5–S8 · 4 semanas · Agencia · 2.750 € · Depende de A1»); seleccionada: borde 2 px `color.focus.ring`; **conflicto de dependencia**: barra con borde 2 px `color.error.border`, flecha en `color.error.fg` y etiqueta flotante «Empieza antes de que termine A1»; arrastre (opcional **[Recortable]**): mover la barra cambia «Inicio» en la tabla; sin arrastre, la edición se hace en la tabla.
- **Accesibilidad**: alternativa en tabla (la tabla de acciones); cada barra es un elemento enfocable con nombre «A6, semanas 5 a 8, depende de A1».

#### 4.B.13 Matriz esfuerzo / impacto **[Deseable]**

- **Anatomía**: rejilla 3×3 · eje X «Esfuerzo» (S, M, L de izquierda a derecha) · eje Y «Impacto» (S, M, L de abajo arriba) · chips de acción en cada celda · etiquetas de cuadrante.
- **Medidas**: 360 × 360 px (celdas de 112 px con 8 px de separación); chips S de 20 px con ID mono.
- **Cuadrantes** (texto en `type.caption` en la esquina de cada celda): esquina impacto L / esfuerzo S = «Victorias rápidas»; impacto L / esfuerzo L = «Apuestas de fondo»; impacto S / esfuerzo L = «Revisar si compensa»; resto sin etiqueta.
- **Datos de la demo**: Impacto L · Esfuerzo S: A2, A5, A9, A10, A14 · Impacto L · Esfuerzo M: A1, A6, A8, A13 · Impacto L · Esfuerzo L: A12 · Impacto M · Esfuerzo S: A3, A4, A7 · Impacto M · Esfuerzo M: A11 · el resto de celdas vacías.
- **Tokens**: celdas `color.bg.canvas` con borde `color.border.subtle`; celda «Victorias rápidas» con fondo `color.bg.sunken`; chips en estilo neutro; chip seleccionado con fondo `color.bg.inverse`.
- **Estados**: hover en chip resalta la misma acción en la tabla y en el Gantt (fondo `color.bg.sunken` en la fila); clic selecciona y desplaza la tabla a la fila; celda vacía sin texto.
- **Accesibilidad**: tabla 3×3 con cabeceras; alternativa textual: «Victorias rápidas: A2, A5, A9, A10, A14».

#### 4.B.14 Barra de presupuesto **[Imprescindible]**

- **Anatomía**: (1) cifra total `type.display.m` («24.300 €») · (2) texto de contexto («dentro del rango del brief: 18.000 € – 27.000 €») · (3) pista de escala 0 – 30.000 € · (4) banda del rango del brief · (5) barra apilada por fase · (6) marcador del total · (7) desglose por responsable en tabla compacta.
- **Medidas**: ancho 100 % de su tarjeta (6 columnas, 552 px); pista 24 px de alto; banda del rango 36 px (sobresale 6 px arriba y abajo).
- **Codificación**: banda del rango en `color.bg.sunken` con bordes verticales de 2 px `color.text.secondary` en 18.000 € y 27.000 € y etiquetas encima; segmentos por fase en escala de tinta: F0 `color.seq.1`, F1 `color.seq.2`, F2 `color.seq.3`, F3 `color.seq.4`, separados 2 px; marcador del total: línea vertical 2 px `color.text.primary` con etiqueta «24.300 €».
- **Datos de la demo**: F0 6.300 € · F1 7.000 € · F2 8.000 € · F3 3.000 € = 24.300 €. Por responsable: Agencia 17.050 € (8 acciones, 70,2 %) · Cliente · Marketing 3.050 € (3; 12,6 %) · Cliente · Comunicación 2.950 € (2; 12,1 %) · Cliente · Equipo médico 1.250 € (1; 5,1 %).
- **Estados**:

| Estado | Tratamiento |
|---|---|
| Dentro del rango | Texto «Dentro del rango del brief» con `check` en `color.success.fg` |
| Por debajo del mínimo | Aviso «{x} € por debajo del mínimo del brief» en `color.warning.fg` |
| Por encima del máximo | Conflicto: el tramo sobrante de la barra se pinta rayado `color.error.fill`; texto «Supera el máximo del brief en {x} €» en `color.error.fg`; bloquea CP3 |
| Recalculando | Cifra con esqueleto 400 ms |

- **Accesibilidad**: texto equivalente: «Total 24.300 euros. Rango del brief de 18.000 a 27.000 euros. Dentro del rango.»

#### 4.B.15 Gráfico de carga del equipo del cliente **[Deseable]**

- **Anatomía**: columnas semanales S1-S52 · línea horizontal de capacidad · zona de exceso · etiqueta de capacidad.
- **Datos**: la capacidad sale del brief y de los supuestos del plan: «1 responsable de marketing + 1 persona de comunicación a media jornada» y «hasta 18 horas semanales combinadas». Las horas por acción **no existen** en `plan.json`: [dato pendiente: horas semanales por acción del cliente]. Mientras falten, el gráfico usa el modo de reserva «Acciones simultáneas del cliente por semana» (calculable desde `plan.json`), con capacidad expresada como texto y sin línea numérica.
- **Recuento calculable (modo de reserva)** a partir de las acciones con responsable del cliente: A3 (S2-S4, Marketing), A5 (S2-S3, Comunicación), A7 (S3-S5, Marketing), A9 (S6-S8, Marketing), A10 (S7-S9, Equipo médico), A13 (S12-S19, Comunicación). Pico: 3 acciones simultáneas en S3.
- **Medidas**: alto 160 px; columnas de ancho = semana del Gantt (alineado con él cuando se muestran juntos); columna apilada por responsable con el mismo patrón que el Gantt.
- **Estados**: dentro de capacidad (columnas en tinta); exceso (la parte por encima de la línea se pinta `color.error.fill` rayado y aparece el aviso «S{x}: {h} h previstas para {c} h de capacidad»); sin horas («Faltan las horas por acción. Mostrando acciones simultáneas.» en `type.caption` con `info`).
- **Accesibilidad**: tabla alternativa semana a semana.

#### 4.B.16 Simulador what-if **[Deseable]**

- **Anatomía**: (1) cabecera con icono `sliders-horizontal`, título «Simulador» y chip permanente «Escenario hipotético, no una predicción» (fondo `color.warning.bg`) · (2) grupo «Aparición espontánea por ciudad»: deslizadores Madrid y Barcelona · (3) grupo «Aparición espontánea por motor»: ChatGPT, Gemini, Perplexity, Claude · (4) «Fuerza media de recomendación» (escala −1 a 3) · (5) «% de fuentes de calidad» · (6) resultado · (7) acciones «Restablecer» y «Usar como objetivo».
- **Valores iniciales (hoy)**: Madrid 54,2 % · Barcelona 4,2 % · ChatGPT 18,3 % · Gemini 56,7 % · Perplexity 65,0 % · Claude 15,0 % · Fuerza media 0,62 (espontánea, T1) · Fuentes de autoridad (Ranking/institución + Medio) 31,3 % (T6).
- **Resultado**: dos bloques lado a lado: «Score» «27,97 → {simulado}» y «Puesto» «7.º → {simulado}.º de 10». La flecha y el valor simulado se pintan en `color.text.primary`; el valor actual en `color.text.tertiary`. El cálculo del score simulado lo hace el backend con la misma fórmula del Score de Citación: [dato pendiente: endpoint o función de simulación]. Debajo: «Calculado con la fórmula del Score de Citación sobre los valores que has movido. No predice lo que harán los chatbots.»
- **Medidas**: tarjeta de 4 columnas (360 px) en la pantalla Plan, o modal M; cada deslizador 64 px de alto.
- **Estados**: valores sin tocar (resultado igual al actual, botón «Usar como objetivo» deshabilitado con tooltip «Mueve algún control para crear un escenario»); calculando (valor simulado con anillo, 200 ms de espera tras soltar); escenario por encima del rango objetivo del plan (aviso «Este escenario supera el rango objetivo del plan (40,0 – 48,0).»).
- **Comportamiento**: «Usar como objetivo» abre un modal: «¿Usar este escenario como objetivo?» · «Se guardará como rango objetivo del Score de Citación a 12 meses: {simulado − 4} – {simulado + 4}. Podrás editarlo.» [el margen del rango lo define el equipo: dato pendiente] · «Cancelar» · «Usar como objetivo». Tras aceptar, la fila de Objetivos se actualiza con marca «Editado por {iniciales}» y el plan se revalida.
- **Accesibilidad**: cada deslizador con valor actual anunciado; el resultado es región en vivo educada.

#### 4.B.17 Indicador de paso degradado **[Imprescindible]**

- **Anatomía**: (1) icono `split` · (2) texto · (3) enlace «Ver traza».
- **Variantes**: chip en el carril («Listo con reglas») · banda informativa bajo la cabecera de la pantalla afectada.
- **Texto de la banda**: «Este paso se completó con reglas porque el modelo de lenguaje no respondió. Los cálculos son correctos; los textos son más básicos. Ver traza.» Para mock: «Este paso se ejecutó en modo mock: los textos son de plantilla.».
- **Medidas**: banda 40 px de alto, relleno 12 px, `color.degraded.bg`, borde `border.degraded`, texto `color.degraded.fg`, radio `radius.m`.
- **Regla de tono**: no usa rojo ni ámbar; no bloquea; no aparece como toast.
- **Accesibilidad**: estado informativo (no alerta).

#### 4.B.18 Chip de rol de competencia **[Imprescindible]**

| Rol (`MarcaMercado.rol`) | Texto | Estilo |
|---|---|---|
| `marca_brief` | «Marca del brief» | `color.brand` tintado + `crosshair` |
| `lider` | «Líder» | `color.leader` sólido (texto blanco) |
| `competidor_directo` | «Competidor directo» | contorno 1,5 px `color.text.primary` |
| `referencia` | «Referencia» | contorno 1 px `color.border.strong` |
| `contexto` | «Contexto» | neutro (`color.bg.sunken`) |

#### 4.B.19 Aviso de discrepancia con el brief **[Imprescindible]**

- **Anatomía**: (1) icono `triangle-alert` 20 px · (2) titular corto `type.h3` · (3) frase con cifra y origen `type.body.m` · (4) línea de origen mono · (5) acciones contextuales.
- **Medidas**: tarjeta de 6 columnas (552 px), alto 136 px, franja izquierda 4 px `color.warning.fill`, fondo `color.surface`.
- **Contenido de la demo**:
  1. «Vistalia Oftalmología no está en el brief» · «Aparece en el 41,2 % de las respuestas espontáneas y es competidor directo (red regional).» · «T1 · n = 240» · acciones «Ver respuestas» y «Mantener como competidor directo».
  2. «El líder real es Grupo Hospitalario Valdecruz» · «Aparece en el 90,8 % de las respuestas espontáneas (score 75,02). El brief trataba como referencia a Instituto Oftálmico Tramuntana (68,8 %, score 51,70).» · «T1 · n = 240» · acciones «Ver respuestas» y «Confirmar como líder».
  3. «5 marcas más con aparición ≥ 30 % que el brief no nombra» · «Oftalmos Centro (60,0 %), Clínica del Ojo Cervantes (44,2 %), Instituto Ocular Santa Eulalia (42,5 %), Visionar Clínicas (33,3 %), Centro Lasik Península (31,2 %).» · «T1 · n = 240» · acción «Ver en la tabla».
- **Estados**: abierto · revisado (al pulsar una acción: chip «Revisado · {iniciales}», franja pasa a `color.human.fill`) · descartado.

#### 4.B.20 Selector de proveedor con coste estimado **[Imprescindible]**

- **Anatomía**: (1) etiqueta «Proveedor de IA» · (2) control segmentado de 3 opciones: «mock», «anthropic», «openai» (los valores técnicos se muestran tal cual en mono, con nombre amable debajo: «Sin IA (plantillas)», «Anthropic», «OpenAI») · (3) bloque de estimación: «Llamadas al modelo», «Tokens estimados», «Coste estimado» · (4) nota.
- **Datos**: mock = 0 llamadas, 0 tokens, 0 €. anthropic / openai = [dato pendiente: llamadas, tokens y € estimados por el backend antes de lanzar] y modelo concreto [dato pendiente].
- **Medidas**: 100 % de ancho del formulario; bloque de estimación en 3 columnas, cifras `type.h2`.
- **Estados**: estimando (esqueleto); sin clave configurada («No hay clave de API para {proveedor}. Usa mock o configura la clave.» y opción deshabilitada); coste alto (aviso si supera [umbral pendiente] €).
- **Nota fija**: «La estimación es orientativa. El coste real aparece en Calidad y trazas al terminar.»

#### 4.B.21 Chip de ámbito y origen en gráficos **[Imprescindible]**

Toda visualización y tabla del Diagnóstico lleva en la esquina superior derecha de su tarjeta: chip de ámbito («Espontánea» o «Asistida», tintado del color del modo) + origen mono («T2 · n = 60 por celda»). Es la garantía de que espontánea y asistida nunca se confunden, ni en capturas.

---

## 5. Visualizaciones de datos

### 5.1 Reglas generales para todos los gráficos

1. **Título que afirma.** Cada gráfico tiene un título descriptivo neutro (`type.h3`) y, debajo, una línea de lectura en `type.body.m` secundaria que dice qué muestra para la marca del brief, calculada por código a partir de los datos. Ejemplo: título «Ranking por Score de Citación», lectura «Clínica Alborada Visión ocupa el 7.º puesto de 10 con 27,97». La lectura nunca valora («mal», «el peor»): describe.
2. **Un color de énfasis.** Marca del brief en `color.brand.fill`; líder en `color.leader.fill`; resto en `color.rest.fill`. Ningún otro color categórico. Los motores, ciudades y fases se distinguen por posición y etiqueta, no por color.
3. **Etiquetas directas, leyenda mínima.** Los valores se escriben junto a la marca gráfica (`type.chart.label`). La leyenda solo aparece cuando hay más de una serie y se coloca encima del gráfico, alineada a la izquierda, en línea con el título.
4. **La marca del brief siempre se reconoce sin color.** Nombre en peso 600 con icono `crosshair`, etiqueta directa en `type.chart.label.brand` y, en barras, borde de 2 px `color.brand.border`. El líder lleva siempre la etiqueta «Líder» en texto.
5. **Origen y ámbito visibles.** Chip de ámbito y línea de origen («T1 · n = 240 por marca») en cada tarjeta de gráfico (componente 4.B.21).
6. **n bajo (n < 15).** La marca gráfica se rellena con rayado 45° (líneas de 1 px cada 6 px sobre su color al 50 %), el valor lleva el chip «n bajo» y el tooltip añade la frase «Muestra pequeña (n = {n}). Interprétalo con cautela.». Nunca se oculta el dato.
7. **Escalas honestas.** Ejes de porcentaje siempre de 0 a 100 %. Scores de 0 a 100. Las barras empiezan en 0. Sin ejes cortados, sin 3D, sin tartas.
8. **Clic = evidencias.** Toda marca gráfica (barra, punto, celda, segmento) abre el visor de evidencias filtrado por su métrica y ámbito (1 clic). El cursor es mano y el elemento tiene foco de teclado.
9. **Tooltip uniforme.** Estructura fija: línea 1, nombre de la marca (y dimensión) en `type.body.m.strong`; línea 2, valor principal; línea 3, valores secundarios; línea 4, origen en mono «{tabla} · n = {n} · {ámbito}»; línea 5, «Clic para ver las respuestas». Fondo `color.bg.inverse`.
10. **Rejilla discreta.** Líneas de rejilla horizontales de 1 px `color.border.subtle` cada 25 %; sin rejilla vertical salvo en el Gantt.
11. **Tipografía de proyector.** A 1920, texto de ejes 15 px y etiquetas 16 px (escala «1920»). Ninguna etiqueta por debajo de 13 px a 1440.
12. **Vista de tabla.** Cada tarjeta de gráfico tiene, junto al origen, el conmutador segmentado «Gráfico / Tabla». La tabla muestra exactamente los mismos datos con las mismas cifras clicables. Es también la alternativa accesible.
13. **Orden estable.** Las marcas se ordenan siempre por score espontáneo descendente (orden de T1), también en asistida, para que el ojo encuentre cada marca en el mismo sitio al conmutar. Excepción: el ranking asistido, que ordena por su propio score y lo indica en el subtítulo.
14. **Estados comunes**: cargando (esqueleto con la silueta del gráfico); vacío («No hay datos para esta combinación.»); error («No se pudo cargar {tabla}.» + «Reintentar»); no aplica en el ámbito (ver cada gráfico); dato pendiente (marca gráfica sustituida por «—» y chip neutro «Pendiente»).

### 5.2 Desglose del Score de Citación

- **Tipo**: barra horizontal segmentada de 4 tramos con pista de máximos (variante de barra de progreso apilada). Por qué: el score es una suma de 4 componentes con máximos distintos (30 + 20 + 30 + 20 = 100); una barra única muestra a la vez cuánto aporta cada parte y cuánto le falta.
- **Eje**: horizontal de 0 a 100, sin etiquetas de eje; cada tramo tiene su pista de fondo del ancho de su máximo.
- **Orden**: Aparición (máx. 30) · Posición (máx. 20) · Fuerza de recomendación (máx. 30) · Calidad de fuente (máx. 20).
- **Colores**: relleno de cada tramo `color.brand.fill`; pista restante `color.bg.sunken`; separación de 2 px entre tramos.
- **Etiquetas directas**: debajo de cada tramo, nombre y valor «Aparición · [dato pendiente] / 30».
- **Leyenda**: ninguna.
- **Tooltip**: «Aparición · {v} de 30 puntos» / «Calculado sobre la tasa de aparición (38,8 %)» / «T1 · n = 240 · Espontánea».
- **Clic**: abre el visor con todas las ejecuciones del ámbito para la marca (métrica `score_espontaneo[marca=…]`).
- **n bajo**: no aplica (n = 240).
- **Con datos reales**: total 27,97 de 100. Valores por componente: [dato pendiente: el backend debe exponer los 4 sumandos en `metrics.json`]. Mientras falten, la barra se muestra como un único tramo de 27,97 con el texto «Desglose pendiente».
- **Asistida**: igual, con total 73,97.

### 5.3 Ranking de las 10 marcas por score

- **Tipo**: barras horizontales ordenadas, con una columna adicional de punto para la aparición. Por qué: comparar 10 valores con nombres largos se lee mejor en horizontal; el orden muestra el puesto sin necesidad de leer números.
- **Ejes**: Y = marcas (etiqueta a la izquierda, 240 px, con número de puesto «7»); X = Score de Citación 0-100, rejilla en 25, 50, 75. Columna derecha de 120 px «Aparición»: valor en texto con una minibarra de 64 px.
- **Orden**: score descendente.
- **Colores**: Valdecruz `color.leader.fill`; Alborada `color.brand.fill` con borde 2 px `color.brand.border`; el resto `color.rest.fill`. Fila de Alborada con fondo `color.brand.bg` a todo el ancho.
- **Etiquetas directas**: score al final de cada barra («75,02»). Nombre de Alborada con `crosshair` y chip «Tu marca»; Valdecruz con chip «Líder».
- **Leyenda**: no necesaria (chips en las filas).
- **Tooltip**: «Clínica Alborada Visión» / «Score 27,97 · puesto 7.º de 10» / «Aparición 38,8 % · recomendación activa 6,7 % · posición media 3,05» / «T1 · n = 240 · Espontánea» / «Clic para ver las respuestas».
- **Clic**: visor con `score_espontaneo[marca={marca}]` (todas las ejecuciones espontáneas de la marca).
- **n bajo**: no aplica (n = 240).
- **Detalle que el diseño debe hacer visible**: Alborada (7.º, score 27,97) aparece en el 38,8 % de respuestas y Vistalia (8.º, 26,59) en el 41,2 %. El score no ordena igual que la aparición. La columna «Aparición» lo deja ver, y un tooltip en su cabecera explica: «El score combina aparición, posición, fuerza y fuente. Una marca puede aparecer más y puntuar menos.»
- **Cómo se ve con datos reales**:

```text
Ranking por Score de Citación                         [Espontánea] T1 · n = 240 por marca
Clínica Alborada Visión ocupa el 7.º puesto de 10 con 27,97
                                          0        25        50        75       100  Aparición
 1 Grupo Hospitalario Valdecruz [Líder]   ███████████████████████████████ 75,02   90,8 %
 2 Instituto Oftálmico Tramuntana         █████████████████████ 51,70             68,8 %
 3 Oftalmos Centro                        ████████████████ 40,70                  60,0 %
 4 Láser Nítida                           ███████████████ 37,50                   55,8 %
 5 Clínica del Ojo Cervantes              ███████████ 28,58                       44,2 %
 6 Instituto Ocular Santa Eulalia         ███████████ 28,04                       42,5 %
 7 ⌖ Clínica Alborada Visión [Tu marca]   ███████████ 27,97  (bermellón)          38,8 %
 8 Vistalia Oftalmología                  ██████████ 26,59                        41,2 %
 9 Visionar Clínicas                      ████████ 20,46                          33,3 %
10 Centro Lasik Península                 ████████ 19,39                          31,2 %
```

- **Asistida**: el gráfico pasa a «Ranking asistido por score» con las 5 marcas que tienen preguntas asistidas: 1 Valdecruz 82,99 (n = 72) · 2 Tramuntana 79,84 (n = 132) · 3 Alborada 73,97 (n = 108) · 4 Vistalia 68,67 (n = 108) · 5 Láser Nítida 67,36 (n = 108). Las otras 5 marcas aparecen al final en gris claro con «Sin preguntas asistidas». La columna derecha pasa a «Menciones negativas» (16,7 % · 5,3 % · 9,3 % · 25,9 % · 34,3 %). Subtítulo: «Ordenado por score asistido. Tu marca: 3.º de 5 con 73,97». Origen «T9 · n por marca indicado en cada fila».

### 5.4 Marca × motor

- **Tipo**: mapa de calor (tabla con celdas coloreadas y valor escrito). Por qué: 10 × 4 = 40 valores; el mapa de calor permite leer por fila (¿en qué motor falla mi marca?) y por columna (¿qué motor favorece al líder?) sin 40 barras.
- **Ejes**: filas = 10 marcas en orden T1; columnas = ChatGPT, Gemini, Perplexity, Claude (orden fijo alfabético de interfaz, igual en toda la aplicación). Columna final «Media».
- **Valor**: tasa de aparición en el ámbito activo (%). Conmutador secundario dentro de la tarjeta: «Aparición / Score».
- **Colores**: escala del mapa de calor (3.1.3). Fila de Alborada con borde exterior 2 px `color.brand.border` y nombre con `crosshair`. Fila de Valdecruz con nombre en 600 y chip «Líder».
- **Etiquetas directas**: valor dentro de cada celda (`type.chart.label`), con el color de texto que marca la escala.
- **Leyenda**: barra de escala horizontal de 7 tramos sobre el gráfico, con «0 %» y «100 %» en los extremos.
- **Medidas**: celda 120 × 40 px a 1440; 144 × 48 a 1920.
- **Tooltip**: «Clínica Alborada Visión · ChatGPT» / «Aparición 18,3 % · score 11,70» / «Posición media 4,91 · fuerza media 0,22» / «T2 · n = 60 · Espontánea» / «Clic para ver las respuestas».
- **Clic**: visor con `tasa_aparicion_espontanea[marca={m},motor={motor}]`.
- **n bajo**: cada celda tiene n = 60 en espontánea; en asistida, n por celda [dato pendiente]; si < 15, rayado y chip.
- **Con datos reales**: fila de Alborada: ChatGPT 18,3 % · Gemini 56,7 % · Perplexity 65,0 % · Claude 15,0 %. Resto de filas: [dato pendiente: T2 para las otras 9 marcas]. Lectura: «Tu marca aparece en el 65,0 % de respuestas de Perplexity y en el 15,0 % de Claude».
- **Asistida**: mismo gráfico con valores asistidos de T2 [dato pendiente]; filas sin preguntas asistidas en gris con «—».

### 5.5 Embudo: descubrimiento → comparación → validación → decisión

- **Tipo**: gráfico de líneas con puntos (pendiente) de 3 series sobre 4 fases. Por qué: la forma de «embudo» dibuja volumen, no tasa; aquí hay que comparar tasas de tres series en cuatro momentos, y una línea muestra de un vistazo dónde cae la marca y si el líder no cae.
- **Ejes**: X = 4 fases en orden del recorrido del paciente (Descubrimiento, Comparación, Validación, Decisión), con n de la marca bajo cada etiqueta en mono («n = 132»); Y = aparición 0-100 %.
- **Series**: Alborada (línea 3 px `color.brand.fill`, puntos de 8 px rellenos); Líder Valdecruz (línea 2 px `color.leader.fill`, puntos cuadrados 7 px); Media de competidores (línea 2 px discontinua `color.rest.fill`, puntos huecos 7 px). La forma del punto distingue las series sin color.
- **Etiquetas directas**: valor junto a cada punto de Alborada; nombre de cada serie al final de su línea, a la derecha («Tu marca», «Líder», «Media competidores»).
- **Leyenda**: no (etiquetas al final de línea).
- **Tooltip** (por fase, agrupa las 3 series): «Decisión» / «Tu marca 25,0 % · fuerza media 0,29» / «Líder 97,9 %» / «Media competidores [dato pendiente]» / «T3, T11 · n = 48 · Espontánea» / «Clic en un punto para ver las respuestas».
- **Clic**: en un punto, visor con `tasa_aparicion_espontanea[intencion={fase}]` de esa serie.
- **n bajo**: n mínimo de Alborada es 24 (Validación): no se marca. Si algún n < 15, el punto se dibuja hueco con rayado y chip.
- **Con datos reales** (`metrics.json`): Alborada Descubrimiento 44,7 % (n = 132) · Comparación 38,9 % (n = 36) · Validación 33,3 % (n = 24) · Decisión 25,0 % (n = 48). Líder: Decisión 97,9 % (n = 48, T11); resto de fases [dato pendiente]. Media de competidores: [dato pendiente]. Si una serie no tiene todos los puntos, se dibujan solo los existentes, sin unir huecos, con «Pendiente» en los que faltan. Lectura: «Tu marca baja del 44,7 % en Descubrimiento al 25,0 % en Decisión».
- **Asistida**: no aplica el embudo de descubrimiento con el mismo significado; se muestra con datos asistidos de T3 si existen [dato pendiente]. Si no existen: estado «No aplica» con texto «El embudo se mide con preguntas espontáneas. Cambia a Espontánea para verlo.» y botón «Cambiar a Espontánea».

### 5.6 Madrid frente a Barcelona

- **Tipo**: gráfico de mancuernas (dumbbell): dos puntos por marca unidos por una línea. Por qué: muestra a la vez los dos valores y la distancia entre ellos, que es el mensaje (la brecha geográfica). Se monta con una librería estándar como barras de rango con dos marcadores.
- **Ejes**: Y = marcas en orden T1; X = aparición espontánea 0-100 %.
- **Codificación**: Madrid = círculo relleno de 10 px; Barcelona = rombo relleno de 10 px; línea de unión 2 px. Colores por marca (brand, leader, rest), no por ciudad: la ciudad la dice la forma.
- **Etiquetas directas**: valores junto a cada marcador de Alborada («Madrid 54,2 %», «Barcelona 4,2 %») y la diferencia sobre la línea («−50,0 p. p.»). Leyenda de formas encima: «● Madrid  ◆ Barcelona».
- **Tooltip**: «Clínica Alborada Visión» / «Madrid 54,2 % (score 42,17) · Barcelona 4,2 % (score 3,39)» / «Diferencia −50,0 p. p.» / «T4 · n = 24 por ciudad · Espontánea» / «Clic en un punto para ver las respuestas».
- **Clic**: en un marcador, visor con `tasa_aparicion_espontanea[ciudad={ciudad}]`; para Barcelona incluye EJ-0406; para Madrid EJ-0193, EJ-0195, EJ-0202.
- **n bajo**: n = 24 por ciudad (≥ 15, no se marca), pero el subtítulo incluye «Muestra por ciudad: 24 respuestas» y el hallazgo H1 tiene confianza media. Si una ciudad baja de 15, rayado.
- **Con datos reales**: Alborada Madrid 54,2 % · Barcelona 4,2 %. Resto de marcas: [dato pendiente: T4 por marca]. Mientras falten, el gráfico se muestra solo con la fila de Alborada y una nota «Comparativa por marca pendiente».
- **Asistida**: no aplica (las preguntas por ciudad no nombran la marca). Estado «No aplica»: «Las preguntas por ciudad son siempre espontáneas. Cambia a Espontánea para verlas.».

### 5.7 Perfil de fuentes por marca

- **Tipo**: barras horizontales apiladas al 100 %, una por marca, con 7 segmentos ordenados por calidad. Por qué: interesa la composición (qué tipo de fuente respalda a cada marca) y compararla entre marcas; ordenar los segmentos de mayor a menor calidad hace que «más oscuro a la izquierda» signifique «mejor respaldo».
- **Ejes**: Y = marcas en orden T1; X = 0-100 % de las apariciones.
- **Segmentos** (de izquierda a derecha): Ranking / institución · Medio · Web propia · Directorio / comparador · Plataforma de reseñas · Red social / foro · Sin fuente. Colores: escala secuencial «Calidad de fuente» `color.seq.1` a `color.seq.7`. Separación de 2 px blanca. Línea vertical discontinua tras los dos primeros segmentos con la etiqueta «Fuentes de autoridad».
- **Fila de Alborada**: contorno 2 px `color.brand.border` alrededor de toda la barra y nombre con `crosshair`.
- **Etiquetas directas**: porcentaje dentro de cada segmento ≥ 8 %; los menores, solo en tooltip. A la derecha de cada barra, «Autoridad {x} %» y «n = {apariciones}».
- **Leyenda**: fila superior con los 7 tipos y su muestra de color, en el mismo orden que los segmentos.
- **Tooltip**: «Clínica Alborada Visión · Medio» / «31 apariciones · 15,4 % · calidad 0,90» / «T6 · n = 201 apariciones · Espontánea» / «Clic para ver las respuestas».
- **Clic**: visor con las ejecuciones de esa marca y tipo de fuente.
- **n bajo**: n son apariciones por marca; si una marca tiene < 15 apariciones, toda su barra se raya.
- **Con datos reales** (Alborada, n = 201): Ranking / institución 15,9 % (32) · Medio 15,4 % (31) · Web propia 20,9 % (42) · Directorio / comparador 20,4 % (41) · Plataforma de reseñas 14,4 % (29) · Red social / foro 6,5 % (13) · Sin fuente 6,5 % (13). Autoridad 31,3 %, calidad media 0,69. Valdecruz: autoridad 38,3 % (n = 290), resto de segmentos [dato pendiente]. Otras marcas: [dato pendiente: T6 por marca].
- **Limitación visible**: bajo el gráfico, nota fija en `type.caption` con `info`: «El tipo de fuente es el campo que el juez clasifica con menos acierto (78,2 % global). Úsalo para ver tendencias, no para decisiones finas. Ver Calidad.» con enlace a la pantalla 7.
- **Asistida**: mismo gráfico con datos asistidos de T6 [dato pendiente].

### 5.8 Consistencia entre repeticiones

- **Tipo**: barra horizontal apilada al 100 % de 3 segmentos por marca. Por qué: cada combinación pregunta × motor se repite 3 veces; la pregunta es qué parte de la presencia es estable y cuál es azar. Tres segmentos ordenados de más a menos estable se leen como una escala.
- **Ejes**: Y = marcas en orden T1; X = 0-100 % de las combinaciones pregunta × motor.
- **Segmentos**: Consolidada 3/3 (`color.seq.1`) · Azar 1-2/3 (`color.seq.4` con rayado 45°) · Ausente 0/3 (`color.bg.sunken` con borde `color.border.strong`).
- **Etiquetas directas**: porcentaje dentro de cada segmento; a la derecha, nada más.
- **Leyenda**: encima, con las tres muestras y su definición corta: «Consolidada: sale en las 3 repeticiones», «Azar: sale en 1 o 2», «Ausente: no sale en ninguna».
- **Tooltip**: «Clínica Alborada Visión · Azar» / «41,2 % de las combinaciones pregunta × motor» / «Sale en 1 o 2 de las 3 repeticiones» / «T{n} · n = [dato pendiente] combinaciones · Espontánea».
- **Clic**: visor con las ejecuciones de las combinaciones de ese segmento, agrupadas por combinación (3 tarjetas por grupo).
- **Con datos reales** (`metrics.json`): Alborada Consolidada 18,8 % · Azar 41,2 % · Ausente 40,0 % (complemento de los dos anteriores; el backend debe exponerlo explícitamente). Tabla de origen y n: [dato pendiente]. Otras marcas: [dato pendiente].
- **Asistida**: igual con datos asistidos si existen [dato pendiente]; si no, estado «No aplica».

### 5.9 Duelos 1 a 1 (solo asistida)

- **Tipo**: barras divergentes por duelo y motor: victorias de tu marca hacia la izquierda, del rival hacia la derecha, desde un eje central. Por qué: en un duelo importa quién gana y por cuánto; la divergencia lo muestra con la longitud y el lado.
- **Ejes**: Y = duelos agrupados por rival (grupo «vs Instituto Oftálmico Tramuntana», grupo «vs Grupo Hospitalario Valdecruz»), 4 filas por grupo (ChatGPT, Gemini, Perplexity, Claude); X = victorias de 0 a 6 a cada lado.
- **Colores**: izquierda `color.brand.fill`; derecha: `color.leader.fill` si el rival es el líder, `color.rest.fill` si no.
- **Etiquetas directas**: número de victorias en el extremo de cada barra; a la derecha de la fila, resultado en texto: «Gana Tramuntana», «Empate», «Gana Valdecruz».
- **Leyenda**: encima, «Victorias de tu marca ◀ | ▶ Victorias del rival».
- **Tooltip**: «Alborada vs Tramuntana · Claude» / «Alborada 1 · Tramuntana 5» / «Gana Instituto Oftálmico Tramuntana» / «T8 · n = 6 · Asistida · n bajo» / «Clic para ver las respuestas».
- **Clic**: visor con las 6 ejecuciones del duelo en ese motor.
- **n bajo**: **todas las filas tienen n = 6**: todas se dibujan rayadas, cada fila lleva chip «n bajo» y el subtítulo dice «Cada duelo se basa en 6 respuestas por motor. Úsalo como señal, no como resultado».
- **Con datos reales** (T8): vs Tramuntana: ChatGPT 2-4 · Gemini 3-3 · Perplexity 3-3 · Claude 1-5. vs Valdecruz: ChatGPT 1-5 · Gemini 2-4 · Perplexity 0-6 · Claude 1-5.
- **Espontánea**: no aplica. Estado: «Los duelos solo existen en preguntas asistidas, porque la pregunta nombra a las dos marcas.» + botón «Cambiar a Asistida».

### 5.10 Calidad de mención asistida **[Deseable]**

Gráfico complementario que solo aparece en asistida y sostiene H2 (fortaleza).

- **Tipo**: barras horizontales del % de menciones negativas por marca, con la fuerza media como valor secundario. Por qué: el hallazgo de fortaleza es una comparación de una sola métrica entre 5 marcas.
- **Ejes**: Y = 5 marcas con preguntas asistidas en orden T1; X = % de menciones negativas 0-100 % (escala completa, aunque los valores sean bajos, para no exagerar).
- **Colores**: Alborada `color.brand.fill`; Valdecruz `color.leader.fill`; resto `color.rest.fill`.
- **Etiquetas directas**: valor al final («9,3 %») y, a la derecha, «fuerza 1,21 · n = 108».
- **Tooltip**: «Láser Nítida» / «Menciones negativas 34,3 % · fuerza media 0,55» / «Objeción más repetida: “hay opiniones que advierten de poca continuidad en el seguimiento postoperatorio” (18)» / «T9 · n = 108 · Asistida».
- **Con datos reales** (T9): Valdecruz 16,7 % (fuerza 2,17, n = 72) · Tramuntana 5,3 % (1,69, n = 132) · Alborada 9,3 % (1,21, n = 108) · Vistalia 25,9 % (0,74, n = 108) · Láser Nítida 34,3 % (0,55, n = 108).
- **Regla normativa**: el gráfico muestra datos, sin adjetivos sobre competidores. El título es «Menciones negativas cuando se nombra la marca» y la lectura «Tu marca: 9,3 % de menciones negativas (n = 108)». No se escribe «peor que».
- **Clic**: visor con las ejecuciones asistidas negativas de esa marca.

---

## 6. Pantallas

Todas las pantallas comparten la estructura de 3.3: aviso de datos sintéticos (28 px), barra superior (56 px), carril «Recorrido» (248 px) y área de contenido con margen de 32 px. Los wireframes muestran solo el área de contenido salvo indicación. Medidas a 1440×900. Se presentan primero las pantallas 3, 4 y 5 (las de la demo) y después el resto.

Estructura común de cabecera de pantalla (fija al desplazar, 96 px salvo que se indique): sobretítulo `type.overline` con número de paso («PASO 3 DE 7») · título `type.h1` · subtítulo `type.body.m` secundario · acciones a la derecha.

---

### Pantalla 3 · Diagnóstico

**Objetivo.** Mostrar dónde está la marca frente al mercado en los chatbots y por qué, con cada cifra trazable.
**Pregunta del usuario.** «¿Cuánto me recomiendan los chatbots, frente a quién y dónde fallo?»

#### Wireframe 1440×900 (vista inicial, espontánea)

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=84
│ PASO 3 DE 7                                                   [Ver tabla T1…T12 ▾] [Continuar│
│ Diagnóstico                                                                    a hallazgos →]│
│ ÁMBITO DE LAS PREGUNTAS  ( ● Espontánea · n=240 por marca | ○ Asistida · n=108 tu marca )    │
│ Preguntas que no nombran ninguna clínica. Mide si el chatbot conoce y recomienda tu marca…   │
├══════════════════════════════════════════════════════════════════════════════════════════════┤ y=212 franja de modo 4 px
│ Resumen · Ranking · Motores · Embudo · Ciudades · Fuentes · Consistencia · Duelos  (índice)  │ y=216 (40 px)
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ Σ Clínica Alborada Visión ocupa el puesto 7 de 10 en respuestas espontáneas: aparece en el 38,8 % frente│ y=256 (56 px)
│   al 90,8 % del líder. Donde menos aparece: Barcelona (4,2 %) y Claude (15,0 %).              │
├───────────────────────────────┬──────────────────────┬─────────────────────┬─────────────────┤ y=328
│ Score de Citación  [Esp.]     │ Puesto               │ Aparición           │ Recomendación   │
│ 27,97 /100                    │ 7.º de 10            │ 38,8 %              │ activa  6,7 %   │
│ ▓▓▓▓░░░░ desglose 4 partes    │ Líder: Valdecruz     │ Líder: 90,8 %       │ Líder: 34,6 %   │
│ Líder: 75,02                  │                      │                     │                 │
│ T1 · n = 240   [Ver evid.]    │ T1 · n = 240         │ T1 · n = 240        │ T1 · n = 240    │
├───────────────────────────────┴──────────────────────┴─────┬───────────────┴─────────────────┤ y=520
│ Ranking por Score de Citación                 [Esp.] T1    │ Tu marca por motor y ciudad     │
│ Clínica Alborada Visión ocupa el 7.º puesto de 10 con 27,97│ [Esp.] T2 · T4                  │
│  1 Grupo Hospitalario Valdecruz [Líder] ████████████ 75,02 │ Perplexity  █████████ 65,0 %    │
│  2 Instituto Oftálmico Tramuntana       ████████ 51,70     │ Gemini      ████████  56,7 %    │
│  …                                                         │ ChatGPT     ███       18,3 %    │
│  7 ⌖ Clínica Alborada Visión [Tu marca] ████ 27,97  38,8 % │ Claude      ██        15,0 %    │
│  …                                                         │ ─────────────────────────────── │
│ 10 Centro Lasik Península               ███ 19,39   31,2 % │ Madrid      ████████  54,2 %    │
│                                                            │ Barcelona   ▏          4,2 %    │
└────────────────────────────────────────────────────────────┴─────────────────────────────────┘ y≈900 (pliegue)
  ↓ desplazamiento
  [Motores · mapa de calor 12 col] 
  [Embudo 6 col] [Madrid frente a Barcelona 6 col]
  [Perfil de fuentes 8 col] [Consistencia 4 col]
  [Duelos 1 a 1 · 12 col]  (en espontánea: estado «No aplica»)
  [Calidad de mención asistida · 12 col] (solo asistida)
```

#### Zonas

| Zona | Posición y medidas | Componentes | Contenido de la demo |
|---|---|---|---|
| Z1 Cabecera fija | 1128 × 128 px | Sobretítulo, título, conmutador (4.B.3), explicación, botones | «PASO 3 DE 7» · «Diagnóstico» · conmutador · «Ver tablas» (menú con T1…T12) · «Continuar a hallazgos» (principal) |
| Z2 Franja de modo | 4 px a todo el ancho del contenido | Franja | `color.spont.fill` o `color.assist.fill` |
| Z3 Índice de secciones | 40 px, fijo bajo la franja | Pestañas tipo ancla (chips) | 8 anclas; la activa se resalta al desplazar |
| Z4 Frase resumen | 56 px, 12 col | Bloque calculado con marca de origen Σ | Texto de plantilla de código (ver textos) |
| Z5 Cifras principales | 4 tarjetas de 3 col, 168 px de alto (la primera 192 px con desglose) | Tarjeta de cifra (4.B.4), protagonista la primera | Score 27,97 · Puesto 7.º de 10 · Aparición 38,8 % · Recomendación activa 6,7 % |
| Z6 Ranking | 8 col × 380 px | Gráfico 5.3 | 10 marcas de T1 |
| Z7 Tu marca por motor y ciudad | 4 col × 380 px | Barras mini (mismo estilo que 5.3, color marca) | 4 motores + 2 ciudades |
| Z8 Motores | 12 col × 520 px | Gráfico 5.4 | Fila Alborada real, resto pendiente |
| Z9 Embudo | 6 col × 400 px | Gráfico 5.5 | Valores de `metrics.json` |
| Z10 Ciudades | 6 col × 400 px | Gráfico 5.6 | Madrid 54,2 % · Barcelona 4,2 % |
| Z11 Fuentes | 8 col × 480 px | Gráfico 5.7 | Perfil de Alborada |
| Z12 Consistencia | 4 col × 480 px | Gráfico 5.8 | 18,8 % · 41,2 % · 40,0 % |
| Z13 Duelos | 12 col × 440 px | Gráfico 5.9 | T8 |
| Z14 Calidad de mención | 12 col × 360 px (solo asistida) | Gráfico 5.10 | T9 |
| Z15 Visor de evidencias | Panel 640 px a la derecha, a demanda | 4.B.5 | Según cifra pulsada |

Separación vertical entre filas de tarjetas: 24 px. Separación entre la frase resumen y las cifras: 16 px.

**Z5 en asistida**: Score asistido 73,97 (T9 · n = 108) · Puesto asistido «3.º de 5» · Aparición asistida 100,0 % · Menciones negativas 9,3 % (sustituye a recomendación activa; la recomendación activa asistida 6,5 % pasa a la línea de comparación). Desconocimiento asistido 6,5 % aparece como quinta línea pequeña en la tarjeta de aparición: «El chatbot dice no conocerla en el 6,5 %».

**Z4 en asistida**: «Cuando la pregunta nombra a Clínica Alborada Visión, la mencionan en el 100,0 % de las respuestas, con un 9,3 % de menciones negativas y una fuerza media de 1,21 sobre 3.»

**Z7 en asistida**: motores con valores asistidos [dato pendiente]; ciudades: «No aplica en asistida».

#### Interacciones paso a paso

1. Al entrar, el ámbito es Espontánea (o el último usado en este análisis). El foco se sitúa en el título.
2. Clic en cualquier cifra de Z5 → abre el visor con la métrica (p. ej. `tasa_aparicion_espontanea[marca=Clínica Alborada Visión]`, IDs de ejemplo EJ-0002, EJ-0003, EJ-0006). Clic en una ejecución → expande la respuesta. Total: 2 clics.
3. Clic en el conmutador «Asistida» → la franja cambia a violeta, todas las tarjetas y gráficos interpolan (400 ms), los chips de ámbito cambian, el visor abierto se refiltra, y se anuncia el cambio. El índice de secciones salta a «Duelos» como sección destacada (punto de 6 px) porque solo existe en asistida.
4. Clic en una barra del ranking → visor con las ejecuciones de esa marca en el ámbito.
5. Clic en una celda del mapa de calor → visor con marca × motor.
6. Hover en cualquier elemento gráfico → tooltip (5.1, regla 9) a los 300 ms.
7. «Gráfico / Tabla» en cualquier tarjeta → alterna la vista; se recuerda por tarjeta.
8. «Ver tablas» → menú con T1…T12 (nombre y descripción corta); elegir una abre un modal M con la tabla completa, filtrada por el ámbito, con columna `ambito` visible y celdas clicables.
9. «Continuar a hallazgos» → navega a la pantalla 4 (sin CP en esta pantalla).
10. Teclado: Alt + Mayús + E / A cambia el ámbito; Tab recorre cifras y gráficos en orden de lectura; dentro de un gráfico, flechas recorren los elementos; Intro abre evidencias.

#### Estados

| Estado | Cómo se ve |
|---|---|
| En curso (calculando evaluaciones y tablas) | Cabecera real; Z4-Z14 en esqueleto; tarjeta central de progreso 560 px: «Evaluando 624 respuestas de 4 chatbots…» con barra determinada («312 de 624») y lista de subpasos (Evaluación · Tablas T1-T12 · Métricas) con estado. En mock dura segundos; el texto añade «Esto tarda unos segundos en modo mock y unos minutos con un modelo real.» |
| Degradado | Banda 4.B.17 bajo la cabecera: «Las evaluaciones de este paso se hicieron con reglas porque el modelo de lenguaje no respondió. Las cifras son correctas; los matices de tono pueden ser más gruesos. Ver traza.» Chip «Evaluado con reglas» en el visor |
| Error con reintento | Tarjeta central: icono `octagon-x`, «No se pudo calcular el diagnóstico», «El paso de tablas falló: [mensaje del backend]. Tus aprobaciones anteriores se conservan.», botones «Reintentar» (principal) y «Ver traza» |
| n bajo | Duelos (n = 6) rayados con chip; cualquier otra celda < 15 igual |
| Vacío | No aplica (se llega con datos); si `tablas/` está vacía: «Todavía no hay diagnóstico para este análisis.» + «Calcular diagnóstico» |
| Bloqueado | Si se entra por URL sin CP1: «Aprueba la competencia para ver el diagnóstico.» + «Ir a Competencia» |
| Desactualizado | Banda ámbar: «Este diagnóstico usa la competencia anterior a tu último cambio.» + «Recalcular» |

#### Textos exactos

- Sobretítulo: «PASO 3 DE 7»
- Título: «Diagnóstico»
- Subtítulo (bajo el título, a la derecha del conmutador si cabe): «624 respuestas de ChatGPT, Gemini, Perplexity y Claude a 52 preguntas, 3 veces cada una.»
- Conmutador: ver 4.B.3.
- Índice: «Resumen», «Ranking», «Motores», «Embudo», «Ciudades», «Fuentes», «Consistencia», «Duelos».
- Frase resumen (plantilla, espontánea): «{marca} ocupa el puesto {puesto} de {total} en respuestas espontáneas: aparece en el {aparición} frente al {aparición líder} del líder. Donde menos aparece: {ciudad con menor aparición} ({valor}) y {motor con menor aparición} ({valor}).» → «Clínica Alborada Visión ocupa el puesto 7 de 10 en respuestas espontáneas: aparece en el 38,8 % frente al 90,8 % del líder. Donde menos aparece: Barcelona (4,2 %) y Claude (15,0 %).»
- Tarjetas Z5: «Score de Citación» / «27,97» / «de 100» / «Líder: 75,02» · «Puesto en el ranking» / «7.º» / «de 10 marcas» / «Líder: Grupo Hospitalario Valdecruz» · «Aparición» / «38,8 %» / «de las respuestas» / «Líder: 90,8 %» · «Recomendación activa» / «6,7 %» / «de las respuestas» / «Líder: 34,6 %». Origen en todas: «T1 · n = 240». Botón: «Ver evidencias».
- Tooltip de «Score de Citación» (icono `info` junto a la etiqueta): «Puntuación de 0 a 100 calculada por código: aparición (hasta 30), posición (20), fuerza de la recomendación (30) y calidad de la fuente (20).»
- Tooltip de «Recomendación activa»: «Respuestas en las que el chatbot recomienda la marca de forma explícita, no solo la menciona.»
- Z7 título: «Tu marca por motor y ciudad» · lectura «Perplexity y Gemini la citan más; ChatGPT y Claude, poco».
- «Ver tablas» → elementos: «T1 · Ranking general», «T2 · Marca × motor», «T3 · Embudo», «T4 · Ciudades», «T6 · Fuentes», «T8 · Duelos», «T9 · Calidad de mención asistida», «T11 · Embudo del líder», resto «T5, T7, T10, T12 · [dato pendiente: nombre]».
- Botón principal: «Continuar a hallazgos».
- Estado No aplica (duelos en espontánea): título «Solo en asistida», texto «Los duelos solo existen en preguntas asistidas, porque la pregunta nombra a las dos marcas.», botón «Cambiar a Asistida».

#### Cambios a 1920×1080 y tablet

- **1920**: escala tipográfica «1920»; Z5 pasa a una fila con 5 tarjetas (añade «Fuerza media 0,62»); Z6 y Z7 suben de alto a 440 px y quedan enteros sobre el pliegue (alto útil 996 px). El visor abre a 760 px y no tapa Z6 si el usuario lo coloca a la derecha (Z7 queda debajo).
- **1024**: carril contraído a 64 px; Z5 en 2 × 2; Z6 a 12 col y Z7 debajo a 12 col; Z9/Z10 y Z11/Z12 apiladas a 12 col.
- **768**: conmutador a ancho completo (2 × 50 %); Z3 se convierte en un selector «Ir a sección»; todos los gráficos a ancho completo; el mapa de calor desplaza horizontalmente con la columna de marcas fija.

---

### Pantalla 4 · Hallazgos (CP2)

**Objetivo.** Revisar y aprobar los hallazgos priorizados, cada uno con su evidencia, distinguiendo problemas de fortalezas y contrastando las hipótesis del cliente.
**Pregunta del usuario.** «¿Qué ha descubierto el sistema, me lo creo y qué hipótesis del cliente se sostienen?»

#### Wireframe 1440×900

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=84
│ PASO 4 DE 7 · PUNTO DE CONTROL 2 DE 4                          [Aprobar todos] [Ordenar ▾]   │
│ Hallazgos                                                                                    │
│ 7 hallazgos: 6 problemas y 1 fortaleza. Revisa las evidencias y aprueba o descarta cada uno. │
├───────────────────────────────────────────────────────────┬──────────────────────────────────┤ y=180
│ ▌H1  [▼ Problema] [Geografía]                 ○ Propuesto │ HIPÓTESIS DEL CLIENTE            │
│ ▌Brecha crítica de visibilidad en Barcelona frente a Madrid│ ⚗ «Con tan buenas reseñas        │
│ ▌ ┌─────────┐ En consultas sin marca sobre Barcelona,     │   deberíamos salir recomendados.»│
│ ▌ │ 4,2 %   │ Clínica Alborada Visión aparece en el 4,2 % │   [✕ Refutada por los datos]     │
│ ▌ │ T4·n=24 │ de las respuestas (n = 24), frente al 54,2 %│   Cuando la nombran, solo 9,3 %  │
│ ▌ └─────────┘ en Madrid (n = 24)…                         │   negativas… Ver H2 y H5         │
│ ▌ n = 24 · Descubrimiento · Todos los motores ·           │                                  │
│ ▌ Impacto alto · Confianza media                          │ ⚗ «En Barcelona nadie nos        │
│ ▌ [✓ Confirma: «En Barcelona nadie nos encuentra.»]       │   encuentra.»                    │
│ ▌ ▸ Ver 2 evidencias          Σ Calculado  [Descartar][Aprobar]│ [✓ Confirmada por los datos] │
├───────────────────────────────────────────────────────────┤   4,2 % frente a 54,2 %… Ver H1  │
│ ▌H2  [▲ Fortaleza] [Reputación]               ○ Propuesto │──────────────────────────────────│
│ ▌Fortaleza en reputación asistida: reputación sólida…     │ RESUMEN                          │
│ ▌ ┌─────────┐ Cuando se consulta por la marca…            │ 6 problemas · 1 fortaleza        │
│ ▌ │ 9,3 %   │                                             │ Aprobados 0 · Descartados 0      │
│ ▌ │T9·n=108 │                                             │ Filtrar: [Todos][Problemas]      │
│ ▌ └─────────┘                                             │          [Fortalezas]            │
│ …                                                         │                                  │
├───────────────────────────────────────────────────────────┴──────────────────────────────────┤ y=828
│ PUNTO DE CONTROL 2 DE 4 · Hallazgos   0 de 7 revisados       [← Volver a Diagnóstico]        │
│                                                              [Aprobar hallazgos  Ctrl ↵]     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘ y=900
```

#### Zonas

| Zona | Medidas | Componentes | Contenido de la demo |
|---|---|---|---|
| Z1 Cabecera | 1128 × 96 px | Sobretítulo, título, subtítulo, «Aprobar todos» (secundario), «Ordenar» (selector: «Por prioridad», «Problemas primero», «Fortalezas primero») | Ver textos |
| Z2 Lista de hallazgos | 8 col (744 px), desplazamiento propio | Tarjetas de hallazgo (4.B.6) separadas 16 px, orden por `prioridad` | H1…H7 |
| Z3 Panel lateral fijo | 4 col (360 px), fijo al desplazar | Contraste de hipótesis (4.B.7) × 2, resumen, filtros | Hipótesis de `ficha.json` |
| Z4 Barra de CP | 72 px | 4.B.8 | CP2 |

**Contenido de las 7 tarjetas** (de `findings.json`; cifra principal = primera evidencia; descripción literal del backend, con formato de número español aplicado):

| ID | Tipo en pantalla | Categoría | Título | Cifra principal | n | Fase | Motores | Impacto | Confianza | Hipótesis |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Problema | Geografía | Brecha crítica de visibilidad en Barcelona frente a Madrid | 4,2 % (T4) | 24 | Descubrimiento | Todos los motores | Alto | Media | Confirma «En Barcelona nadie nos encuentra.» |
| H2 | **Fortaleza** | Reputación | Fortaleza en reputación asistida: reputación sólida cuando la nombran; el problema es la visibilidad espontánea | 9,3 % (T9) | 108 | Comparación | Todos los motores | Alto | Alta | Refuta «Con tan buenas reseñas deberíamos salir recomendados.» |
| H3 | Problema | Motor | Visibilidad espontánea deficitaria en ChatGPT, Claude | 18,3 % (T2) | 60 | · | ChatGPT, Claude | Alto | Alta | · |
| H4 | Problema | Competencia | Brecha de visibilidad espontánea frente a Grupo Hospitalario Valdecruz y competidores directos | 27,97 (T1) | 240 | · | Todos los motores | Alto | Alta | · |
| H5 | Problema | Brief frente a datos | Contraste Brief vs Datos: Vistalia omitida, Valdecruz líder real y reseñas insuficientes | 41,2 % (T1) | 240 | · | Todos los motores | Alto | Alta | Refuta (parcialmente) «Con tan buenas reseñas…» |
| H6 | Problema | Embudo | Caída de visibilidad en la fase de Decisión del embudo | 25,0 % (T3) | 48 | Decisión | Todos los motores | Alto | Alta | · |
| H7 | Problema | Fuentes | Menor respaldo en rankings y prensa sanitaria frente al líder | 31,3 % (T6) | 201 | Validación | Todos los motores | Alto | Alta | · |

Excepción de cifra principal: en H6 se muestra la evidencia de la fase del hallazgo (Decisión, 25,0 %, n = 48) en lugar de la primera, porque el título habla de Decisión. Regla general para el backend: si el hallazgo tiene `fase_embudo`, la cifra principal es la evidencia de esa fase.

La descripción de H2 empieza en el backend con «FORTALEZA:». La interfaz elimina ese prefijo del texto porque el tipo ya se muestra en el chip.

Determinación de «Problema» frente a «Fortaleza»: `schemas.py` no tiene un campo de polaridad. Regla de diseño: el backend añade el campo `polaridad` (`problema` / `fortaleza`) [dato pendiente]; mientras tanto, se marca como fortaleza el hallazgo cuya descripción empieza por «FORTALEZA:» (H2).

#### Interacciones paso a paso

1. Al entrar, todas las tarjetas están en «Propuesto» (o con su estado guardado). Foco en el título.
2. «Ver 2 evidencias» en H1 → despliega la lista: «Aparición espontánea · Barcelona · 4,2 % · n = 24 · T4 · [Abrir respuestas]» y «Aparición espontánea · Madrid · 54,2 % · n = 24 · T4 · [Abrir respuestas]». «Abrir respuestas» abre el visor (EJ-0406; EJ-0193, EJ-0195, EJ-0202). Clic en la cifra principal abre el visor directamente (1 clic).
3. «Aprobar» en una tarjeta → estado Aprobado, contador de la barra de CP sube («1 de 7 revisados»).
4. «Descartar» → pide motivo opcional en línea (campo «Motivo (opcional)» y botones «Cancelar» / «Descartar»). La tarjeta pasa a Descartado y al final de la lista.
5. «Aprobar todos» → aprueba todos los propuestos (no recupera descartados) y muestra toast «7 hallazgos aprobados» con «Deshacer».
6. «Aprobar hallazgos» (barra de CP):
   - Si quedan propuestos sin revisar: popover «Quedan {k} hallazgos sin revisar. Se aprobarán tal como están.» con «Revisar» y «Aprobar igualmente».
   - Si todos están revisados: aprueba al instante. Registra persona y hora, toast «Hallazgos aprobados. Calculando el plan…» y navega a Plan cuando está listo.
   - Si se descartaron todos: botón deshabilitado con «Aprueba al menos un hallazgo para crear el plan».
7. Clic en «Ver H2 y H5» del contraste de hipótesis → desplaza la lista hasta H2 y lo resalta 1,2 s (fondo `color.bg.sunken`).
8. Filtros del panel: «Todos», «Problemas», «Fortalezas» (botones conmutables).
9. Teclado: con foco en una tarjeta, A aprueba, D descarta, E abre evidencias; Ctrl/⌘ + Intro aprueba el CP.

#### Estados

| Estado | Cómo se ve |
|---|---|
| En curso | Z2 con 4 tarjetas esqueleto; Z1 subtítulo «Generando hallazgos a partir de las 12 tablas…» |
| Esperando aprobación | Estado normal; barra de CP en «Esperando aprobación» |
| Aprobado | Barra de CP en «Aprobado»; las tarjetas pasan a solo lectura con botón «Editar» en la cabecera (2.3) |
| Degradado | Banda: «Los hallazgos se generaron con reglas porque el modelo de lenguaje no respondió. Las cifras y evidencias son las mismas.» |
| Error | «No se pudieron generar los hallazgos.» + «Reintentar» + «Ver traza» |
| Vacío | Icono `scan-search` 40 px · «No hay hallazgos para este análisis» · «El sistema no encontró diferencias relevantes con los umbrales actuales.» · «Volver a Diagnóstico» |
| n bajo | Tarjeta con cifra principal de n < 15: chip «n bajo» y confianza mostrada como «Baja» |
| Desactualizado | Banda ámbar en cabecera + barra de CP en «Desactualizado» |

#### Textos exactos

- Sobretítulo: «PASO 4 DE 7 · PUNTO DE CONTROL 2 DE 4»
- Título: «Hallazgos»
- Subtítulo: «7 hallazgos: 6 problemas y 1 fortaleza. Revisa las evidencias y aprueba o descarta cada uno.»
- Botones de cabecera: «Aprobar todos», «Ordenar: Por prioridad».
- Chips de tipo: «Problema», «Fortaleza». Chips de categoría (enumerado `Hallazgo.tipo`): `geografia` «Geografía» · `motor` «Motor» · `embudo` «Embudo» · `competencia` «Competencia» · `fuentes` «Fuentes» · `reputacion` «Reputación» · `brief_vs_datos` «Brief frente a datos» · `consistencia` «Consistencia» · `perfil` «Perfil de paciente».
- Metadatos: «n = 24» · «Descubrimiento» · «Todos los motores» · «Impacto alto» · «Confianza media».
- Evidencias: «Ver 2 evidencias» / «Ocultar evidencias» · fila: «{métrica en lenguaje natural} · {valor} · n = {n} · {tabla}» · «Abrir respuestas».
- Nombres de métricas en lenguaje natural: `tasa_aparicion_espontanea` «Aparición espontánea» · `pct_negativo_asistida` «Menciones negativas (asistida)» · `fuerza_media_asistida` «Fuerza media (asistida)» · `score_espontaneo` «Score espontáneo» · `pct_recomendacion_activa_espontanea` «Recomendación activa (espontánea)» · `tasa_aparicion_lider` «Aparición del líder» · `pct_fuentes_autoridad` «Fuentes de autoridad» · `calidad_media_fuente` «Calidad media de fuente».
- Acciones: «Aprobar», «Descartar», «Quitar aprobación», «Recuperar», «Motivo (opcional)».
- Panel: «HIPÓTESIS DEL CLIENTE» · «RESUMEN» · «6 problemas · 1 fortaleza» · «Aprobados {a} · Descartados {d}» · «Filtrar».
- Barra de CP: «PUNTO DE CONTROL 2 DE 4» · «Hallazgos» · «{r} de 7 revisados» · «Volver a Diagnóstico» · «Aprobar hallazgos».
- Toasts: «H{n} aprobado», «H{n} descartado» (con «Deshacer»), «Hallazgos aprobados. Calculando el plan…».

#### Cambios a 1920×1080 y tablet

- **1920**: lista a 8 col (1000 px aprox.) con la cifra principal a `type.display.l`; caben 3 tarjetas sobre el pliegue.
- **1024**: el panel lateral pasa arriba como bloque plegable «Hipótesis del cliente (2)»; lista a 12 col.
- **768**: tarjetas con la cifra principal encima de la descripción; botones «Descartar» y «Aprobar» a ancho 50 % cada uno.

---

### Pantalla 5 · Plan (CP3)

**Objetivo.** Revisar, editar y aprobar el plan de acción por fases con objetivos en rangos, calendario, presupuesto y carga del equipo, validado en contexto.
**Pregunta del usuario.** «¿Qué hacemos, cuándo, quién, cuánto cuesta y cabe en el presupuesto y en el equipo del cliente?»

#### Wireframe 1440×900 (pestaña «Acciones»)

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=84
│ PASO 5 DE 7 · PUNTO DE CONTROL 3 DE 4                                                        │
│ Plan de acción                     14 acciones · 4 fases · 48 semanas · 24.300 €             │
│ Validación:  [✓ Presupuesto dentro del rango] [✓ Dependencias correctas] [ⓘ Capacidad: faltan horas] │
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=196
│ OBJETIVOS A 12 MESES  (rangos, nunca promesas)                                        [▾]   │
│ Score de Citación espontáneo   27,97 → 40,0 – 48,0  · 12 meses · H4 H7                       │
│ Aparición espontánea global    38,8 % → 50,8 – 58,8 % · 12 meses · H4 H5                     │
│ Aparición en Barcelona          4,2 % → 20,0 – 35,0 % · 12 meses · H1                        │
│ Aparición en ChatGPT          18,3 % → 32,0 – 45,0 % · 12 meses · H3                         │
│ Aparición en Decisión         25,0 % → 38,0 – 50,0 % · 12 meses · H6                         │
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=380
│ [ Acciones | Calendario | Presupuesto y equipo | Simulador ]                                 │
├──────────────────────────────────────────────────────────────────┬───────────────────────────┤ y=424
│ 🔍 Buscar  [Fase ▾][Responsable ▾][Palanca ▾]   14 acciones · 24.300 €  [+ Añadir acción]   │ MATRIZ ESFUERZO / IMPACTO │
│ ID  Acción                         Fase Hall.  Resp.     E  I  Ini Plazo Coste   ✓ │ Impacto L │A2 A5 │A1 A6 │A12│
│ A1  Datos estructurados schema.org F0  H7 H3 H6 Agencia M L S1  3 sem 2.000 € ✓   │           │A9 A10│A8 A13│   │
│ A2  Auditoría técnica de rastreab. F0  H3      Agencia  S L S1  2 sem   750 € ✓   │           │A14   │      │   │
│ A3  Normalización de entidad y NAP F0  H7 H1 H5 Cl·Mkt  S M S2  3 sem 1.150 € ✓   │ Impacto M │A3 A4 │A11   │   │
│ …                                                                                 │           │A7    │      │   │
│ A14 Re-medición trimestral…        F3  H1…H5   Agencia  S L S12 36 sem 3.000 € ✓  │ Impacto S │      │      │   │
│                                                                                   │            S      M      L  │
├──────────────────────────────────────────────────────────────────┴───────────────────────────┤ y=828
│ PUNTO DE CONTROL 3 DE 4 · Plan   14 acciones · 24.300 € · sin conflictos  [← Volver a Hallazgos] [Aprobar plan Ctrl ↵] │
└──────────────────────────────────────────────────────────────────────────────────────────────┘ y=900
```

Pestaña «Calendario»: Gantt (4.B.12) a 12 col, 14 filas agrupadas por fase (≈ 560 px), y debajo, alineado por semanas, el gráfico de carga del equipo (4.B.15, 160 px).
Pestaña «Presupuesto y equipo»: barra de presupuesto (4.B.14, 6 col) + tabla por fase (6 col); debajo, reparto por responsable (6 col) + carga del equipo resumida (6 col).
Pestaña «Simulador»: simulador (4.B.16) a 6 col + bloque explicativo a 6 col con los objetivos actuales para comparar.

#### Zonas

| Zona | Medidas | Componentes | Contenido de la demo |
|---|---|---|---|
| Z1 Cabecera | 1128 × 112 px | Título, resumen, fila de validación (3 chips) | «14 acciones · 4 fases · 48 semanas · 24.300 €» |
| Z2 Objetivos | 12 col, 184 px desplegado / 48 px plegado | Tabla compacta de 5 filas; cada fila: KPI, valor actual (tarjeta compacta clicable), flecha, rango objetivo (campo doble editable), plazo, hallazgos (chips) | 5 objetivos de `plan.json` |
| Z3 Pestañas | 44 px | Pestañas estándar | 4 pestañas |
| Z4a Tabla de acciones | 8 col | 4.B.11 | 14 acciones |
| Z4b Matriz | 4 col (360 px) | 4.B.13 | Distribución de la demo |
| Z5 Barra de cambios sin guardar | 56 px sobre la barra de CP, solo si hay cambios | 4.B.11 | · |
| Z6 Barra de CP | 72 px | 4.B.8 | CP3 |

**Fases** (encabezados de grupo en tabla y Gantt, con nombre corto en pantalla y nombre completo en tooltip):

| Fase | Nombre corto | Semanas | Acciones | Presupuesto |
|---|---|---|---|---|
| 0 | Fundamentos | S1–S4 | A1, A2, A3, A4, A5, A7 | 6.300 € |
| 1 | Quick wins | S5–S10 | A6, A8, A9, A10 | 7.000 € |
| 2 | Autoridad y escala | S11–S36 | A11, A12, A13 | 8.000 € |
| 3 | Optimización y medición | S12–S48 | A14 | 3.000 € |

Nombres completos (tooltip) literales de `plan.json`, p. ej. «Fase 0 · Fundamentos técnicos, entidad y datos estructurados».

Hitos de re-medición: S12, S24 (además «Revisión de mitad · mes 6»), S36, S48.

#### Interacciones paso a paso

1. Al entrar, pestaña «Acciones». Fila de validación calculada al cargar.
2. Clic en un valor actual de Objetivos (p. ej. «4,2 %») → visor de evidencias de esa métrica.
3. Editar un rango objetivo: clic en «20,0 – 35,0» → dos campos numéricos con sufijo «%»; regla: mínimo < máximo y ambos > valor actual; si no, error en línea «El rango debe estar por encima del valor actual (4,2 %).». No se admite un valor único: el campo exige dos valores («Los objetivos se expresan como rango, no como cifra cerrada.»).
4. Editar una celda de la tabla (p. ej. «Inicio» de A6 de S5 a S3) → punto ámbar en la celda, aparece la barra «1 cambio sin guardar». «Guardar y revalidar» → validación (≤ 1 s): A6 depende de A1 (S1–S3) → conflicto: fila A6 en rojo, chip de validación de la cabecera «✕ 1 conflicto de dependencias», barra de A6 en el Gantt con borde rojo y etiqueta «Empieza antes de que termine A1», barra de CP con bloqueo «Resuelve 1 conflicto para aprobar». El tooltip de la fila ofrece «Mover a S4» (primera semana válida) como acción rápida.
5. Editar un coste que lleve el total por encima de 27.000 € → conflicto de presupuesto (bloqueante) con texto «Supera el máximo del brief en {x} €». Por debajo de 18.000 € → aviso no bloqueante.
6. Capacidad: si hay horas por acción, el exceso semanal es aviso no bloqueante («S3: {h} h previstas para 18 h de capacidad»). Sin horas: chip informativo «Capacidad: faltan horas por acción» (no bloquea).
7. «Añadir acción» → nueva fila en edición con ID siguiente (A15), campos obligatorios: título, hallazgos relacionados (≥ 1, si no: incidencia «Acción sin hallazgo», bloqueante), palanca, responsable, inicio, plazo, coste, KPI.
8. Hover en un chip de la matriz → resalta la fila; clic → desplaza y selecciona.
9. Pestaña «Calendario» → clic en una barra abre la fila expandida de esa acción en un panel lateral de detalle (mismo contenido que la fila expandida).
10. Pestaña «Simulador» → mover deslizadores → resultado en vivo; «Usar como objetivo» → modal → actualiza Z2.
11. «Aprobar plan» → si no hay conflictos ni cambios sin guardar: aprueba, toast «Plan aprobado. Revisando y redactando la propuesta…», navega a Propuesta.

#### Estados

| Estado | Cómo se ve |
|---|---|
| En curso | Z2 y Z4 en esqueleto; subtítulo «Construyendo el plan a partir de los hallazgos aprobados…» |
| Esperando aprobación | Normal |
| Edición sin guardar | Puntos ámbar + barra Z5; «Aprobar plan» deshabilitado con «Guarda los cambios para aprobar» |
| Conflicto de validación | Fila roja, chip rojo en Z1, aviso en Gantt/presupuesto/carga según el tipo, barra de CP bloqueada |
| Aviso no bloqueante | Chip ámbar en Z1, icono en la fila; al aprobar, popover de confirmación |
| Degradado | Banda: «El plan se generó con reglas porque el modelo de lenguaje no respondió. Revisa títulos y descripciones; los costes y fechas son los de las plantillas.» |
| Error | «No se pudo generar el plan.» + «Reintentar» |
| Aprobado | Tabla en solo lectura, «Editar» en cabecera |
| Desactualizado | «Este plan usa hallazgos anteriores a tu último cambio.» + «Recalcular plan» |

#### Textos exactos

- Sobretítulo: «PASO 5 DE 7 · PUNTO DE CONTROL 3 DE 4»
- Título: «Plan de acción»
- Resumen: «14 acciones · 4 fases · 48 semanas · 24.300 €»
- Validación: «Presupuesto dentro del rango» / «Supera el máximo del brief en {x} €» / «{x} € por debajo del mínimo del brief» · «Dependencias correctas» / «{k} conflictos de dependencias» · «Capacidad dentro del límite» / «Capacidad superada en {k} semanas» / «Capacidad: faltan horas por acción».
- Objetivos: sobretítulo «OBJETIVOS A 12 MESES» · ayuda «Rangos esperados, nunca resultados garantizados.» · columnas «Indicador», «Hoy», «Rango objetivo», «Plazo», «Hallazgos».
- Pestañas: «Acciones», «Calendario», «Presupuesto y equipo», «Simulador».
- Barra de herramientas: «Buscar acción», «Fase», «Responsable», «Palanca», «14 acciones · 24.300 €», «Añadir acción».
- Cabeceras de tabla: «ID», «Acción», «Fase», «Hallazgos», «Responsable», «Esfuerzo», «Impacto», «Inicio», «Plazo», «Coste», «Validación».
- Detalle de fila: «Descripción», «Palanca», «Fase del embudo», «Motores», «Ciudades», «Dependencias», «Entregables», «KPI», «Añadir entregable».
- Matriz: «Esfuerzo», «Impacto», «Victorias rápidas», «Apuestas de fondo», «Revisar si compensa».
- Gantt: «Semana», «Re-medición {k}», «Revisión de mitad · mes 6», leyenda «Agencia», «Cliente · Marketing», «Cliente · Comunicación», «Cliente · Equipo médico», «Tercero».
- Presupuesto: «Inversión total» · «24.300 €» · «Dentro del rango del brief: 18.000 € – 27.000 €» · «Por fase» · «Por responsable».
- Carga: «Carga semanal del equipo del cliente» · «Capacidad: 1 responsable de marketing + 0,5 de comunicación (hasta 18 h/semana)».
- Simulador: «Simulador» · «Escenario hipotético, no una predicción» · «Aparición espontánea por ciudad» · «Aparición espontánea por motor» · «Fuerza media de recomendación» · «Fuentes de calidad» · «Score» · «Puesto» · «Hoy» · «Restablecer» · «Usar como objetivo».
- Barra de cambios: «{k} cambios sin guardar» · «Descartar» · «Guardar y revalidar».
- Conflicto de dependencia: «A6 empieza en S3, antes de que termine A1 (S3).» · acción «Mover a S4».
- Barra de CP: «PUNTO DE CONTROL 3 DE 4» · «Plan» · «14 acciones · 24.300 € · sin conflictos» · «Volver a Hallazgos» · «Aprobar plan».

#### Cambios a 1920×1080 y tablet

- **1920**: Objetivos siempre desplegados; tabla y matriz visibles sin desplazar (tabla 8 col ≈ 1000 px con todas las columnas holgadas); el Gantt gana 22 px por semana.
- **1024**: matriz baja debajo de la tabla; la tabla oculta las columnas «Esfuerzo», «Impacto» y «Plazo» (visibles en el detalle); Gantt con desplazamiento horizontal y columna de acciones fija de 160 px.
- **768**: tabla convertida en lista de tarjetas por acción (título, fase, responsable, inicio–fin, coste); edición en panel completo; Gantt en solo lectura con desplazamiento horizontal.

---

### Pantalla 0 · Inicio / lista de análisis

**Objetivo.** Empezar un análisis nuevo o abrir uno existente; abrir la demo al instante.
**Pregunta del usuario.** «¿Qué análisis tengo y cómo lanzo uno nuevo?»

En Inicio no hay carril «Recorrido» (no hay análisis abierto): el contenido ocupa 1440 − 64 = 1376 px con ancho máximo de 1128 px centrado.

#### Wireframe 1440×900

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=0
│ ⚠ Datos sintéticos del kit · no representan el comportamiento real de ningún LLM  Qué significa│
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=28
│ ⌖ GEO Copilot                                                         [⌨] [◐ Tema] [AB]      │
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=84
│           Análisis GEO                                                                       │
│           De un brief a una propuesta revisada en minutos. La IA propone; tú decides.        │
│                                                                                              │
│           ┌──────────────────────────────────────────┐  ┌───────────────────────────────────┐│
│           │ ▶ Cargar demo                            │  │ + Nuevo análisis                  ││
│           │ Clínica Alborada Visión · precalculado   │  │ Sube un brief o elige una marca   ││
│           │ Se abre al instante                      │  │                                   ││
│           └──────────────────────────────────────────┘  └───────────────────────────────────┘│
│           ¿Quién revisa?  [ Nombre y apellidos           ]  Se guarda con cada aprobación.   │
│                                                                                              │
│           ANÁLISIS ANTERIORES                                    [Buscar marca…] [Modo ▾]    │
│           Marca                    Fecha            Modo      Estado            Score  run_id│
│           ⌖ Clínica Alborada Visión 20 oct. 2026 23:00 Cliente  Te toca revisar  27,97  demo │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Panel «Nuevo análisis»** (Panel lateral de 640 px, 4 bloques numerados en una sola vista):

```text
┌────────────────────────────── Nuevo análisis ──────────────────────────── ✕ ┐
│ 1 · Modo                                                                    │
│   ( ● Cliente: informe completo a partir de un brief )                      │
│   ( ○ Prospecto: mini auditoría y correo para captar una marca )            │
│ 2 · Brief                                                                   │
│   [Subir archivo | Pegar texto]                                             │
│   ┌ ⇪ Arrastra el brief aquí o [Elegir archivo]   .md · .docx · .txt ┐       │
│   └──────────────────────────────────────────────────────────────────┘       │
│   (en Prospecto: «Marca»  [Selecciona una marca de la lista ▾])             │
│ 3 · Proveedor de IA                                                         │
│   [ mock · Sin IA | anthropic · Anthropic | openai · OpenAI ]               │
│   Llamadas 0 · Tokens 0 · Coste 0 €                                         │
│   La estimación es orientativa. El coste real aparece en Calidad y trazas.  │
│ 4 · Lanzar                                                                  │
│                                   [Cancelar]  [Lanzar análisis]             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Zonas

| Zona | Medidas | Componentes | Contenido |
|---|---|---|---|
| Z1 Presentación | 1128 px, alto 96 | Título `type.h1`, subtítulo `type.body.l` | Ver textos |
| Z2 Acciones principales | 2 tarjetas interactivas de 6 col, 120 px | Tarjeta interactiva; «Cargar demo» con borde 2 px `color.text.primary` y botón principal L | «Cargar demo», «Nuevo análisis» |
| Z3 Revisor | 1 fila, campo de 360 px | Campo de texto | Nombre de la persona que aprueba |
| Z4 Lista | 12 col | Tabla de datos | Columnas: Marca · Fecha · Modo · Estado · Score · run_id · acciones de fila («Abrir», «Duplicar») |
| Z5 Panel «Nuevo análisis» | Panel lateral 640 px | Control segmentado, zona de carga, combinado de marcas, selector de proveedor (4.B.20) | Ver arriba |

Fila de la demo: «Clínica Alborada Visión» · «20 oct. 2026 23:00» · «Cliente» · estado según `state.json` · «27,97» · «demo». El score de la lista es siempre el espontáneo y la cabecera de la columna lo dice: «Score espontáneo».

Lista de marcas para modo prospecto (de `market.json`): Grupo Hospitalario Valdecruz, Instituto Oftálmico Tramuntana, Oftalmos Centro, Láser Nítida, Clínica del Ojo Cervantes, Instituto Ocular Santa Eulalia, Clínica Alborada Visión, Vistalia Oftalmología, Visionar Clínicas, Centro Lasik Península.

#### Interacciones

1. «Cargar demo» → si Z3 está vacío, el campo se marca con error «Escribe tu nombre para registrar tus aprobaciones.» y recibe el foco; si está relleno, abre el análisis `demo` en el paso pendiente (pantalla 1 con CP0 esperando, según el guion 9). Tiempo objetivo: < 1 s, sin pantallas intermedias.
2. «Nuevo análisis» → abre Z5.
3. Cambiar a «Pegar texto» → área de texto de 240 px, marcador «Pega aquí el texto del brief».
4. Elegir proveedor → la estimación se recalcula (esqueleto 300 ms).
5. «Lanzar análisis» → deshabilitado hasta tener brief (o marca) y revisor; al pulsar, cierra el panel, crea la fila en la lista con estado «Calculando…» y navega a la pantalla 1 en estado «En curso».
6. Clic en una fila → abre el análisis en su paso actual.

#### Estados

| Estado | Cómo se ve |
|---|---|
| Vacío (sin análisis) | Z4 sustituida por: icono `file-text` 40 px · «Todavía no hay análisis» · «Empieza con la demo para ver el recorrido completo o sube el brief de un cliente.» · botones «Cargar demo» y «Nuevo análisis» |
| Cargando lista | 3 filas esqueleto |
| Error de lista | «No se pudo cargar la lista de análisis.» + «Reintentar» |
| Error al subir | Mensajes de 4.A.15 |
| Demo no disponible | La tarjeta «Cargar demo» muestra «La demo precalculada no está en el servidor.» + «Ver instrucciones» [dato pendiente: ruta de la carpeta demo] |
| Fila en curso | Estado «Calculando · paso {k} de 8» con barra fina |
| Fila con error | Estado «Error · Reintentar» en `color.error.fg` |

#### Textos exactos

- Título: «Análisis GEO»
- Subtítulo: «De un brief a una propuesta revisada en minutos. La IA propone; tú decides.»
- Tarjeta demo: «Cargar demo» · «Clínica Alborada Visión · análisis precalculado» · «Se abre al instante».
- Tarjeta nuevo: «Nuevo análisis» · «Sube un brief o elige una marca».
- Revisor: etiqueta «¿Quién revisa?» · marcador «Nombre y apellidos» · ayuda «Se guarda con cada aprobación.»
- Lista: sobretítulo «ANÁLISIS ANTERIORES» · «Buscar marca» · «Modo» · cabeceras «Marca», «Fecha», «Modo», «Estado», «Score espontáneo», «run_id» · acciones «Abrir», «Duplicar».
- Panel: «Nuevo análisis» · «1 · Modo» · «Cliente» «Informe completo a partir de un brief» · «Prospecto» «Mini auditoría y correo para captar una marca» · «2 · Brief» · «Subir archivo» · «Pegar texto» · «Arrastra el brief aquí o» · «Elegir archivo» · «.md · .docx · .txt» · (prospecto) «2 · Marca» · «Selecciona una marca de la lista» · «3 · Proveedor de IA» · «Llamadas al modelo» · «Tokens estimados» · «Coste estimado» · «4 · Lanzar» · «Cancelar» · «Lanzar análisis».
- Toast: «Análisis creado. Leyendo el brief…»

#### 1920 y tablet

- **1920**: ancho máximo 1128 px centrado (no se estira); tipografía «1920».
- **1024 / 768**: tarjetas Z2 apiladas a ancho completo; la tabla oculta «run_id» y «Modo» (visibles al expandir la fila); el panel ocupa el 100 % del ancho.

---

### Pantalla 1 · Brief → Ficha (CP0)

**Objetivo.** Comprobar y completar la ficha extraída del brief antes de que el sistema la use.
**Pregunta del usuario.** «¿Ha entendido bien el brief? ¿Falta algo?»

#### Wireframe 1440×900

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=84
│ PASO 1 DE 7 · PUNTO DE CONTROL 0 DE 4                                                        │
│ Ficha de la marca                 22 campos extraídos · 0 por completar   [Ocultar brief]    │
├────────────────────────────────────┬─────────────────────────────────────────────────────────┤ y=180
│ BRIEF ORIGINAL           📄 .md     │ Identidad · Oferta · Públicos y mercado · Situación     │
│                                    │ digital · Objetivos · Presupuesto y equipo · Normativa  │
│ [texto del brief con desplazamiento│ ─────────────────────────────────────────────────────── │
│  propio; el pasaje del campo       │ IDENTIDAD                                               │
│  enfocado se resalta]              │ Marca*            [Clínica Alborada Visión     ] ✎IA    │
│                                    │ Web               [https://www.alboradavision.example]  │
│ [dato pendiente: texto del brief]  │ Sector*           [Sanidad privada             ]        │
│                                    │ Subsector         [oftalmología (cirugía refractiva…)]  │
│                                    │ OFERTA                                                  │
│                                    │ Servicios         [Cirugía refractiva…] [cataratas…] +  │
│                                    │ Servicios prioritarios [Cirugía refractiva] [control…]  │
│                                    │ Diferenciales     • Seguimiento postoperatorio…         │
│                                    │ …                                                       │
├────────────────────────────────────┴─────────────────────────────────────────────────────────┤ y=828
│ PUNTO DE CONTROL 0 DE 4 · Ficha   0 campos por completar     [← Inicio]  [Confirmar ficha Ctrl ↵] │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Zonas

| Zona | Medidas | Componentes | Contenido |
|---|---|---|---|
| Z1 Cabecera | 96 px | Título, contador de campos, conmutador «Ocultar brief / Mostrar brief» | «22 campos extraídos · 0 por completar» |
| Z2 Brief original | 5 col (448 px), desplazamiento propio, fondo `color.bg.surface`, texto Source Serif 4 16/26 | Visor de documento de solo lectura | [dato pendiente: texto del brief original]. Nombre del archivo y formato en cabecera |
| Z3 Formulario | 7 col (656 px), desplazamiento propio | Índice de secciones (anclas), campos (4.A.2), selectores multiselección | `ficha.json` |
| Z4 Barra de CP | 72 px | 4.B.8 | CP0 |

**Campos y contenido de la demo** (orden de pantalla; * obligatorio según `FichaMarca`):

| Sección | Campo en pantalla | Campo | Control | Valor de la demo |
|---|---|---|---|---|
| Identidad | Marca* | `marca` | Texto | Clínica Alborada Visión |
| | Web | `web` | Texto (URL) | https://www.alboradavision.example |
| | Sector* | `sector` | Texto | Sanidad privada |
| | Subsector | `subsector` | Texto | oftalmología (cirugía refractiva y cataratas) |
| Oferta | Servicios | `servicios` | Lista de chips editable | Cirugía refractiva (LASIK, PRK, lentes fáquicas) · cirugía de cataratas con lentes premium · control de miopía infantil · revisiones oftalmológicas · derivación en retina y glaucoma |
| | Servicios prioritarios | `servicios_prioritarios` | Multiselección sobre servicios | Cirugía refractiva · control de miopía infantil |
| | Diferenciales | `diferenciales` | Lista editable de líneas | Seguimiento postoperatorio personalizado incluido durante 12 meses · valoración preoperatoria completa en una sola visita · equipo médico estable y bien valorado por los pacientes |
| Públicos y mercado | Públicos | `publicos` | Lista editable de líneas | Los 4 públicos de `ficha.json` |
| | Ciudades | `ciudades` | Chips | Madrid · Barcelona |
| | Ciudad principal | `ciudad_principal` | Selector (de ciudades) | Madrid |
| | Ciudad de crecimiento | `ciudad_crecimiento` | Selector | Barcelona |
| | Competidores declarados | `competidores_declarados` | Chips | Instituto Oftálmico Tramuntana · Láser Nítida · Grupo Hospitalario Valdecruz |
| Situación digital | Web y contenidos · Reputación · Medios y terceros · Técnico · Herramientas · Fundación y tamaño · Sedes | `situacion_digital.*` | Área de texto por clave | Textos de `ficha.json` (p. ej. Reputación: «4,7 sobre 5 en Google con unas 1.800 opiniones.») |
| Objetivos | Hipótesis del cliente | `hipotesis_cliente` | Lista editable | «Con tan buenas reseñas deberíamos salir recomendados.» · «En Barcelona nadie nos encuentra.» |
| | Objetivo principal* | `objetivo_principal` | Área de texto | «Que los asistentes de IA recomienden a Clínica Alborada Visión de forma espontánea en Madrid y Barcelona, especialmente en cirugía refractiva» |
| | KPI de negocio | `kpis_negocio` | Lista editable | «+25 % de primeras visitas de cirugía refractiva en 12 meses» · «visibilidad y recomendación en asistentes de IA medibles y en crecimiento» |
| | Horizonte | `horizonte_meses` | Numérico con sufijo «meses» | 12 |
| Presupuesto y equipo | Presupuesto mínimo · máximo | `presupuesto_min_eur`, `presupuesto_max_eur` | Dos numéricos con sufijo «€» | 18.000 € · 27.000 € |
| | Equipo del cliente | `equipo` | Área de texto | «1 responsable de marketing + 1 persona de comunicación a media jornada; colaboración con la agencia» |
| Normativa, tono y formato | Restricciones normativas | `restricciones_normativas` | Lista editable | Las 2 de `ficha.json` |
| | Tono | `tono` | Texto | «Riguroso, cercano y sin sensacionalismo» |
| | Audiencia | `audiencia` | Texto | «Comité de dirección (perfil mixto médico y de negocio)» |
| | Formato | `formato` | Texto | «Documento + resumen ejecutivo presentable» |

Nota sobre el KPI «+25 % de primeras visitas»: es un objetivo de negocio del cliente, no una promesa de GEO Copilot. Se muestra con el chip neutro «Objetivo del cliente» para que el revisor normativo no lo confunda con una promesa propia.

#### Interacciones

1. Foco en un campo → su pasaje de origen se resalta en Z2 (fondo `color.ai.bg`) y Z2 se desplaza hasta él. Requiere offsets de extracción: [dato pendiente]; sin ellos, la función se oculta y Z2 es solo lectura.
2. Editar un campo → la marca de origen pasa de «Redactado por IA» a «Editado por {iniciales}»; aparece punto de «sin guardar» y la ficha se guarda sola a los 800 ms de inactividad (toast silencioso: texto «Guardado» junto al contador de cabecera).
3. Campo vacío obligatorio → estado «No encontrado en el brief», contador «{k} por completar», y la barra de CP bloquea: «Completa {k} campos obligatorios para confirmar».
4. Campo vacío no obligatorio → estado «No encontrado en el brief» sin bloqueo; contador lo suma como «por revisar».
5. «Confirmar ficha» → registra aprobación, toast «Ficha confirmada. Buscando competencia…», navega a Competencia cuando está lista.

#### Estados

| Estado | Cómo se ve |
|---|---|
| En curso (leyendo el brief) | Z2 muestra el brief; Z3 esqueleto con secciones; texto «Extrayendo la ficha del brief…» |
| Esperando aprobación | Normal |
| Campos faltantes | Campos con estilo «No encontrado en el brief»; índice de secciones con punto ámbar en las secciones afectadas |
| Degradado | Banda: «La ficha se extrajo con reglas porque el modelo de lenguaje no respondió. Revisa los campos de texto libre.» |
| Error | «No se pudo leer el brief.» · «Comprueba que el archivo no está protegido y vuelve a intentarlo.» · «Reintentar» · «Subir otro archivo» |
| Aprobado / desactualizado | Ver 2.3 |

#### Textos exactos

- Sobretítulo: «PASO 1 DE 7 · PUNTO DE CONTROL 0 DE 4» · Título: «Ficha de la marca» · Contador: «{n} campos extraídos · {k} por completar» · «Ocultar brief» / «Mostrar brief».
- Z2: sobretítulo «BRIEF ORIGINAL».
- Secciones: «Identidad», «Oferta», «Públicos y mercado», «Situación digital», «Objetivos», «Presupuesto y equipo», «Normativa, tono y formato».
- Campo vacío: chip «Falta en el brief» · marcador «Completa este campo: no aparece en el brief».
- Error presupuesto: «El presupuesto máximo debe ser mayor que el mínimo.»
- Barra de CP: «PUNTO DE CONTROL 0 DE 4» · «Ficha» · «{k} campos por completar» / «Todo completo» · «Inicio» · «Confirmar ficha».

#### 1920 y tablet

- **1920**: Z2 a 5 col y Z3 a 7 col con dos columnas internas de campos cortos (web, sector, subsector).
- **1024**: Z2 oculto por defecto; botón «Mostrar brief» lo abre como panel lateral.
- **768**: igual que 1024 con el formulario a 1 columna.

---

### Pantalla 2 · Competencia (CP1)

**Objetivo.** Validar con qué marcas se compara la marca del brief y ver lo que el brief no contemplaba.
**Pregunta del usuario.** «¿Contra quién compito de verdad en los chatbots?»

#### Wireframe 1440×900

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=84
│ PASO 2 DE 7 · PUNTO DE CONTROL 1 DE 4                                                        │
│ Competencia               10 marcas · 4 declaradas en el brief · 6 detectadas solo en datos  │
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=180
│ LO QUE EL BRIEF NO CONTEMPLA                                                     3 avisos    │
│ ┌─▲ Vistalia Oftalmología no está en el brief ─┐ ┌─▲ El líder real es Grupo Hospitalario ─┐  │
│ │ Aparece en el 41,2 % de las respuestas       │ │ Valdecruz: 90,8 % (score 75,02). El    │  │
│ │ espontáneas y es competidor directo.         │ │ brief trataba como referencia a        │  │
│ │ T1 · n = 240  [Ver respuestas] [Mantener…]   │ │ Tramuntana (68,8 %, 51,70). T1·n=240   │  │
│ └──────────────────────────────────────────────┘ └────────────────────────────────────────┘  │
│ ▸ 5 marcas más con aparición ≥ 30 % que el brief no nombra                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=400
│ Marca                         Rol                  En brief  En datos  Aparición espontánea  │
│ Grupo Hospitalario Valdecruz  [Líder ▾]            Sí        Sí        ███████████ 90,8 %  ⋯│
│ Instituto Oftálmico Tramuntana[Referencia ▾]       Sí        Sí        ████████ 68,8 %     ⋯│
│ Oftalmos Centro               [Contexto ▾]         No        Sí        ███████ 60,0 %      ⋯│
│ Láser Nítida                  [Competidor dir. ▾]  Sí        Sí        ██████ 55,8 %       ⋯│
│ Clínica del Ojo Cervantes     [Contexto ▾]         No        Sí        █████ 44,2 %        ⋯│
│ Instituto Ocular Santa Eulalia[Contexto ▾]         No        Sí        █████ 42,5 %        ⋯│
│ ⌖ Clínica Alborada Visión     [Marca del brief]    Sí        Sí        ████ 38,8 %          │
│ Vistalia Oftalmología         [Competidor dir. ▾]  No        Sí        ████ 41,2 %         ⋯│
│ Visionar Clínicas             [Contexto ▾]         No        Sí        ████ 33,3 %         ⋯│
│ Centro Lasik Península        [Contexto ▾]         No        Sí        ███ 31,2 %          ⋯│
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=828
│ PUNTO DE CONTROL 1 DE 4 · Competencia  3 avisos revisados de 3  [← Volver a Ficha] [Aprobar competencia Ctrl ↵] │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Zonas

| Zona | Medidas | Componentes | Contenido |
|---|---|---|---|
| Z1 Cabecera | 96 px | Título y resumen | «10 marcas · 4 declaradas en el brief · 6 detectadas solo en datos» |
| Z2 Avisos | 12 col; 2 tarjetas de 6 col (136 px) + aviso plegable de ancho completo | Aviso de discrepancia (4.B.19) | Los 3 textos de `market.json` |
| Z3 Tabla | 12 col; filas de 44 px | Tabla de datos con selector de rol en celda, barra de aparición (240 px, `color.rest.fill`; brand y leader con sus colores), columna «Nota» visible en tooltip, menú de fila «⋯» | 10 marcas de `market.json` en su orden |
| Z4 Barra de CP | 72 px | 4.B.8 | CP1 |

Columnas: «Marca» (280) · «Rol» (200, selector) · «En el brief» (96, «Sí»/«No», «No» con chip ámbar «No declarada») · «En los datos» (96) · «Aparición espontánea» (320, barra + valor; origen en pie «T1 · n = 240 por marca · Espontánea») · menú (48).

Cuenta de declaradas: `market.json` marca `declarada_en_brief = true` en Valdecruz, Tramuntana, Láser Nítida y Alborada (4, incluida la marca del brief); la ficha lista 3 competidores declarados. El resumen dice «4 declaradas en el brief (incluida tu marca)».

#### Interacciones

1. Clic en la barra o el valor de aparición → visor de evidencias de esa marca (espontánea).
2. Cambiar rol → selector con los 5 roles; la marca del brief no se puede cambiar (celda de solo lectura con tooltip «La marca del brief no cambia de rol»). Solo puede haber un líder: elegir «Líder» en otra marca abre un modal «¿Cambiar el líder?» · «{marca actual} dejará de ser líder y pasará a Referencia. El líder se usa como comparación en todo el diagnóstico.» · «Cancelar» · «Cambiar líder».
3. Menú «⋯» → «Excluir del análisis» / «Incluir de nuevo» / «Ver respuestas». Excluir una marca la tacha y la saca de los gráficos de comparación (no de las evaluaciones). Toast «{marca} excluida» con «Deshacer».
4. Acciones de los avisos: «Ver respuestas» (visor), «Mantener como competidor directo» (marca el aviso como revisado), «Confirmar como líder» (idem), «Ver en la tabla» (desplaza y resalta las 5 filas).
5. «Aprobar competencia» → si quedan avisos sin revisar, popover «Quedan {k} avisos sin revisar. ¿Aprobar igualmente?»; si no, aprueba y navega a Diagnóstico (en mock, las evaluaciones están precalculadas y el paso tarda segundos).

#### Estados

| Estado | Cómo se ve |
|---|---|
| En curso | «Contrastando el brief con las respuestas…»; tabla esqueleto de 10 filas |
| Degradado | Banda 4.B.17 |
| Error | «No se pudo contrastar el mercado.» + «Reintentar» |
| Sin avisos | Z2: «El brief coincide con lo que dicen los datos. No hay marcas relevantes sin declarar.» con `check` |
| Aprobado / desactualizado | Ver 2.3 |

#### Textos exactos

- Sobretítulo «PASO 2 DE 7 · PUNTO DE CONTROL 1 DE 4» · Título «Competencia» · Resumen «10 marcas · 4 declaradas en el brief (incluida tu marca) · 6 detectadas solo en datos».
- Avisos: sobretítulo «LO QUE EL BRIEF NO CONTEMPLA» · contador «{k} avisos» · textos de 4.B.19.
- Tabla: cabeceras «Marca», «Rol», «En el brief», «En los datos», «Aparición espontánea» · valores «Sí», «No» · chip «No declarada».
- Roles: ver 4.B.18.
- Menú: «Ver respuestas», «Excluir del análisis», «Incluir de nuevo».
- Barra de CP: «PUNTO DE CONTROL 1 DE 4» · «Competencia» · «{r} avisos revisados de {k}» · «Volver a Ficha» · «Aprobar competencia».

#### 1920 y tablet

- **1920**: los 3 avisos caben en una fila de 3 tarjetas de 4 col.
- **1024**: avisos apilados; la tabla oculta «En los datos» (todas «Sí» en la demo; si alguna es «No», la columna se muestra).
- **768**: tabla convertida en lista de tarjetas: nombre, rol (selector), aparición, chips «En brief»/«No declarada».

---

### Pantalla 6 · Propuesta

**Objetivo.** Revisar la propuesta final, comprobar el sello del revisor, distinguir texto de IA y tablas de código, y exportarla.
**Pregunta del usuario.** «¿Puedo enviar esto tal cual al comité?»

#### Wireframe 1440×900 (modo cliente)

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐ y=84
│ PASO 6 DE 7                       [ Cliente | Prospecto ]      [🔗 Enlace de solo lectura]   │
│ Propuesta                                                      [⇩ .md] [⇩ Descargar .docx]   │
├──────────────────────────────────────────────────────────────────────────────────────────────┤ y=180
│ 🛡 REVISIÓN AUTOMÁTICA   578/578 cifras trazables · 0 entidades no verificadas ·              │
│                          0 incidencias normativas                    Lista para enviar  Σ    │
├──────────────────┬───────────────────────────────────────────────────────────────────────────┤ y=300
│ ÍNDICE           │ ┌──────────────────────── hoja 888 px ─────────────────────────────────┐  │
│ 1 Resumen ejec.  │ │ ⚠ Datos sintéticos del kit · run_id demo · 20 oct. 2026 23:00         │  │
│ 2 Contexto       │ │ Propuesta GEO · Clínica Alborada Visión                                │  │
│ 3 Diagnóstico    │ │ 1. Resumen ejecutivo                                ✎ Redactado por IA │  │
│ 4 Competencia    │ │ ┆ Clínica Alborada Visión cuenta con una base asistencial y            │  │
│ 5 Hallazgos      │ │ ┆ reputacional muy sólida (valoración de 4,7 sobre 5 con 1.800 …)      │  │
│ 6 Estrategia     │ │ ┆ … ocupa el puesto 7 de 10 con un Score de Citación de 27,97 …        │  │
│ 7 Plan por fases │ │ 3. Diagnóstico de visibilidad                                          │  │
│ 8 Medición       │ │ ┌ Desglose por motor (Espontánea) ─────────────── Σ Calculado · T2 ┐   │  │
│ 9 Riesgos        │ │ │ Motor  n  Aparición  Posición  Fuerza  Score                     │   │  │
│ 10 Hoja de ruta  │ │ └──────────────────────────────────────────────────────────────────┘   │  │
│ Anexo            │ └────────────────────────────────────────────────────────────────────────┘  │
│ [✓] Marcas de    │                                                                           │
│     origen       │                                                                           │
└──────────────────┴───────────────────────────────────────────────────────────────────────────┘
```

#### Zonas (modo cliente)

| Zona | Medidas | Componentes | Contenido |
|---|---|---|---|
| Z1 Cabecera | 96 px | Título, pestañas segmentadas «Cliente / Prospecto», botones de exportación | · |
| Z2 Sello del revisor | 12 col × 96 px | 4.B.9 | «578/578 cifras trazables · 0 entidades no verificadas · 0 incidencias normativas» · «Lista para enviar» |
| Z3 Índice | 216 px, fijo | Lista de anclas + interruptor «Marcas de origen» | 10 secciones + «Anexo de trazabilidad» |
| Z4 Documento | hoja de 888 px (márgenes internos 64 px, cuerpo 760 px), fondo `color.bg.surface`, `elevation.1`, sobre canvas | Tipografía `type.doc.*`; bloques de IA con `border.ai` lateral; tablas con chip «Calculado · {tabla}»; cifras clicables | `propuesta_cliente.md` |
| Z5 Incidencias | Panel lateral de 400 px, solo si hay incidencias | Lista de 4.B.10 | En la demo: no aparece |

**Las 10 secciones** (títulos en pantalla) y su origen:

| # | Título | Contenido | Marca de origen |
|---|---|---|---|
| 1 | Resumen ejecutivo | Texto | Redactado por IA |
| 2 | Contexto y alcance | Texto + aviso de datos sintéticos + limitaciones | Redactado por IA |
| 3 | Diagnóstico de visibilidad | Texto + tablas por motor, embudo, ciudad, familia de prompt, fuentes; apartado asistido separado | Texto IA · tablas Calculado (T1-T6, T9) |
| 4 | Análisis de la competencia | Texto + ranking T1 + calidad de mención T9 + duelos T8 | Texto IA · tablas Calculado |
| 5 | Hallazgos clave | H1-H7 con evidencias | Calculado (plantilla) + Aprobado |
| 6 | Estrategia recomendada | Texto + tabla de objetivos | Texto IA · tabla Calculado + Aprobado |
| 7 | Plan de acción por fases | Tabla de 14 acciones | Calculado + Aprobado |
| 8 | Medición y seguimiento | Texto | Redactado por IA |
| 9 | Riesgos y supuestos | Listas | Calculado (de `plan.json`) |
| 10 | Hoja de ruta y presupuesto | Tablas por fase y por responsable | Calculado |
| Anexo | Anexo de trazabilidad | Tabla hallazgo → evidencia → ejecuciones | Calculado |

**Reglas de presentación del documento**:

- Las tablas de 3.2 (visibilidad asistida) van en un apartado propio con chip «Asistida» en el título de la tabla, y las de 3.1 con «Espontánea». Ninguna tabla mezcla ámbitos.
- Formato de números: la interfaz aplica formato español a todas las cifras del documento. `propuesta_cliente.md` contiene formatos mixtos («24,300 €», «9.3 %»); la vista y las exportaciones deben mostrar «24.300 €» y «9,3 %» [requisito para el backend de redacción].
- Los nombres internos (`entidad_datos_estructurados`, `cliente_marketing`, `generico`) se sustituyen por sus etiquetas en pantalla (tabla de 4.B.11) también en el documento.
- En los hallazgos, la línea «Evidencia trazable» se muestra como lista con métricas en lenguaje natural; los IDs de ejecución se conservan en mono y son clicables.
- Interruptor «Marcas de origen»: activado en la aplicación por defecto; en la exportación .docx se sustituye por una nota al inicio («Los textos marcados con una línea discontinua han sido redactados con IA y revisados por el equipo; las tablas se calculan automáticamente a partir de los datos.») y el borde discontinuo se mantiene como borde gris claro a la izquierda del párrafo.

#### Modo prospecto

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Marca  [Vistalia Oftalmología ▾]                     Sello del revisor (misma regla)         │
├────────────────────────────────────────────┬─────────────────────────────────────────────────┤
│ GANCHO                         ✎ IA        │ CORREO COMERCIAL                    ✎ IA        │
│ [dato pendiente]                           │ Asunto: [dato pendiente]                        │
│ Cifras de apoyo (Σ): puesto 8.º de 10 ·    │ [cuerpo del correo · dato pendiente]            │
│ score 26,59 · aparición 41,2 % (T1, n=240) │                                                 │
│ OPORTUNIDAD (3 hallazgos)                  │                                                 │
│ [tarjeta H] [tarjeta H] [tarjeta H]        │                                                 │
│ QUÉ HARÍAMOS (3 acciones)                  │                     [Copiar asunto] [Copiar correo] │
│ [acción] [acción] [acción]                 │                                                 │
└────────────────────────────────────────────┴─────────────────────────────────────────────────┘
```

| Zona | Medidas | Contenido |
|---|---|---|
| Selector de marca | Combinado de 360 px | Las 10 marcas; por defecto, la elegida al crear el análisis |
| Gancho | 7 col | Texto IA de `propuesta_prospecto_{marca}.md` [dato pendiente] + tarjetas de cifra compactas (Σ) con puesto, score y aparición de T1. Para Vistalia: 8.º de 10 · 26,59 · 41,2 % |
| Oportunidad | 7 col, 3 tarjetas de hallazgo compactas (sin acciones de aprobación) | [dato pendiente] |
| Qué haríamos | 7 col, 3 filas de acción (título, fase, plazo, sin coste salvo que el backend lo dé) | [dato pendiente] |
| Correo | 5 col, fijo | Asunto y cuerpo en un área de texto editable (Plex Sans 15/24), contador de palabras, botones «Copiar asunto» y «Copiar correo» |

Regla del correo: no puede incluir cifras de menciones negativas de la propia marca prospecto con tono alarmista ni comparativas denigratorias; el revisor normativo se aplica también al correo y el sello del modo prospecto lo cubre.

#### Interacciones

1. Clic en una cifra del documento → visor de evidencias (1 clic) → expandir (2 clics).
2. Clic en un contador del sello → desplaza al anexo (cifras trazables) o abre Z5 (incidencias).
3. Hover en un párrafo de IA → aparece el chip «Redactado por IA · {modelo} · prompt {versión}» y el botón fantasma «Editar párrafo».
4. «Editar párrafo» → el párrafo se vuelve editable en el sitio; al salir, marca «Editado por {iniciales}» y el revisor vuelve a pasar sobre ese párrafo (sello en «Revisando…» 1-2 s).
5. «Descargar .docx» / «.md» → descarga inmediata; si el sello está bloqueado, el botón muestra un popover: «La revisión tiene {k} incidencias bloqueantes. Corrígelas antes de exportar.» con «Ver incidencias» (no hay opción de exportar igualmente).
6. «Enlace de solo lectura» → modal: «Enlace para el comité» · campo con la URL [dato pendiente: formato] y «Copiar enlace» · texto «Quien tenga el enlace verá la propuesta y el diagnóstico simplificado, sin herramientas de edición.» · interruptor «Incluir diagnóstico simplificado».
7. Modo prospecto: cambiar la marca recarga gancho, oportunidad, acciones y correo (esqueleto); «Copiar correo» → toast «Correo copiado».

#### Estados

| Estado | Cómo se ve |
|---|---|
| En curso (revisión + redacción) | Sello en «Revisando cifras y textos…»; documento con secciones en esqueleto que se rellenan en orden; contador «Redactando sección {k} de 10» |
| Revisión con incidencias bloqueantes | Sello rojo «Bloqueada: {k} incidencias que corregir»; Z5 abierto con la lista; párrafos afectados con subrayado ondulado rojo; descargas bloqueadas |
| Incidencias no bloqueantes | Sello ámbar; descargas permitidas con popover de confirmación |
| Degradado | Banda: «La propuesta se redactó con plantillas porque el modelo de lenguaje no respondió. Las tablas y cifras son las mismas.»; chips de IA cambian a «Plantilla» |
| Error | «No se pudo redactar la propuesta.» + «Reintentar» |
| Bloqueado | Sin CP3: «Aprueba el plan para generar la propuesta.» + «Ir a Plan» |

#### Textos exactos

- Sobretítulo «PASO 6 DE 7» · Título «Propuesta» · pestañas «Cliente», «Prospecto» · botones «Enlace de solo lectura», «Descargar .md», «Descargar .docx».
- Sello: ver 4.B.9.
- Índice: «ÍNDICE» · títulos de sección · «Anexo de trazabilidad» · interruptor «Marcas de origen».
- Prospecto: «Marca» · «GANCHO» · «OPORTUNIDAD» · «QUÉ HARÍAMOS» · «CORREO COMERCIAL» · «Asunto» · «Copiar asunto» · «Copiar correo» · «{n} palabras».
- Toasts: «Descargando propuesta_cliente.docx», «Enlace copiado», «Correo copiado».

#### 1920 y tablet

- **1920**: hoja de 960 px con cuerpo 18/30; el índice se ensancha a 264 px.
- **1024**: índice como selector «Ir a sección» en la cabecera; hoja a ancho completo (912 px).
- **768**: hoja a ancho completo con márgenes internos de 24 px; tablas con desplazamiento horizontal propio.

---

### Pantalla 7 · Calidad y trazas

**Objetivo.** Demostrar al jurado técnico cómo de fiable es el juez, qué no coincide, qué hizo cada paso y quién aprobó qué.
**Pregunta del usuario.** «¿Me puedo fiar de cómo se ha evaluado y de cómo se ha ejecutado?»

#### Wireframe 1440×900 (pestaña «Validación del juez»)

```text
x=280                                                                                          x=1408
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ CALIDAD                                                                                      │
│ Calidad y trazas                                                                             │
│ [ Validación del juez | Discrepancias | Traza de la ejecución | Aprobaciones ]               │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ ⓘ LIMITACIÓN DECLARADA  El tipo de fuente es el campo con menos acierto (78,2 % global; 56,7 %│
│   en apariciones). Las decisiones del plan se apoyan en el conjunto agregado de fuentes.     │
├──────────────────────────────────────────────┬───────────────────────────────────────────────┤
│ Acierto y acuerdo por campo  Σ               │ Matriz de confusión · [Tipo de fuente ▾]      │
│ Campo            Acierto   Kappa   n muestra │          Pred.→  Rank Medio Web Dir Res Red Sin│
│ Tipo de mención  [pend.]   [pend.] [pend.]   │ Real Rank        [celdas con recuento]         │
│ Fuerza           [pend.]   [pend.] [pend.]   │      Medio                                     │
│ Sentimiento      [pend.]   [pend.] [pend.]   │      …                                         │
│ Tipo de fuente   78,2 %    [pend.] [pend.]   │                                               │
│ ▌limitación                                  │                                               │
└──────────────────────────────────────────────┴───────────────────────────────────────────────┘
```

#### Zonas y contenido

**Pestaña «Validación del juez»**

| Zona | Medidas | Contenido |
|---|---|---|
| Banda de limitación | 12 col, 64 px, fondo `color.warning.bg`, franja 4 px | Texto exacto en «Textos» |
| Tabla por campo | 6 col | Filas: Tipo de mención · Fuerza · Sentimiento · Tipo de fuente. Columnas: «Acierto» (barra 0-100 % + valor), «Kappa de Cohen» (valor de −1 a 1 + etiqueta de interpretación: < 0,20 «Leve», 0,21-0,40 «Aceptable», 0,41-0,60 «Moderado», 0,61-0,80 «Considerable», > 0,80 «Casi perfecto»), «n revisado a mano». Valores: Tipo de fuente acierto 78,2 % global; resto [dato pendiente]. La fila «Tipo de fuente» lleva franja ámbar y chip «Limitación» |
| Matriz de confusión | 6 col | Mapa de calor con escala secuencial; filas = valor real (revisión humana), columnas = valor del juez; selector de campo; diagonal con borde 2 px `color.text.primary`; celdas con recuento escrito; clic en celda → visor con esas evaluaciones. Valores [dato pendiente] |

**Pestaña «Discrepancias»**: tabla de filas con `discrepancia = true` (juez por reglas ≠ juez LLM). Columnas: «Ejecución» (mono, clicable) · «Marca» · «Campo» · «Reglas» · «LLM» · «Confianza» · «Decisión humana» (selector con los valores posibles del campo + «Sin revisar») · «Revisado por». Contador «{k} discrepancias · {r} revisadas» [dato pendiente: k]. Al fijar la decisión, la evaluación pasa a `juez = humano` y la fila muestra la marca «Aprobado · {iniciales}». Aviso al pie: «Cambiar una evaluación recalcula las tablas afectadas y marca como desactualizados los pasos que dependen de ellas.»

**Pestaña «Traza de la ejecución»**: tabla de pasos del pipeline (de `trace.jsonl`):

| Columna | Contenido |
|---|---|
| Paso | Extracción de la ficha · Contraste de mercado · Evaluación de respuestas · Tablas y métricas · Hallazgos · Plan · Revisión · Redacción |
| Estado | Chip con el estado (tabla 2.2) |
| Duración | «{s} s» |
| Llamadas LLM | número |
| Tokens | entrada / salida, punto de miles |
| Coste | «{x} €» con 2 decimales en esta tabla |
| Modelo | mono |
| Versión de prompt | mono |
| Degradado | «Sí» con chip 4.B.17 / «No» |

Fila de totales al pie (negrita). Todos los valores: [dato pendiente: `trace.jsonl` no está en los adjuntos]. Clic en una fila → panel lateral con el detalle de la línea de traza en formato clave-valor (no JSON en bruto).

**Pestaña «Aprobaciones»**: tabla cronológica. Columnas: «Punto de control» (CP0…CP3 + discrepancias revisadas) · «Qué se aprobó» («Ficha · 22 campos», «Competencia · 10 marcas, 3 avisos revisados», «Hallazgos · 6 aprobados, 1 descartado», «Plan · 14 acciones, 24.300 €») · «Persona» · «Fecha y hora» · «Estado» («Vigente» / «Sustituida el {fecha}», tachada). En la demo recién cargada: CP0 según el estado precargado; CP1 «Pendiente» (`market.json` `aprobado_por_humano: false`); CP2 y CP3 «Pendiente».

#### Estados

| Estado | Cómo se ve |
|---|---|
| Sin muestra revisada a mano | Tabla por campo vacía: «Todavía no hay una muestra revisada a mano para validar el juez.» |
| Sin discrepancias | «Reglas y LLM coinciden en todas las evaluaciones.» |
| Traza en curso | Filas con «En curso» y duración contando |
| Modo mock | Columna «Modelo» con «mock», coste «0,00 €»; banda informativa «Ejecución en modo mock: no se llamó a ningún modelo.» |

#### Textos exactos

- Sobretítulo «CALIDAD» · Título «Calidad y trazas» · pestañas «Validación del juez», «Discrepancias», «Traza de la ejecución», «Aprobaciones».
- Banda: «LIMITACIÓN DECLARADA» · «El tipo de fuente es el campo con menos acierto (78,2 % global; 56,7 % en apariciones). Las decisiones del plan se apoyan en el conjunto agregado de fuentes, no en casos sueltos.»
- Tabla: «Acierto y acuerdo por campo» · «Campo» · «Acierto» · «Kappa de Cohen» · «n revisado a mano» · tooltip de kappa: «Acuerdo entre el juez y la revisión humana descontando el acuerdo por azar. 1 es acuerdo total; 0, el que daría el azar.»
- Matriz: «Matriz de confusión» · «Valor real (revisión humana)» · «Valor del juez» · selector «Campo».

#### 1920 y tablet

- **1920**: tabla y matriz de 6 col cada una con más aire; la traza muestra todas las columnas sin desplazar.
- **1024 / 768**: tabla y matriz apiladas; la traza oculta «Modelo» y «Versión de prompt» (visibles en el detalle).

---

### Pantalla 8 · Vista de solo lectura para el cliente **[Deseable]**

**Objetivo.** Que el comité de dirección entienda el diagnóstico y el plan sin herramientas de edición ni jerga.
**Pregunta del usuario.** «¿Cómo nos ven los asistentes de IA y qué vamos a hacer?»

Sin carril, sin barra de CP, sin chips técnicos (ni run_id, ni T1, ni «espontánea» como término). Sí mantiene: aviso de datos sintéticos, cifras con «Ver ejemplo de respuesta» y el sello del revisor en lenguaje llano.

#### Wireframe 1440×900

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚠ Datos sintéticos del kit · no representan el comportamiento real de ningún LLM             │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ ⌖ GEO Copilot · Propuesta para Clínica Alborada Visión                       🔒 Solo lectura │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                 [ Resumen | Cómo nos ven | Qué haremos | Documento completo ]                │
│                                                                                              │
│      Cuando alguien pide a un asistente de IA una clínica oftalmológica sin nombrar          │
│      ninguna, Clínica Alborada Visión aparece en 39 de cada 100 respuestas.                  │
│      La clínica que más aparece lo hace en 91 de cada 100.                                   │
│                                                                                              │
│      ┌ 7.º de 10 ┐  ┌ 38,8 % ┐  ┌ 4,2 % en Barcelona ┐   ✓ 578 cifras comprobadas            │
│      │ clínicas  │  │ aparece │  │ 54,2 % en Madrid  │     una a una contra los datos         │
│      └───────────┘  └─────────┘  └────────────────────┘                                      │
│      [ranking simplificado: 10 barras, tu clínica resaltada, sin scores, solo «aparece en x %»]│
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Zonas

| Pestaña | Contenido | Componentes |
|---|---|---|
| Resumen | Frase principal (Source Serif 4, 28/40), 3 cifras grandes, sello en lenguaje llano, enlace «Ver la propuesta completa» | Tarjetas de cifra sin origen técnico; con «Ver ejemplo de respuesta» |
| Cómo nos ven | Ranking simplificado (aparición, no score) · «Por asistente» (4 barras de la clínica) · «Por ciudad» (2 barras) · «Lo que dicen cuando nos nombran»: «9,3 % de menciones negativas sobre 108 respuestas» (sin convertir a fracciones) · objeción más repetida de la clínica: «Eso sí, algunos pacientes echan en falta más franjas de cita por la tarde.» (3 veces) | Gráficos 5.3, 5.4 (solo fila), 5.6 simplificados |
| Qué haremos | 4 fases como línea de tiempo horizontal simple (sin dependencias), inversión 24.300 € dentro de 18.000 € – 27.000 €, objetivos como rangos, re-mediciones S12, S24, S36, S48 | Barra de presupuesto, lista de fases |
| Documento completo | La Propuesta (pantalla 6) sin controles, sin marcas de origen visibles (con la nota de origen al inicio), con descarga .docx si el consultor la permitió | Hoja de documento |

Equivalencias de lenguaje llano (solo en esta vista):

| Término técnico | En la vista del comité |
|---|---|
| Espontánea | «Cuando el paciente no nombra ninguna clínica» |
| Asistida | «Cuando el paciente pregunta por la clínica» |
| Score de Citación | No se muestra en Resumen; en «Documento completo» se mantiene con su definición |
| Motor | «Asistente de IA» |
| Recomendación activa | «La recomiendan expresamente» |
| n = 240 | «sobre 240 respuestas» |
| Revisor automático | «578 cifras comprobadas una a una contra los datos» |

Nota de redacción: el redondeo «39 de cada 100» y «91 de cada 100» es una transformación de presentación de 38,8 % y 90,8 % que debe hacer el código (redondeo a entero), y la cifra exacta aparece en el tooltip.

#### Móvil (390×844)

- Una columna de 358 px; pestañas como control segmentado desplazable; frase principal 22/32; cifras en tarjetas de ancho completo; ranking como lista de 10 filas con barra de 120 px; documento con tipografía 16/26.
- Aviso de datos sintéticos de 2 líneas (alto 44 px).
- El visor «Ver ejemplo de respuesta» se abre como hoja inferior a pantalla completa.

#### Estados

| Estado | Cómo se ve |
|---|---|
| Enlace caducado o revocado | «Este enlace ya no está disponible. Pide uno nuevo a tu consultor.» |
| Propuesta sin aprobar | La vista no se puede generar (el botón del consultor está deshabilitado hasta CP3) |
| Cargando | Esqueleto de la frase y las 3 cifras |

---

## 7. Microcopy

### 7.1 Glosario de la interfaz

Cada término tiene un nombre fijo en pantalla y una explicación corta (≤ 160 caracteres) para su tooltip. No se usan sinónimos.

| Concepto | Nombre en pantalla | Tooltip |
|---|---|---|
| GEO | GEO | «Optimización para motores generativos: trabajo para que los asistentes de IA conozcan y recomienden una marca.» |
| Motor | Motor | «Asistente de IA evaluado: ChatGPT, Gemini, Perplexity o Claude.» |
| Ejecución | Respuesta / Ejecución | «Una pregunta lanzada a un motor en una repetición. Hay 624 en este análisis.» |
| Pregunta | Pregunta | «Una de las 52 preguntas del estudio, generada a partir de 25 plantillas.» |
| Repetición | Repetición | «Cada pregunta se lanza 3 veces a cada motor para medir la estabilidad de la respuesta.» |
| Espontánea | Espontánea | «Preguntas que no nombran ninguna clínica. Mide si el chatbot conoce y recomienda la marca por iniciativa propia.» |
| Asistida | Asistida | «Preguntas que nombran la marca o la enfrentan a otra. Mide qué dice el chatbot de ella cuando ya la conoce.» |
| Ámbito | Ámbito de las preguntas | «Espontánea o asistida. Nunca se mezclan en una misma cifra.» |
| Aparición | Aparición | «Porcentaje de respuestas en las que la marca aparece.» |
| Posición | Posición | «Lugar en el que aparece la marca dentro de la respuesta. 1 es la primera mencionada.» |
| Tipo de mención | Tipo de mención | «Recomendación activa, comparación neutra o mención pasiva.» |
| Recomendación activa | Recomendación activa | «El chatbot recomienda la marca de forma explícita, no solo la menciona.» |
| Comparación neutra | Comparación neutra | «La marca aparece comparada con otras sin que el chatbot se incline por ella.» |
| Mención pasiva | Mención pasiva | «La marca aparece en una lista o de pasada.» |
| Fuerza de recomendación | Fuerza | «De −1 (desaconseja) a 3 (recomienda con claridad). 0 si no aparece.» |
| Sentimiento | Sentimiento | «Tono de la mención: positivo, neutro o negativo.» |
| Menciones negativas | Menciones negativas | «Porcentaje de menciones con advertencias o críticas sobre la marca.» |
| Desconocimiento | El chatbot no la conoce | «Respuestas en las que el chatbot dice no tener información sobre la marca.» |
| Fuente | Fuente | «Sitio que el chatbot cita o en el que se apoya. Se clasifica en 7 tipos.» |
| Calidad de fuente | Calidad de fuente | «Valor de 0 a 1 según el tipo de fuente: 1 para rankings e instituciones, 0,2 sin fuente.» |
| Fuentes de autoridad | Fuentes de autoridad | «Rankings, instituciones y medios. Son las que más pesan en la calidad de fuente.» |
| Score de Citación | Score de Citación | «Puntuación de 0 a 100 calculada por código: aparición (hasta 30), posición (20), fuerza (30) y calidad de fuente (20).» |
| Ranking | Puesto | «Lugar de la marca entre las 10 analizadas, ordenadas por Score de Citación.» |
| Embudo | Embudo | «Fases de decisión del paciente: descubrimiento, comparación, validación y decisión.» |
| Descubrimiento | Descubrimiento | «Preguntas para encontrar opciones: “¿qué clínicas hay…?”.» |
| Comparación | Comparación | «Preguntas para comparar opciones entre sí.» |
| Validación | Validación | «Preguntas para comprobar si una opción es fiable.» |
| Decisión | Decisión | «Preguntas para elegir y pedir cita.» |
| Consistencia | Consistencia | «Si la marca sale siempre (3/3), a veces (1-2/3) o nunca (0/3) al repetir la misma pregunta.» |
| Consolidada | Consolidada | «Sale en las 3 repeticiones.» |
| Azar | Azar | «Sale en 1 o 2 de las 3 repeticiones.» |
| Ausente | Ausente | «No sale en ninguna repetición.» |
| Duelo | Duelo 1 a 1 | «Pregunta asistida que enfrenta a dos marcas. Gana la que el chatbot prefiere.» |
| n | n | «Número de respuestas sobre las que se calcula la cifra.» |
| n bajo | n bajo | «Menos de 15 respuestas. Una sola respuesta cambia mucho la cifra.» |
| Tabla T1…T12 | Tabla T{n} | «Tabla de diagnóstico calculada por código de la que sale la cifra.» |
| Evidencias | Evidencias | «Las respuestas originales de los chatbots que forman una cifra.» |
| Hallazgo | Hallazgo | «Conclusión priorizada con su evidencia. Puede ser un problema o una fortaleza.» |
| Problema | Problema | «Hallazgo que señala una brecha que conviene corregir.» |
| Fortaleza | Fortaleza | «Hallazgo que señala algo que la marca ya hace bien.» |
| Impacto | Impacto | «Cuánto afecta el hallazgo al objetivo del cliente: alto, medio o bajo.» |
| Confianza | Confianza | «Solidez de la evidencia: alta, media o baja, según la muestra y la coherencia de los datos.» |
| Hipótesis del cliente | Hipótesis del cliente | «Creencias del cliente recogidas del brief, contrastadas con los datos.» |
| Palanca | Palanca | «Tipo de trabajo de una acción: técnico, contenido, autoridad en terceros, etc.» |
| Esfuerzo / Impacto (S/M/L) | Esfuerzo · Impacto | «Talla estimada: S pequeño, M medio, L grande.» |
| Objetivo | Rango objetivo | «Valor esperado a 12 meses, expresado como rango. No es una promesa de resultado.» |
| Re-medición | Re-medición | «Repetir el estudio completo para medir la evolución. Previstas en las semanas 12, 24, 36 y 48.» |
| Simulador | Simulador | «Calcula el score con los valores que muevas. Escenario hipotético, no una predicción.» |
| Punto de control | Punto de control (CP) | «Momento en que una persona revisa y aprueba antes de que el sistema continúe.» |
| Calculado | Calculado | «Cifra o tabla obtenida por código a partir de los datos.» |
| Redactado por IA | Redactado por IA | «Texto escrito por un modelo de lenguaje. Lo revisa una persona.» |
| Aprobado | Aprobado | «Una persona lo ha revisado y aprobado. Se registra quién y cuándo.» |
| Degradado | Listo con reglas | «El modelo de lenguaje no respondió y el paso se completó con reglas o plantillas.» |
| Revisor | Revisión automática | «Comprueba que cada cifra y entidad del texto existe en los datos y que no se incumple la normativa de publicidad sanitaria.» |
| Juez | Juez | «Sistema que evalúa cada respuesta: por reglas, por LLM o ambos.» |
| Kappa de Cohen | Kappa | «Acuerdo entre el juez y la revisión humana descontando el azar.» |
| Proveedor | Proveedor de IA | «Servicio de modelo de lenguaje usado: mock (sin IA), anthropic u openai.» |
| run_id | run_id | «Identificador único de este análisis.» |
| Modo cliente | Cliente | «Informe completo a partir del brief de un cliente.» |
| Modo prospecto | Prospecto | «Mini auditoría y correo comercial para presentar el servicio a una marca nueva.» |

### 7.2 Tono de voz

- **Consultor (pantallas 0-7)**: tuteo, frases cortas, verbo delante. «Revisa las evidencias y aprueba o descarta cada uno.» Sin entusiasmo ni exclamaciones.
- **Comité (pantalla 8 y Propuesta)**: tercera persona e impersonal («Clínica Alborada Visión aparece…», «Se propone…»). Rigor sin tecnicismos, en línea con el tono del brief: «Riguroso, cercano y sin sensacionalismo».
- **Sistema**: dice qué pasó, qué se conserva y qué hacer. «No se pudo calcular el diagnóstico. Tus aprobaciones anteriores se conservan.»

### 7.3 Reglas de redacción

1. **Cifra + base.** Ninguna cifra sin su n o su base: «38,8 % (n = 240)» o «sobre 240 respuestas».
2. **Describir, no valorar.** «Aparece en el 4,2 %» en lugar de «resultado pésimo».
3. **Rangos, nunca promesas.** Objetivos siempre como «40,0 – 48,0». Palabras prohibidas en toda la interfaz y en los textos generados: «garantizado», «garantizamos», «asegurado», «el mejor», «líder indiscutible», «número uno», «100 % eficaz», «sin riesgo», «resultados inmediatos», «milagro», «definitivo».
4. **Competidores con datos, sin adjetivos.** Se permite «Láser Nítida: 34,3 % de menciones negativas (n = 108)». No se permite «peor», «mala», «deficiente» aplicado a otra marca, ni frases que inviten a desconfiar de ella. «Líder» es un rol del análisis (la marca más visible en los datos), no una valoración; su tooltip lo dice.
5. **Botones con verbo y objeto.** «Aprobar hallazgos», no «Aceptar».
6. **Errores con salida.** Todo error incluye una acción («Reintentar», «Ver traza», «Subir otro archivo»).
7. **Honestidad sobre los datos.** El aviso de datos sintéticos no se reformula ni se acorta.
8. **Formato español.** Coma decimal, punto de miles, espacio antes de % y €, comillas españolas «» para citas, fechas «20 oct. 2026».
9. **Mayúsculas.** Solo inicial de frase y nombres propios. Los títulos de botones y pantallas no van en mayúsculas iniciales por palabra.
10. **Sin emojis** ni iconos de destellos.

### 7.4 Mensajes del sistema reutilizables

| Situación | Texto |
|---|---|
| Guardado automático | «Guardado» |
| Cambios sin guardar al salir | Modal: «Tienes cambios sin guardar» · «Si sales ahora, se perderán {k} cambios.» · «Seguir editando» · «Salir sin guardar» |
| Paso en curso | «Calculando {paso}…» |
| Paso en curso largo (> 20 s) | «Sigue calculando. Con un modelo real este paso puede tardar unos minutos.» |
| Error genérico | «Algo ha fallado en {paso}.» · «Reintentar» · «Ver traza» |
| Sin conexión | «Sin conexión con el servidor. Tus cambios se guardarán al reconectar.» |
| Aprobación deshecha | «Aprobación deshecha. {CP} vuelve a estar pendiente.» |
| Copiado | «Copiado» |

---

## 8. Accesibilidad

### 8.1 Orden de foco por pantalla

Común a todas: (1) enlace oculto «Saltar al contenido» (visible al recibir foco) · (2) aviso de datos sintéticos («Qué significa») · (3) barra superior · (4) carril «Recorrido» · (5) contenido · (6) barra de punto de control · (7) región de notificaciones.

| Pantalla | Orden dentro del contenido |
|---|---|
| 0 Inicio | «Cargar demo» → «Nuevo análisis» → «¿Quién revisa?» → buscador → filtro de modo → filas de la tabla (cada fila un enlace; acciones de fila con flecha derecha) |
| 1 Ficha | «Ocultar brief» → índice de secciones → campos en orden visual de arriba abajo → brief original (región desplazable enfocable) → barra de CP |
| 2 Competencia | Avisos (cada aviso: «Ver respuestas» → acción) → aviso plegable → tabla (fila a fila: barra de aparición → rol → menú) → barra de CP |
| 3 Diagnóstico | Conmutador de ámbito → «Ver tablas» → «Continuar a hallazgos» → índice de secciones → frase resumen → 4 tarjetas de cifra → gráficos en orden de lectura (cada gráfico: conmutador «Gráfico / Tabla» → elementos del gráfico con flechas) |
| 4 Hallazgos | «Aprobar todos» → «Ordenar» → tarjetas H1…H7 (dentro: cifra principal → «Ver evidencias» → «Descartar» → «Aprobar») → panel de hipótesis → filtros → barra de CP |
| 5 Plan | Chips de validación (cada conflicto es un enlace al elemento) → objetivos → pestañas → contenido de la pestaña (tabla: barra de herramientas → rejilla) → matriz → barra de cambios → barra de CP |
| 6 Propuesta | Pestañas Cliente/Prospecto → exportaciones → sello (contadores) → índice → documento (cifras clicables en orden de lectura) → interruptor de marcas de origen |
| 7 Calidad | Pestañas → banda de limitación → tabla → matriz (celdas con flechas) |
| 8 Solo lectura | Pestañas → frase principal → cifras («Ver ejemplo de respuesta») → gráficos |
| Visor de evidencias | Al abrir, foco en el título del panel → filtros → lista (flechas o J/K) → pie; Esc devuelve el foco al elemento que lo abrió |

### 8.2 Atajos de teclado

Todos con modificador, salvo los que solo actúan con el foco dentro de un componente (cumple WCAG 2.1.4). Panel de ayuda con «?» desde el botón `keyboard` de la barra superior (no por tecla suelta).

| Atajo | Acción | Ámbito |
|---|---|---|
| Ctrl/⌘ + Intro | Aprobar el punto de control de la pantalla | Pantallas con CP (fuera de áreas de texto) |
| Alt + 1…7 | Ir al paso 1…7 | Análisis abierto |
| Alt + 0 | Ir a Inicio | Global |
| Alt + Mayús + E | Ámbito Espontánea | Diagnóstico |
| Alt + Mayús + A | Ámbito Asistida | Diagnóstico |
| Esc | Cerrar visor, modal, tooltip o popover | Global |
| F6 | Mover el foco a la región de notificaciones y volver | Global |
| J / K | Siguiente / anterior ejecución | Con foco en la lista del visor |
| Intro | Expandir / contraer ejecución o abrir evidencias | Elemento enfocado |
| A / D / E | Aprobar / descartar / ver evidencias del hallazgo | Con foco en una tarjeta de hallazgo |
| Flechas | Recorrer elementos de un gráfico, celdas de tabla o mapa de calor | Con foco en el componente |
| Ctrl/⌘ + S | Guardar y revalidar el plan | Plan con cambios |

### 8.3 Textos alternativos de los gráficos

Cada gráfico tiene: (a) nombre accesible = título; (b) descripción = lectura calculada + resumen de datos; (c) alternativa en tabla (conmutador «Gráfico / Tabla»). Plantillas con los datos de la demo:

| Gráfico | Descripción accesible |
|---|---|
| Desglose del score | «Score de Citación de Clínica Alborada Visión en espontánea: 27,97 de 100. Desglose por componentes pendiente.» |
| Ranking | «Barras horizontales de 10 marcas ordenadas por score espontáneo. Primero Grupo Hospitalario Valdecruz, líder, con 75,02. Clínica Alborada Visión, tu marca, séptima con 27,97 y 38,8 % de aparición. Último Centro Lasik Península con 19,39.» |
| Marca × motor | «Mapa de calor de aparición espontánea por marca y motor. Tu marca: ChatGPT 18,3 %, Gemini 56,7 %, Perplexity 65,0 %, Claude 15,0 %. n = 60 por celda.» |
| Embudo | «Líneas de aparición espontánea por fase. Tu marca: Descubrimiento 44,7 %, Comparación 38,9 %, Validación 33,3 %, Decisión 25,0 %. Líder en Decisión: 97,9 %.» |
| Ciudades | «Comparación Madrid y Barcelona. Tu marca: Madrid 54,2 %, Barcelona 4,2 %, diferencia de 50,0 puntos. n = 24 por ciudad.» |
| Fuentes | «Composición de fuentes en las 201 apariciones de tu marca: Ranking o institución 15,9 %, Medio 15,4 %, Web propia 20,9 %, Directorio o comparador 20,4 %, Plataforma de reseñas 14,4 %, Red social o foro 6,5 %, Sin fuente 6,5 %.» |
| Consistencia | «Consistencia de tu marca entre repeticiones: consolidada 18,8 %, azar 41,2 %, ausente 40,0 %.» |
| Duelos | «Duelos asistidos de tu marca, 6 respuestas por motor, muestra pequeña. Frente a Tramuntana: ChatGPT 2 a 4, Gemini 3 a 3, Perplexity 3 a 3, Claude 1 a 5. Frente a Valdecruz: ChatGPT 1 a 5, Gemini 2 a 4, Perplexity 0 a 6, Claude 1 a 5.» |
| Calidad de mención | «Menciones negativas en asistida: Valdecruz 16,7 %, Tramuntana 5,3 %, tu marca 9,3 %, Vistalia 25,9 %, Láser Nítida 34,3 %.» |
| Gantt | «Calendario de 14 acciones en 48 semanas, 4 fases. Re-mediciones en las semanas 12, 24, 36 y 48. Ver la tabla de acciones para el detalle.» |
| Presupuesto | «Total 24.300 euros dentro del rango del brief de 18.000 a 27.000. Fase 0: 6.300; fase 1: 7.000; fase 2: 8.000; fase 3: 3.000.» |
| Matriz | «Victorias rápidas, impacto alto y esfuerzo pequeño: A2, A5, A9, A10, A14. …» (las 5 celdas con contenido) |

### 8.4 Lectores de pantalla

- **Regiones**: «Aviso de datos», «Barra superior», «Recorrido del análisis» (navegación), «Contenido principal», «Punto de control», «Evidencias» (complementaria), «Notificaciones».
- **Cambios en vivo** (región educada): cambio de ámbito («Mostrando resultados de preguntas asistidas»), aprobaciones («Hallazgos aprobados por {nombre} a las {hora}»), resultados del simulador, revalidación del plan («Plan revalidado: 1 conflicto de dependencias»). Región asertiva solo para errores.
- **Marca del brief**: su nombre se anuncia seguido de «, tu marca»; el líder, de «, líder». Así no depende del color.
- **Origen**: cada cifra anuncia su origen tras el valor («38,8 %, tabla T1, n = 240»). El chip «Redactado por IA» se anuncia al inicio del bloque de texto.
- **n bajo**: se anuncia «muestra pequeña» tras el valor.
- **Gráficos**: elementos enfocables con nombre completo; se puede pasar a la vista de tabla con un único botón.
- **Estados de carga**: «Calculando diagnóstico, 312 de 624» (actualizado como máximo cada 5 s para no saturar).

### 8.5 Checklist WCAG 2.1 AA

| Criterio | Cómo se cumple |
|---|---|
| 1.1.1 Contenido no textual | Iconos con nombre o decorativos ocultos; gráficos con descripción y tabla |
| 1.3.1 Información y relaciones | Tablas semánticas, encabezados jerárquicos, formularios con etiqueta |
| 1.3.2 Secuencia significativa | Orden de foco = orden visual (8.1) |
| 1.4.1 Uso del color | Marca del brief con icono y texto; tipos de hallazgo con texto e icono; ámbito con texto; series con forma; n bajo con chip |
| 1.4.3 Contraste mínimo | Tablas de 3.1.5: todas las combinaciones de texto ≥ 4,5:1 |
| 1.4.4 Cambio de tamaño | Funciona al 200 % de zoom (el layout pasa a la rejilla de 1024/768) |
| 1.4.10 Reflujo | A 320 px CSS de ancho solo se garantiza la vista 8; el resto exige tablet (excepción declarada: herramienta de datos compleja; las tablas desplazan en su contenedor) |
| 1.4.11 Contraste no textual | Controles y bordes informativos ≥ 3:1 (`border.strong` 3,89:1); gráficos con separación y etiquetas |
| 1.4.12 Espaciado de texto | Sin alturas fijas en contenedores de texto salvo chips (que permiten salto de línea) |
| 1.4.13 Contenido al pasar | Tooltips descartables con Esc, persistentes mientras el puntero está encima |
| 2.1.1 Teclado | Todo operable con teclado, incluidos gráficos, Gantt (vía tabla) y deslizadores |
| 2.1.2 Sin trampas | Modales con foco atrapado y salida con Esc |
| 2.1.4 Atajos de una tecla | Solo activos con foco en el componente |
| 2.2.1 Tiempo ajustable | Toasts con «Deshacer» de 10 s, pausables |
| 2.3.1 Destellos | Sin destellos |
| 2.4.1 Saltar bloques | «Saltar al contenido» |
| 2.4.3 Orden de foco | 8.1 |
| 2.4.6 Encabezados y etiquetas | Descriptivos |
| 2.4.7 Foco visible | Anillo de 2 px con separación, ≥ 3:1 |
| 2.5.3 Etiqueta en el nombre | Nombre accesible empieza por el texto visible |
| 3.1.1 Idioma | Documento declarado en español (es-ES) |
| 3.2.2 Al introducir datos | Editar no navega; guardar es explícito en el plan |
| 3.3.1 / 3.3.3 Errores | Mensaje en texto con sugerencia |
| 3.3.4 Prevención de errores | Confirmación al editar pasos aprobados; «Deshacer» en aprobaciones |
| 4.1.2 Nombre, función, valor | Componentes de la librería con patrones accesibles |
| 4.1.3 Mensajes de estado | Regiones en vivo (8.4) |

---

## 9. Guion de la demo en la interfaz

**Duración**: 5 minutos. **Resolución**: 1920×1080 proyectada (modo proyector activo, tema claro). **Navegador**: pestaña única, zoom 100 %.

### 9.1 Estado precargado

| Elemento | Estado antes de empezar |
|---|---|
| Inicio | Campo «¿Quién revisa?» relleno con el nombre de quien presenta |
| Análisis `demo` | Todos los pasos calculados en mock (`state.json` con pasos `done` o `awaiting_human`); CP0 a CP3 en «Esperando aprobación»; proveedor «mock» |
| Diagnóstico | Ámbito Espontánea; sin visor abierto |
| Hallazgos | Los 7 en «Propuesto» |
| Plan | Sin cambios; A6 en S5 |
| Propuesta | Generada; sello 578/578, 0 incidencias |
| Copia de seguridad **[Deseable]** | Un segundo análisis «demo · todo aprobado» en la lista, por si hay que saltar pasos |

### 9.2 Recorrido clic a clic

| Tiempo | Pantalla | Clic / acción | Qué se dice y qué se señala |
|---|---|---|---|
| 0:00 | Inicio | Señalar la barra de aviso | «Datos sintéticos del kit: lo avisamos en cada pantalla.» |
| 0:10 | Inicio | Clic en «Cargar demo» | «Clínica Alborada Visión, el caso del reto.» |
| 0:15 | 1 Ficha | Señalar brief a la izquierda y ficha a la derecha; marca «Redactado por IA» en un campo | «La IA lee el brief y propone la ficha. Lo que redacta la IA se ve con línea discontinua.» |
| 0:35 | 1 Ficha | Ctrl + Intro | «Primer punto de control. Un clic y queda registrado quién y cuándo.» Señalar el segmento azul en el carril |
| 0:45 | 2 Competencia | Señalar aviso «Vistalia Oftalmología no está en el brief · 41,2 %» y «El líder real es Grupo Hospitalario Valdecruz · 90,8 %» | «El sistema avisa de lo que el brief no contempla.» |
| 1:10 | 2 Competencia | Clic en «Aprobar competencia» | Punto de control 2 |
| 1:15 | 3 Diagnóstico | Dejar 5 s quieta la pantalla | Señalar la frase resumen y la barra bermellón en el 7.º puesto: «Séptima de diez. Aparece en el 38,8 % frente al 90,8 % del líder.» |
| 1:35 | 3 Diagnóstico | Clic en la tarjeta «Aparición 38,8 %» → visor → clic en EJ-0002 | «Cada cifra lleva a la respuesta original del chatbot en dos clics. La marca va resaltada.» |
| 2:00 | 3 Diagnóstico | Esc · clic en «Asistida» | «Cuando la nombran, la cosa cambia: 73,97 y solo 9,3 % de menciones negativas. Espontánea y asistida nunca se mezclan: la franja de color lo indica.» Señalar duelos rayados: «n = 6, lo marcamos como muestra pequeña.» |
| 2:25 | 3 Diagnóstico | Clic en «Espontánea» · desplazar a «Ciudades» | «Madrid 54,2 %, Barcelona 4,2 %.» |
| 2:40 | 3 Diagnóstico | Clic en «Continuar a hallazgos» | |
| 2:45 | 4 Hallazgos | Señalar H2 en verde frente a los demás en granate; panel de hipótesis «Refutada por los datos» | «La hipótesis del cliente era que con buenas reseñas deberían salir. Los datos dicen que las reseñas no son el freno: el freno es que no la descubren.» |
| 3:10 | 4 Hallazgos | «Aprobar todos» · Ctrl + Intro | Punto de control 3 |
| 3:20 | 5 Plan | Señalar objetivos en rangos y chip «Presupuesto dentro del rango» · pestaña «Calendario» | «14 acciones, 24.300 € dentro de 18.000-27.000 €. Objetivos en rangos, nunca promesas.» |
| 3:45 | 5 Plan | Pestaña «Acciones» · cambiar Inicio de A6 a S3 · «Guardar y revalidar» | Señalar el conflicto en rojo y el bloqueo de la aprobación: «Si edito, el sistema revalida.» Clic en «Mover a S4» · guardar |
| 4:10 | 5 Plan | Ctrl + Intro | Punto de control 4 |
| 4:15 | 6 Propuesta | Señalar el sello «578/578 cifras trazables · 0 entidades no verificadas · 0 incidencias normativas» y un párrafo de IA frente a una tabla calculada | «Lista para enviar al comité.» Clic en «Descargar .docx» |
| 4:40 | 7 Calidad | Clic en «Calidad y trazas» del carril · señalar la limitación 78,2 % · pestaña «Aprobaciones» | «Declaramos dónde falla el juez. Y aquí están las 4 aprobaciones con nombre y hora.» |
| 5:00 | · | Fin | |

### 9.3 Planes de contingencia

- Si un paso tarda: el estado «En curso» muestra el progreso; seguir hablando del paso anterior.
- Si algo falla: Alt + 0 → abrir «demo · todo aprobado» y continuar en el mismo punto.
- Si el proyector corta los bordes: el contenido crítico está dentro de un margen de 48 px (rejilla 1920).

---

## 10. Priorización para implementar

Esfuerzo relativo: S (≤ 2 h), M (2-5 h), L (5-10 h) para 1 persona. Presupuesto total: ~25 h × 2-3 personas.

### 10.1 Imprescindible (la demo de extremo a extremo depende de esto)

| Elemento | Esfuerzo |
|---|---|
| Tokens de color, tipografía, espaciado (tema claro) | S |
| Estructura de la aplicación: aviso de datos sintéticos, barra superior, carril «Recorrido» con estados | M |
| Botón, campo, selector, chip, pestañas, tarjeta, modal, panel lateral, toast, tooltip, barra de progreso | M (librería) |
| Tabla de datos con fila de marca del brief, celdas clicables y n bajo | M |
| Barra de punto de control con registro de persona y hora | M |
| Marca de origen (código / IA / humano) | S |
| Indicador de paso degradado y estados En curso / Error / Bloqueado comunes | S |
| Pantalla 0 Inicio con «Cargar demo» y revisor (lista simple) | S |
| Pantalla 1 Ficha (formulario + brief) | M |
| Pantalla 2 Competencia (tabla + avisos + aprobar) | M |
| Pantalla 3 Diagnóstico: conmutador, frase resumen, 4 tarjetas, ranking, marca por motor y ciudad | L |
| Visor de evidencias | L |
| Pantalla 4 Hallazgos: tarjetas problema/fortaleza, evidencias, hipótesis, aprobar | M |
| Pantalla 5 Plan: objetivos, tabla de acciones editable (sin añadir), revalidación de presupuesto y dependencias, Gantt de solo lectura, barra de presupuesto | L |
| Pantalla 6 Propuesta modo cliente: documento, sello, descargas | M |
| Pantalla 7: banda de limitación + tabla por campo + aprobaciones | S |

### 10.2 Deseable

| Elemento | Esfuerzo |
|---|---|
| Mapa de calor marca × motor | S |
| Embudo, Madrid frente a Barcelona, fuentes, consistencia, duelos | M (S cada uno) |
| Calidad de mención asistida | S |
| Matriz esfuerzo / impacto | S |
| Carga del equipo (modo de reserva por acciones simultáneas) | S |
| Simulador what-if | M |
| Modo prospecto (selector, gancho, correo copiable) | M |
| Traza de la ejecución y discrepancias en pantalla 7 | M |
| Vista de tabla en cada gráfico | S |
| Tema oscuro | S |
| Escala «1920» / modo proyector | S |
| Vista 8 de solo lectura (escritorio) | M |
| Copia de seguridad «demo · todo aprobado» | S |

### 10.3 Recortable

| Elemento | Esfuerzo |
|---|---|
| Arrastrar barras en el Gantt | M |
| Matriz de confusión | S |
| Resaltado del pasaje del brief al enfocar un campo (necesita offsets) | M |
| «Añadir acción» en el plan | S |
| Edición de párrafos de la Propuesta en el sitio | M |
| Vista 8 en móvil | S |
| Panel de atajos de teclado | S |
| Exportar CSV desde el visor | S |

### 10.4 Estados mínimos para la demo

En curso · Esperando aprobación · Aprobado · n bajo · Bloqueado. El resto de estados (degradado, error con reintento, incidencias bloqueantes, vacío, sin guardar, conflicto) se implementan con su texto y estilo básicos dentro de los componentes imprescindibles; el conflicto de dependencias del plan es imprescindible porque forma parte del guion.

---

## 11. Verificación

| Punto | Resultado |
|---|---|
| No hay ni una línea de código, CSS ni pseudocódigo | ✔ Cumple. Los valores se dan como datos en tablas; los bloques de texto son wireframes ASCII |
| Todas las cifras, marcas, dominios y ciudades salen de los adjuntos o de la sección 3.6 | ✔ Cumple. Lo que no está en los adjuntos aparece como [dato pendiente] (Anexo A). Hay 4 valores derivados por cálculo directo de los adjuntos, señalados donde aparecen: «Ausente 40,0 %» (100 − 18,8 − 41,2), «−50,0 p. p.» (54,2 − 4,2), «39 / 91 de cada 100» (redondeo de 38,8 % y 90,8 %) y la distribución de la matriz esfuerzo/impacto y de acciones simultáneas (lectura directa de `plan.json`) |
| Pantallas 0-7 (y 8) diseñadas con wireframe, zonas, interacciones, estados y textos | ✔ Cumple. La 8 incluye móvil |
| Componentes de 5.4 con anatomía, medidas, tokens, variantes y estados | ✔ Cumple (4.A y 4.B) |
| Gráficos con tipo justificado, ejes, colores, tooltip, clic y n bajo | ✔ Cumple (5.2-5.10) |
| Colores con hex, token, uso y ratio; texto en AA | ✔ Cumple (3.1.5). Ratios calculados con la fórmula de luminancia relativa de WCAG |
| 4 checkpoints, aprobación rápida, registro de quién y cuándo | ✔ Cumple (4.B.8, pantalla 7 «Aprobaciones») |
| Conmutador espontánea/asistida afecta a todo el Diagnóstico y su estado es siempre visible | ✔ Cumple (cabecera fija, franja de modo, chip en cada gráfico) |
| Visor de evidencias desde todas las cifras del Diagnóstico, Hallazgos y Propuesta | ✔ Cumple |
| Aviso de datos sintéticos en todas las pantallas | ✔ Cumple, incluida la vista 8 y la Propuesta exportada |
| Interfaz en español de España con formato numérico español | ✔ Cumple. Se pide además al backend corregir los formatos mixtos de `propuesta_cliente.md` |
| Sin textos que prometan resultados ni comparativas denigratorias | ✔ Cumple. Las palabras prohibidas solo aparecen en la lista de 7.3 y en el ejemplo ilustrativo del estado de incidencia (4.B.10) |
| La priorización deja claro qué hace falta para la demo de extremo a extremo | ✔ Cumple (10.1 y 10.4) |
| Un desarrollador puede implementar cada pantalla sin preguntas de diseño | ✔ Cumple en lo que depende del diseño. Las preguntas que quedan son de datos (Anexo A), no de diseño |

---

## Anexo A · Datos pendientes que debe aportar el backend

| # | Dato | Dónde se usa | Archivo esperado |
|---|---|---|---|
| 1 | Los 4 sumandos del Score de Citación (aparición, posición, fuerza, fuente) por marca y ámbito | 5.2, tarjeta de score | `metrics.json` |
| 2 | T2 (marca × motor) para las 9 marcas que no son la del brief, y valores asistidos | 5.4 | `tablas/T2` |
| 3 | Embudo del líder (Descubrimiento, Comparación, Validación) y media de competidores por fase | 5.5 | `tablas/T3`, `T11` |
| 4 | Madrid y Barcelona por marca | 5.6 | `tablas/T4` |
| 5 | Perfil de fuentes por marca (salvo Alborada) | 5.7 | `tablas/T6` |
| 6 | Consistencia por marca, tabla de origen, n y valor «ausente» explícito | 5.8 | `tablas/T?` |
| 7 | Nombres de T5, T7, T10 y T12 | Menú «Ver tablas» | `tablas/` |
| 8 | Textos de pregunta (`prompt_ejecutado`), respuestas completas, fuentes y fragmentos por ejecución | Visor de evidencias | corpus de ejecuciones + `evaluaciones.parquet` |
| 9 | Numerador de cada cifra («1 de 24») | Visor, resumen | `tablas/` |
| 10 | Campo `polaridad` del hallazgo (problema / fortaleza) | Pantalla 4 | `findings.json` |
| 11 | Texto del brief original y offsets de extracción por campo | Pantalla 1 | brief + `ficha.json` |
| 12 | Estimación de llamadas, tokens y € por proveedor; modelo usado | Inicio, 4.B.20 | servicio de estimación |
| 13 | `trace.jsonl` completo (duraciones, llamadas, tokens, coste, modelo, versión de prompt, degradado) | Pantalla 7 | `trace.jsonl` |
| 14 | Acierto y kappa por campo, n revisado, matriz de confusión (salvo tipo de fuente 78,2 % global) | Pantalla 7 | informe de validación del juez |
| 15 | Lista y recuento de discrepancias reglas/LLM | Pantalla 7 | `evaluaciones.parquet` (`discrepancia`) |
| 16 | Horas semanales por acción del cliente | 4.B.15 | `plan.json` |
| 17 | Función de simulación del score y margen del rango al «Usar como objetivo» | 4.B.16 | servicio del backend |
| 18 | Contenido de la propuesta de prospecto (gancho, 3 hallazgos, 3 acciones, correo) | Pantalla 6 | `propuesta_prospecto_*.md` |
| 19 | Formato del enlace de solo lectura y caducidad | Pantalla 6 y 8 | · |
| 20 | Tamaño máximo de archivo del brief | 4.A.15 | · |
| 21 | Ruta de la carpeta demo e instrucciones si falta | Inicio | · |
| 22 | Umbral de coste para el aviso de «coste alto» | 4.B.20 | · |
