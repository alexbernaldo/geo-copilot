# DESIGN · GEO Copilot

Dirección visual de la web (W1). Escrito por el agente D antes de implementar componentes. Fuentes: Parte A6 y H de la guía, `PRODUCT.md`, skill `design-taste-frontend` (principios aplicables a una herramienta: sin Inter por defecto, un solo acento, bloqueo de radios, sin guiones largos ni emojis) y reglas de movimiento de `emil-design-eng`.

Nota de herramientas: la versión instalada de Taste Skill declara fuera de alcance los paneles y no trae ruta de aplicación. Se han aplicado sus reglas generales y se han razonado a mano las tres direcciones de abajo.

## Lectura del encargo

Herramienta de trabajo para un consultor que defiende cifras ante un comité. Aplicación densa pero calma, tablas y gráficos, sin decoración. Diales: varianza 3, movimiento 2, densidad 7.

## Las tres direcciones consideradas

### 1. Libro mayor (ELEGIDA)
Papel gris azulado muy claro, líneas finas de 1 px, interfaz monocromática (negro tinta) y **el color reservado para los datos**. Cifras en tipografía monoespaciada con tabulares. Tarjetas solo cuando la elevación significa algo; el resto se agrupa con filetes y espacio.
- Tipografía: Geist (interfaz) y Geist Mono (cifras, identificadores), servidas en local con `@fontsource-variable`.
- Marca del proyecto azul, líder naranja, espontánea verde azulado, asistida ciruela, resto neutro.
- Densidad: alta (filas de 32 a 36 px, texto 13 px en tablas).

### 2. Consola (segunda mejor)
Oscuro primero, estética de terminal: mono en todo, acento neón contenido, paneles sin borde con contraste de superficie.
- Descartada: el modo claro pierde identidad, el mono continuo cansa al leer los párrafos de la Propuesta y el neón compite con los colores de datos.

### 3. Boletín
Editorial: serif en títulos, columnas anchas, fondo cálido.
- Descartada: la propuesta es un documento de lectura, pero el 80 % del producto son tablas y gráficos; el serif y el fondo cálido restan precisión y caen en el patrón genérico de «consultoría elegante».

### Por qué Libro mayor sirve al consultor
Cada cifra tiene que poder defenderse. La interfaz monocroma deja que el único color que ve el ojo sea semántico (quién es la marca, quién el líder, qué ámbito). Con las cifras en mono tabular las columnas se leen en vertical y se comparan de un vistazo. Los filetes finos dan estructura sin ruido, y la densidad permite ver una tabla T1 completa sin desplazarse.

## Tokens

Definidos como variables CSS en `frontend/src/styles/tokens.css`. Claro por defecto, oscuro con `prefers-color-scheme` o `data-theme="dark"` (conmutador manual en la cabecera; `data-theme="light"` fuerza claro).

### Color

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--bg` | `#f6f7f9` | `#0f1217` | Fondo de página |
| `--surface` | `#ffffff` | `#161a21` | Paneles |
| `--surface-2` | `#eef0f4` | `#1d222b` | Filas alternas, cabeceras de tabla |
| `--border` | `#dfe3e9` | `#2a303b` | Filetes |
| `--border-strong` | `#c5ccd6` | `#3a4250` | Controles |
| `--fg` | `#151a22` | `#e9ecf1` | Texto |
| `--fg-muted` | `#566070` | `#9aa4b3` | Texto secundario |
| `--ink` | `#151a22` | `#e9ecf1` | Botón primario (fondo) |
| `--ink-fg` | `#ffffff` | `#0f1217` | Texto del botón primario |
| `--focus` | `#1d5fd1` | `#6fa0f2` | Anillo de foco |
| `--brand-project` | `#1d5fd1` | `#6fa0f2` | Marca del proyecto en gráficos |
| `--brand-leader` | `#c2570c` | `#f0974f` | Líder |
| `--brand-neutral` | `#8b95a3` | `#6b7685` | Resto de marcas |
| `--spont` | `#0f766e` | `#4cc2b5` | Ámbito espontáneo |
| `--assist` | `#7b4a9e` | `#c19be0` | Ámbito asistido |
| `--good` | `#18794e` | `#5ccf98` | Correcto |
| `--warn` | `#a15c07` | `#f2b24d` | Aviso, esperando revisión |
| `--bad` | `#b42318` | `#f28b82` | Error |
| `--info` | `#2f5aa8` | `#8db1ee` | Información, IA |

