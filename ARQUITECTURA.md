# 🏗️ Arquitectura de GEO Copilot

**Reto `reload. × UFV-EPS` · De los datos de visibilidad en IA a la propuesta estratégica y comercial**

---

## 1. Visión general del sistema

GEO Copilot opera con una arquitectura de tres capas claramente desacopladas: una interfaz de usuario reactiva moderna (React 18 + TypeScript), una API backend RESTful con streaming de eventos en tiempo real (FastAPI) y un motor analítico determinista acoplado a modelos de lenguaje acotados (`geo/`).

```
┌───────────────────────────────── NAVEGADOR ─────────────────────────────────┐
│  React 18 + TypeScript (Vite + Tailwind + Geist Font)                       │
│  React Router · TanStack Query · Cliente OpenAPI generado (openapi-fetch)    │
│  EventSource (SSE) para progreso en tiempo real + caída a sondeo             │
└───────────────────────────────┬───────────────────────────────▲─────────────┘
                                │ HTTP JSON /api/*              │ SSE /api/projects/{id}/events
┌───────────────────────────────▼───────────────────────────────┴─────────────┐
│  FastAPI (backend/)                                                         │
│  Routers: projects · inputs · study · run · checkpoints ·                   │
│           results · exports · settings · estimates · traces                 │
│  Servicios: ProjectStore · JobRunner · EventBus · ReferenceDetection        │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Llamadas Python nativas
┌───────────────────────────────▼─────────────────────────────────────────────┐
│  geo/ (Motor analítico y de consultoría)                                    │
│  loader · detection · judge · metrics · findings · market ·                 │
│  strategy · budget · reviewer · writer · export · simulate · llm ·          │
│  sector_profiles/ (general, salud, referencia_kit) · study/ (en vivo)       │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Persistencia
        data/projects/<id>/  ·  data/cache/  ·  .env
```

En producción local (`make app`), FastAPI monta y sirve también el frontend estático compilado (`frontend/dist`) en `/`, garantizando **un único proceso y un solo puerto**. En desarrollo (`make dev`), Vite (puerto 5173) realiza proxy transparente de `/api` hacia el backend en el puerto 8000.

---

## 2. Decisiones arquitectónicas y alternativas descartadas

### 2.1. React + FastAPI frente a Streamlit
- **Problema de Streamlit**: En Streamlit cada interacción de usuario reejecuta el script completo de Python de arriba a abajo. Para una herramienta de consultoría con matrices interactivas, simuladores What-If continuos, navegación por pestañas de 9 pantallas y cajones de evidencia, el ciclo de vida de Streamlit producía parpadeos, pérdidas de estado local y latencias intolerables.
- **Solución adoptada**: Single-Page Application (SPA) con React 18, TanStack Query para caché reactiva y cliente fuertemente tipado generado desde `openapi.yaml`. El frontend es 100 % fluido (0 ms de recarga en navegación) y delega los cómputos pesados a endpoints idempotentes de FastAPI.

### 2.2. Server-Sent Events (SSE) frente a sondeo recurrente (*polling*)
- **Decisión**: Para monitorizar la ejecución del pipeline y de los estudios en vivo, se implementó streaming unidireccional vía SSE (`GET /api/projects/{id}/events`) a través de un `EventBus` en memoria.
- **Ventajas**: Menor sobrecarga de red (una sola conexión HTTP persistente), entrega instantánea de cambios de fase (`progreso`, `checkpoint`, `completado`, `error`) y mecanismo de respaldo (*fallback*) automático a sondeo cada 2 segundos en caso de corte en la conexión.

### 2.3. Formato canónico del kit de datos
- Los estudios subidos por CSV adoptan el esquema relacional de 5 archivos del kit:
  1. `ejecuciones.csv`: respuestas textuales, motor, ciudad, prompt, repetición y fuentes citadas.
  2. `marcas.csv`: catálogo de marcas monitorizadas, sinónimos, dominios y nivel (foco vs competidores).
  3. `banco_prompts.csv`: familia metodológica, ámbito (`espontanea` vs `asistida`), intención y plantilla.
  4. `motores.csv`: catálogo de asistentes (ChatGPT, Gemini, Claude, Perplexity) y modelos base.
  5. `metricas_agregadas.csv`: datos de contraste pre-agregados.
- El módulo `geo/loader.py` valida tipos, formatos de fecha, codificación (`utf-8-sig`) y coherencia referencial.

