# 🧭 GEO Copilot · Auditoría y Estrategia de Visibilidad en Motores de IA

**Reto `reload. × UFV-EPS`**

GEO Copilot es una plataforma web completa (**FastAPI + React 18 + TypeScript + Tailwind**) que transforma los datos de presencia de marcas en motores conversacionales (**ChatGPT, Gemini, Perplexity y Claude**) y el briefing de un cliente (o una marca en frío) en un diagnóstico riguroso, un plan estratégico a 12 meses y una propuesta comercial ejecutiva verificada y auditable.

---

## 1. Requisitos e Instalación

### Requisitos previos
- **Python 3.11+** (probado en 3.11 y 3.13)
- **Node.js 18+** y `npm`

### Instalación en un paso
```bash
make install
```
Este comando crea el entorno virtual `.venv`, instala las dependencias de Python y ejecuta `npm ci` en `frontend/`.

O bien manualmente:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm ci && cd ..
```

---

## 2. Puesta en marcha

### Modo aplicación (Producción local lista para demo)
```bash
make app
```
Compila el frontend (si no está ya compilado en `frontend/dist`), inicia el servidor FastAPI en el primer puerto libre (a partir del 8000), comprueba `/api/health` y abre la interfaz en el navegador en modo aplicación.

### Modo desarrollo (Backend con recarga + Vite HMR)
```bash
make dev
```
- Backend FastAPI en `http://localhost:8000` (con documentación Swagger en `/api/docs`).
- Frontend Vite con hot-reload en `http://localhost:5173` (con proxy automático hacia `/api`).

---

## 3. Configuración inicial (Ajustes)

Al arrancar la aplicación por primera vez, navega a la sección **Ajustes** en la barra lateral:
1. **Clave de OpenRouter (opcional)**: Introduce tu API key `sk-or-v1-...` y pulsa **Probar conexión**. La aplicación verificará latencia, gasto acumulado y límite de saldo.
   - *Sin clave*: El sistema opera en modo seguro con los datos precalculados del kit o datos sintéticos de referencia.
   - *Con clave*: Permite ejecutar estudios en vivo y re-redactar propuestas con modelos reales.
2. **Modelos por rol**: Asigna el modelo LLM para cada tarea:
   - Juez y extracción: `google/gemini-2.5-flash`
   - Estrategia y redacción final: `anthropic/claude-sonnet-4.5`
   - Propuesta de marcas y banco: `google/gemini-2.5-flash`
   - Motores para estudio en vivo: ChatGPT (`openai/gpt-4o`), Gemini, Claude y Perplexity.
3. **Límites y control de gasto**:
   - Tope de gasto por proyecto (por defecto 5,00 €).
   - Llamadas máximas (1500) y concurrencia (8).

---

## 4. Flujo de trabajo

### Caso 1 · Proyecto con datos CSV (Kit del reto)
1. Pulsa **«Nuevo proyecto»** en la pantalla principal.
2. **Paso 1**: Elige tipo **Cliente (tengo su brief)** y asigna un nombre (o déjalo automático).
3. **Paso 2**: Sube el brief en formato `.docx` o `.md` (p. ej. `Brief_de_ejemplo_Clinica_Alborada.docx`) o pega su contenido. El extractor analiza el documento y previsualiza la ficha de la marca y campos faltantes.
4. **Paso 3**: En la pestaña **Subir datos del estudio (CSV del kit)**, sube los 5 archivos CSV del kit (`ejecuciones.csv`, `marcas.csv`, `banco_prompts.csv`, `motores.csv`, `metricas_agregadas.csv`). El validador confirma las 624 ejecuciones, 4 motores y 3 repeticiones.
5. **Paso 4**: Elige el modo de revisión (**Parar en cada punto de control** o continuo) y pulsa **Lanzar análisis**.
6. Durante la ejecución podrás revisar y aprobar los 4 puntos de control:
   - **Punto 0**: Ficha técnica del cliente y restricciones presupuestarias.
   - **Punto 1**: Contraste de competidores (detecta que el líder real en IA es Valdecruz y que el brief omitía a Vistalia).
   - **Punto 2**: Hallazgos clave priorizados con acceso directo a evidencias textuales.
   - **Punto 3**: Plan estratégico con matriz esfuerzo/impacto, calendario semanal, simulador What-If y propuesta exportable en `.docx`.

### Caso 2 · Estudio en vivo con IA
1. En el asistente, crea un proyecto de tipo **Prospecto** (o Cliente).
2. En el Paso 3, selecciona la pestaña **Generar estudio en vivo con IA**.
3. Pulsa **Proponer marcas** y **Proponer banco** para derivar automáticamente competidores y preguntas del sector.
4. Selecciona el tamaño del estudio:
   - **Rápido**: 1 repetición, prompts clave (~0,15 €).
   - **Estándar**: 2 repeticiones (~0,50 €).
   - **Completo**: 3 repeticiones y matriz completa (~1,20 €).
5. Confirma la estimación de coste y lanza el análisis.

---

## 5. Costes orientativos y seguridad presupuestaria

- **Ejecución con dataset del kit / referencia**: Coste de API: **0,00 €** (0 llamadas externas).
- **Estudio en vivo «Rápido» (OpenRouter)**: Entre **0,10 € y 0,25 €** según modelos seleccionados.
- **Auditoría completa + Redacción**: Menos de **0,40 €** por ejecución.
- **Protección de gasto**: El backend bloquea llamadas si la estimación o el acumulado superan el tope configurado (`MAX_BUDGET_EUR = 5,00 €`) o el número máximo de llamadas (`1.500`).

---

## 6. Verificación y Tests

```bash
# Suite completa: backend (pytest) + frontend (vitest + typecheck)
make test

# Solo backend
.venv/bin/pytest -q

# Solo frontend
cd frontend && npm run typecheck && npm test
```

---

## 7. Solución de problemas comunes

- **Puerto en uso**: `make app` detecta automáticamente puertos ocupados y se vincula al siguiente disponible (8000, 8001...).
- **El frontend no carga o muestra página en blanco**: Ejecuta `make build` para regenerar la compilación estática en `frontend/dist`.
- **Falta la clave de OpenRouter**: La plataforma puede utilizarse íntegramente con los archivos del kit del reto sin ninguna clave configurada. Para análisis en vivo, añade tu clave en la pantalla de Ajustes.
- **Error en subida de CSV**: Comprueba que los archivos CSV tengan codificación UTF-8 y contengan las columnas mínimas especificadas en `contracts/openapi.yaml`.