Cada color semántico tiene su variante `-soft` (fondo de chip, mezcla al 12 % con la superficie). El texto sobre fondo normal cumple 4,5:1; los colores de datos se usan además con etiqueta de texto, nunca como única señal.

### Tipografía

- Interfaz: `Geist Variable`, fallback `system-ui`. Cifras y códigos: `Geist Mono Variable`.
- Escala (px / interlineado): `--text-xs` 11/16, `--text-sm` 13/20 (tablas), `--text-base` 14/22 (cuerpo), `--text-md` 16/24, `--text-lg` 20/28 (títulos de panel), `--text-xl` 26/32 (título de página), `--text-kpi` 28/32 mono.
- Pesos 400, 500, 600. Sin mayúsculas con tracking salvo etiquetas de KPI.

### Espaciado, radios, sombras, foco

- Base de 4 px: `--s-1` 4, `--s-2` 8, `--s-3` 12, `--s-4` 16, `--s-5` 24, `--s-6` 32, `--s-7` 48.
- Radios (regla única): controles y chips `6px`, paneles `10px`, cajones/diálogos `12px`. Sin pastillas.
- Sombras teñidas del fondo, solo en capas flotantes (`--shadow-pop`, `--shadow-drawer`).
- Foco: anillo de 2 px `--focus` con desfase de 2 px, siempre visible con teclado (`:focus-visible`).

### Movimiento (tokens de H2.1)

| Token | Valor |
|---|---|
| `--ease-out` | `cubic-bezier(0.23, 1, 0.32, 1)` |
| `--ease-move` | `cubic-bezier(0.77, 0, 0.175, 1)` |
| `--ease-drawer` | `cubic-bezier(0.32, 0.72, 0, 1)` |
| `--dur-press` | `120ms` |
| `--dur-tip` | `150ms` |
| `--dur-menu` | `180ms` |
| `--dur-modal` | `240ms` |
| `--dur-drawer` | `320ms` |

Reglas: sin `ease-in`; nada nace de `scale(0)` (se empieza en `0.96` con opacidad 0); solo `transform` y `opacity`; los pulsables hacen `scale(0.97)` en `:active`; hover solo con `@media (hover: hover) and (pointer: fine)`; con `prefers-reduced-motion: reduce` se quitan desplazamientos y escalados y se conservan opacidad y color. Sin animación en cambios de pestaña, filtros ni conmutador de ámbito.

## Identidad constante

- **Espontánea / asistida:** chip y marca de borde (`border-top`) en `--spont` y `--assist` en KpiStrip, ScopeToggle y gráficos. Nunca se mezclan en un mismo gráfico.
- **Marca del proyecto y líder:** `useBrandColors` devuelve `--brand-project`, `--brand-leader` o `--brand-neutral`; el tema de ECharts resuelve esas variables a hexadecimal en tiempo de ejecución y se recrea al cambiar de tema.
- **Puntos de control:** `CheckpointBar` y el chip del `PageHeader` usan `--warn` (pendiente) y `--good` (aprobado); nunca se omiten.
- **Origen:** `OriginTag` con texto fijo de la regla 0.1; no usa color de acento propio, solo `info` para IA.

## Componentes y estados

Todos con estados por defecto, hover, foco, activo, deshabilitado, cargando, vacío y error cuando aplica. Detalle vivo en `/_kit` (solo desarrollo).

## Decisiones discutibles (para la revisión del equipo)

1. Interfaz monocroma: el botón primario es negro tinta, no azul. El azul queda para la marca del proyecto en gráficos.
2. Fondo gris azulado frío frente a blanco puro.
3. Texto de tablas a 13 px.
4. Asistida en ciruela: puede confundirse con un acento si se ve aislada; siempre va con etiqueta.
5. Conmutador de tema manual además del sistema.
6. Sin iconos decorativos: solo `lucide-react` (ya en las dependencias del contrato) para flechas, cierre y avisos, con trazo único de 1,5.