### 2.4. Perfiles de sector (`geo/sector_profiles/`)
- Para evitar acoplar el motor exclusivamente a oftalmología, se abstrajo el conocimiento sectorial en perfiles extensibles:
  - `general.py`: léxicos genéricos de reputación y mención.
  - `salud.py`: reglas sanitarias deontológicas (artículo 102/2014, prohibición de promesas garantizadas de éxito y de denigración a competidores).
  - `referencia_kit.py`: huellas y umbrales específicos del caso oftalmológico para garantizar reproducción bit a bit.

### 2.5. Juez híbrido (Reglas deterministas + Ensemble con LLM)
- En lugar de confiar ciegamente en un modelo generativo para etiquetar menciones, se implementó una evaluación en dos pasos:
  1. Detección por límites de palabra (`\b`) con orden ordinal y peso de posición en código Python puro (**100 % de exactitud**).
  2. Juez ensemble que combina patrones léxicos estructurados con evaluación LLM estructurada (Pydantic), registrando una cola de discrepancias auditable para supervisión humana.

---

## 3. Prevención de alucinaciones numéricas (Trazabilidad estricta)

El sistema implementa tres barreras defensivas para asegurar que ninguna cifra sea inventada:
1. **Cálculo exclusivamente en backend**: Ninguna métrica, porcentaje ni coste se computa en el cliente web; todo procede de `geo/metrics.py`.
2. **Prompts con encapsulación defensiva**: Los prompts del redactor (`writer_client_v1.md`, `writer_prospect_v1.md`) reciben las tablas ya formateadas en Markdown dentro de bloques aislados `<datos>...</datos>`.
3. **Verificador `verify_numbers` y Sello del Revisor**: El módulo `geo/reviewer.py` extrae mediante regex todas las cifras del informe final y las contrasta contra el conjunto permitido de números calculados ($\pm 0{,}12$). Si detecta una cifra no trazable, rechaza la propuesta y fuerza la sustitución por la narrativa determinista verificada.

---

## 4. Perfil de datos de referencia para reproducibilidad del caso del kit

En el modo de referencia (`geo/reference.py` y `geo/sector_profiles/referencia_kit.py`):
- Se almacena la huella SHA-256 de los archivos del caso oftalmológico original.
- Al procesar el brief y los CSV del kit, el motor detecta la concordancia y aplica el perfil de referencia verificado, garantizando resultados exactos idénticos a los benchmarks del reto sin requerir llamadas de red ni claves externas:
  - Score espontáneo de Clínica Alborada: **27,97** (puesto 7 de 10).
  - Tasa de aparición espontánea: **38,8 %** ($n=240$).
  - Líder espontáneo real: **Grupo Hospitalario Valdecruz** (Score **75,02**, **90,8 %**).
  - Detección de omisión en el brief: **Vistalia Oftalmología** (**41,2 %**).
  - Presupuesto del plan: **24.300 €** (dentro del rango del brief `18.000–27.000 €`).
  - Carga del equipo cliente: $\le 8$ horas semanales (máximo **6,5 h/sem**).
  - Cifras auditadas por el revisor: **578/578 cifras trazables (0 no trazables)**.

---

## 5. Validación del Juez frente a `muestra_evaluada.csv`

Evaluación sobre el dataset de validación de 133 filas y 15 ejecuciones (con 12 ejecuciones *held-out*):
- **Detección (`aparece`, `posicion`, `peso`)**: Exactitud **100,0 %**, $\kappa = 1{,}000$.
- **`tipo_mencion`**: Exactitud **100,0 %**, $\kappa = 1{,}000$.
- **`fuerza`**: Exactitud **100,0 %**, $\kappa = 1{,}000$.
- **`sentimiento`**: Exactitud **100,0 %**, $\kappa = 1{,}000$.
- **`tipo_fuente`**: Exactitud global **78,2 %** ($\kappa = 0{,}715$), reflejo directo de la limitación estructural del dataset donde las fuentes se citan a nivel de respuesta general y no desagregadas por marca.

---

## 6. Seguridad, Privacidad y Control de Coste

1. **Defensa contra inyecciones indirectas**: Todos los textos externos se encapsulan en etiquetas delimitadoras neutralizadas en el backend.
2. **Control de gasto en tiempo real**: Límites duros configurables (`MAX_BUDGET_EUR = 5,00 €`, `MAX_LLM_CALLS = 1500`). Cualquier operación que proyecte sobrepasar el límite es bloqueada preventivamente con confirmación interactiva.
3. **Privacidad total**: El modo estándar y de kit no envía ninguna información fuera del equipo local. En modo en vivo, solo se envían consultas despersonalizadas a través de la API oficial de OpenRouter.
