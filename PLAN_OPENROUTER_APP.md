# PLAN · GEO Copilot con LLM reales (OpenRouter) y experiencia de aplicación · versión multiagente

Plan de trabajo para Claude Code sobre el repositorio actual de GEO Copilot (reto reload. × UFV-EPS). Sigue el formato de `PLAN.md`: cada fase tiene objetivo, archivos, especificación, prompt listo para pegar, criterios de aceptación y tests. Está organizado para que varios agentes de Claude Code trabajen a la vez (sección M).

Alcance:
- **Sí:** todas las piezas que hoy llaman a un LLM (intake, juez, estrategia, redactor, revisor normativo) pasan a funcionar de verdad con OpenRouter, con una sola clave. La interfaz se comporta como una aplicación: ajustes, lanzador de análisis, progreso en vivo, historial y estado de conexión.
- **Sí:** los datos de entrada siguen siendo los del kit (`ejecuciones.csv` y el resto de CSV, brief de Alborada o brief subido). Las 624 respuestas no se regeneran.
- **Opcional (G9):** el mini-estudio en vivo de los motores pasa por OpenRouter. Va aislado del kit, como ya exige F15.
- **No:** cambiar los contratos de `geo/schemas.py`, la fórmula del score, las reglas de hallazgos ni el detector. Las cifras las sigue calculando el código.

---

## 0. Cómo usar este plan

Este plan se ejecuta **en paralelo con varios agentes de Claude Code**, cada uno en su propia copia del repo (git worktree) y con archivos asignados en exclusiva. La sección M explica quién hace qué, cuándo se lanza cada agente y cómo se integra. Las fases G0-G12 (secciones 5 en adelante) son la especificación técnica que cada agente lee.

1. Copia este archivo en la raíz del repo como `PLAN_OPENROUTER.md`.
2. El agente líder añade al final de `CLAUDE.md` (lo hace su prompt, pero conviene saberlo):
   ```markdown
   - Plan activo: PLAN_OPENROUTER.md (fases G0-G12, sección M para el reparto). PLAN.md queda como referencia histórica.
   - Trabajas como UN agente del equipo. Toca solo los archivos de tu fila en la matriz M3. El resto es de solo lectura.
   - Los contratos de coord/CONTRATOS.md no se cambian. Si necesitas cambiar uno, para y escríbelo en coord/peticiones/<tu-agente>.md.
   - Proveedor real único: OpenRouter. Nunca llamar a la red en tests: usar scripts/fake_openrouter.py o monkeypatch.
   - La clave OPENROUTER_API_KEY solo vive en .env. Jamás en código, logs, trazas, state.json ni capturas.
   ```
3. Cada agente trabaja en su rama `ag/<letra>-<nombre>`, hace commits pequeños con el prefijo de su fase (`G3: ...`) y no hace merge a `main`: eso lo hace el líder en los puntos de integración.
4. Si un agente rompe tests que no son suyos, para y lo reporta. No arregla archivos ajenos.
5. Si falta tiempo, el orden de sacrificio es: G9 → G10 → G12 → pulido de G7. Lo que no se toca: C0, G1-G6 y G8.

---

## M. Organización multiagente

### M1. Por qué así

La forma secuencial (G0 → G12) tiene una cadena crítica de ~9 h. Casi todo el trabajo depende solo de **interfaces**, no de implementaciones: la UI necesita saber qué devuelve `jobs.read_progress()`, no cómo funciona el hilo; el juez necesita las excepciones de `llm.py`, no el cliente HTTP. Si el líder fija esas interfaces primero (fase **C0, contratos**) con stubs que ya funcionan en mock, cinco agentes pueden construir a la vez y la cadena crítica baja a ~4 h 30.

Tres reglas sostienen el paralelismo:
1. **Contratos congelados.** Firmas, excepciones, formato de `progress.json`, protocolo del servidor falso y puntos de enganche de la UI se fijan en C0 y viven en `coord/CONTRATOS.md`. Nadie los cambia salvo el líder.
2. **Propiedad exclusiva de archivos.** Cada archivo tiene un solo agente con permiso de escritura (matriz M3). Así los merges no chocan.
3. **Stubs que funcionan.** Tras C0, `main` arranca y los tests pasan: los módulos nuevos existen, con lo mínimo para el modo mock y `NotImplementedError` solo donde nadie depende todavía.

### M2. Los agentes

| Agente | Nombre | Fases | Persona que lo supervisa | Ola de lanzamiento |
|---|---|---|---|---|
| **L** | Líder e integrador | G0, C0, integraciones I1-I3, `real_smoke` en el Mac | Alejandro | Ola 0 (solo) |
| **A** | Núcleo LLM | G1, G2 (cliente), G3 | Persona 1 | Ola 1 |
| **B** | Juez y orquestador | G4, G5 | Persona 1 | Ola 1 |
| **C** | Ejecución y herramientas | G2 (servidor falso completo), G6, G11 (script), G10 | Persona 2 | Ola 1 |
| **D** | UI · marco y Ajustes | G7 | Persona 3 | Ola 1 |
| **E** | UI · análisis, progreso e historial | G8 | Persona 4 | Ola 1 |
| **F** | Motores en vivo (opcional) | G9 | Persona 2 | Ola 2 |
| **Q** | Verificador independiente | QA de extremo a extremo | Persona 3 | Ola 3 |
| **H** | Documentación | G12 | Persona 4 | Ola 3 |

**Q no ha visto el código mientras se escribía**: se lanza en una sesión limpia, solo con este plan y el repo integrado, para que la revisión no la haga quien construyó.

Con 4 personas, cada una supervisa como mucho 2 agentes a la vez. La persona no programa: lee los planes que propone su agente (modo plan, Shift+Tab), aprueba, vigila que no toque archivos ajenos y avisa al líder cuando su agente termina.

### M3. Matriz de propiedad de archivos

`E` = escribe (exclusivo). `L` = lee. `—` = no lo necesita. **Ningún agente escribe en un archivo que no tenga marcado con E.**

| Archivo | L | A | B | C | D | E | F | Q | H |
|---|---|---|---|---|---|---|---|---|---|
| `coord/CONTRATOS.md`, `CLAUDE.md`, `requirements.txt`, `.gitignore`, `tests/conftest.py` | E | L | L | L | L | L | L | L | L |
| `.env.example` | — | E | — | — | L | L | — | — | L |
| `geo/settings.py` | stub | E | L | L | L | L | L | — | — |
| `geo/openrouter.py` | stub | E | L | L | L | L | L | — | — |
| `geo/llm.py`, `geo/writer.py` (solo resolución de modelo) | stub | E | L | L | — | — | — | — | — |
| `geo/judge_llm.py`, `geo/judge.py` | stub | — | E | — | — | — | — | — | — |
| `geo/orchestrator.py` | stub | — | E | L | — | L | — | — | — |
| `geo/jobs.py` | stub | — | L | E | — | L | — | — | — |
| `scripts/fake_openrouter.py`, `tests/fixtures/fake_openrouter/*` | stub | L | L | E | L | L | L | L | — |
| `tests/fixtures/progress/*.json` | E | — | — | L | — | L | — | — | — |
| `scripts/real_smoke.py`, `scripts/geo_copilot.py`, `GEO Copilot.command`, `Makefile` | — | — | — | E | — | — | — | L | L |
| `.streamlit/config.toml`, `app/Home.py`, `app/ui_shared.py`, `app/pages/8_Ajustes.py` | stub | — | — | — | E | L | — | L | — |
| `app/ui_jobs.py` (nuevo: `render_progress`, `guard_active_run`) | stub | — | — | — | L | E | — | L | — |
| `app/pages/00_Nuevo_analisis.py`, `app/pages/9_Historial.py`, `app/pages/0_Inicio.py`, `5_Plan.py`, `6_Propuesta.py` | — | — | — | — | — | E | — | L | — |
| `app/pages/7_Calidad_y_trazas.py` (líneas 1-140) | — | — | — | — | — | E | — | L | — |
| `app/pages/7_Calidad_y_trazas.py` (sección «Conectores en vivo», al final) | — | — | — | — | — | — | E | L | — |
| `geo/engines/*` | — | — | — | — | — | — | E | — | — |
| Tests nuevos de cada agente (`tests/test_<su_modulo>.py`) | — | E | E | E | — | E | E | E (`tests/e2e/`) | — |
| `README.md`, `ARQUITECTURA.md`, `RESUMEN_IMPLEMENTACION.md` | — | — | — | — | — | — | — | — | E |

Nota sobre `ui_shared.py`: lo posee **D**. E no lo toca: pone sus componentes en `app/ui_jobs.py`. En C0 el líder deja en `shell()` una llamada a `ui_jobs.guard_active_run()` (que de momento no hace nada), para que D y E no tengan que coordinarse.

Nota sobre `7_Calidad_y_trazas.py`: E solo borra la llamada implícita a `run_all()` (línea ~20). F solo toca la sección final. Se integra primero E y después F.

### M4. Fase C0 · Contratos y stubs (agente L, antes que nadie)

**Duración objetivo:** 40-50 min. Es la única fase que bloquea a todos, así que se mantiene mínima.

**Entregables:**
1. G0 completo (repo con git, `conftest.py` que genera `runs/demo/`, tests en verde).
2. `coord/CONTRATOS.md` con las firmas exactas de la sección M5.
3. Stubs que compilan y no rompen nada:
   - `geo/settings.py` **completo** (es pequeño y todos lo usan; mejor hacerlo ya que dejarlo a medias).
   - `geo/openrouter.py`: `OpenRouterError`, `ChatResult` y las firmas; `list_models()` devuelve una lista fija de 4 modelos de ejemplo si `OPENROUTER_BASE_URL` apunta a `127.0.0.1`; el resto lanza `NotImplementedError`.
   - `geo/llm.py`: añadir `LLMConfigError` y `resolve_model()` reales (son 20 líneas); el resto sin tocar.
   - `geo/judge_llm.py` y `geo/judge.py`: añadir el parámetro `on_progress=None` (ignorado por ahora) y `JUDGE_LAST_RUN = {}`.
   - `geo/orchestrator.py`: atributos `on_event = None`, `on_progress = None`, método `_emit()` vacío y `estimate()` que devuelve un diccionario con la forma correcta y ceros.
   - `geo/jobs.py`: `read_progress()` y `list_runs()` **reales** (solo leen ficheros); `start()`, `is_running()` y `any_running()` como stubs (`start()` lanza `NotImplementedError`, los otros devuelven `False`/`None`).
   - `scripts/fake_openrouter.py` **mínimo**: `/models`, `/key` y `/chat/completions` con respuesta del juez y `usage.cost`. C le añade luego modos de fallo y fixtures.
   - `tests/fixtures/progress/{running,done,error,interrupted,degraded}.json` con el formato de G6, para que E construya la UI de progreso sin esperar a C.
   - `app/ui_jobs.py` con `render_progress(run_id)` y `guard_active_run()` vacías, y la llamada a `guard_active_run()` ya puesta en `shell()`.
   - Páginas vacías `00_Nuevo_analisis.py`, `8_Ajustes.py` y `9_Historial.py` registradas en `Home.py` con `render_empty(...)`.
4. Puertos reservados para que los agentes no se pisen al arrancar servidores:

   | Agente | Streamlit | Servidor falso |
   |---|---|---|
   | D | 8511 | 8761 |
   | E | 8512 | 8762 |
   | C | — | 8763 |
   | F | 8514 | 8764 |
   | Q | 8515 | 8765 |
   | L | 8501 | 8760 |

5. Etiqueta `git tag contratos-v1` y commit `C0: contratos y stubs`.

**Prompt del agente L (C0):**
```
Eres el agente L (líder e integrador) del equipo descrito en PLAN_OPENROUTER.md, sección M.
Lee las secciones 0, M, 1, 2, 3 y 4, y las fases G0, G1 y G6 para los formatos.
Tu tarea ahora es solo G0 + C0 (sección M4). No implementes lógica de otros agentes: deja stubs.
1. Haz G0 completo.
2. Crea coord/CONTRATOS.md copiando las firmas de M5 tal cual, y coord/peticiones/ vacía (con un .gitkeep).
3. Crea los stubs de M4 punto 3. geo/settings.py va completo, con sus tests (G1).
4. Crea las 5 fixtures de progreso con el formato de G6.
5. Registra en app/Home.py las páginas nuevas y pon la llamada a ui_jobs.guard_active_run() en shell().
6. Comprueba: rm -rf runs cache && pytest -q en verde; streamlit run app/Home.py --server.port 8501 arranca y las páginas nuevas muestran su estado vacío.
7. Commit "C0: contratos y stubs" y git tag contratos-v1.
Al terminar, imprime la lista de archivos creados y los comandos de la sección M6 para lanzar la ola 1.
```

### M5. Contratos (contenido de `coord/CONTRATOS.md`)

```python
# ---- geo/settings.py (L, completo en C0) ----
ENV_PATH: Path; DEFAULTS: dict[str, str]; SECRET_KEYS: set[str]
def get(key: str) -> str
def get_int(key: str) -> int
def get_float(key: str) -> float
def current() -> dict[str, str]
def save(values: dict[str, str]) -> Path
def mask(secret: str) -> str
def has_openrouter_key() -> bool

# ---- geo/openrouter.py (A) ----
class OpenRouterError(RuntimeError):
    status: int | None; retryable: bool
@dataclass
class ChatResult:
    text: str; model: str; tokens_in: int; tokens_out: int
    cost_usd: float | None; citations: list[str]; raw: dict
def chat(messages: list[dict[str, str]], *, model: str, temperature: float = 0.0,
         json_mode: bool = False, web_search: bool = False, max_tokens: int | None = 4096,
         api_key: str | None = None, retries: int = 4) -> ChatResult
def list_models(force: bool = False) -> list[dict]   # claves: id, name, price_in_per_m, price_out_per_m, context
def model_price(model_id: str) -> tuple[float, float] | None
def key_info(api_key: str | None = None) -> dict     # label, usage, limit, is_free_tier
def test_connection(model: str, api_key: str | None = None) -> dict  # key, model, latency_s, reply, cost_usd

# ---- geo/llm.py (A) ----
class LLMConfigError(RuntimeError): ...          # no recuperable: sin clave, 401, 402, 403, 404
class LLMProviderError(RuntimeError): ...        # recuperable (ya existe)
class LLMCallLimitError(RuntimeError): ...       # tope de llamadas o de gasto (ya existe)
def resolve_model(provider: str, prompt_version: str, model: str | None = None) -> str
def estimate_cost_for_model(model: str, tok_in: int, tok_out: int) -> float   # €
def get_llm_stats() -> dict   # añade: cost_is_real: bool; estimated_cost_eur pasa a ser coste real si lo hay
# complete_json(): firma intacta; acepta provider="openrouter"

# ---- geo/judge_llm.py / geo/judge.py (B) ----
JUDGE_LAST_RUN: dict[str, object]   # llamadas, fallos, ejemplos_fallo
def judge_llm(..., on_progress: Callable[[int, int], None] | None = None) -> pd.DataFrame
def judge_ensemble(..., on_progress: Callable[[int, int], None] | None = None) -> pd.DataFrame
def estimate_judge_llm_workload(df_detection, ejecuciones, model: str | None = None) -> dict

# ---- geo/orchestrator.py (B) ----
class Run:
    on_event: Callable[[str, str, dict], None] | None    # estado ∈ start | degraded | done | error
    on_progress: Callable[[str, int, int], None] | None   # (paso, hechos, total)
    def estimate(self) -> dict   # {"pasos": {paso: {"llamadas": int, "eur": float}}, "total_llamadas": int, "total_eur": float, "minutos": float}
# state.json añade: "models": {...}, "degradados": {paso: mensaje}
# trace.jsonl añade por paso: provider, cost_is_real, model real del paso, y en judge: juez_llm

def estimate_pipeline(provider: str, models: dict[str, str] | None = None) -> dict   # misma forma que Run.estimate(), sin crear carpeta

# ---- geo/jobs.py (C; read_progress y list_runs reales en C0) ----
def start(*, modo: str, provider: str, brief_path: str | Path | None,
          marca_prospecto: str | None, meta: dict | None = None) -> str
def is_running(run_id: str) -> bool
def any_running() -> str | None
def read_progress(run_id: str) -> dict | None
def list_runs() -> list[dict]   # run_id, marca, modo, provider, created_at, status, cost_eur, degradados
# progress.json: formato exacto de G6

# ---- app/ui_jobs.py (E) ----
def render_progress(run_id: str) -> None   # fragmento que se refresca cada segundo
def guard_active_run() -> None             # llamada desde shell(); puede hacer st.stop()

# ---- scripts/fake_openrouter.py (C; mínimo en C0) ----
# python scripts/fake_openrouter.py --port N
# GET /models, GET /key, POST /chat/completions
# FAKE_OR_FAIL = 401 | 402 | 429_once | 500_always | bad_json
# Respuestas no-juez: tests/fixtures/fake_openrouter/<prompt_version>.json (si falta: {})
```

### M6. Cómo lanzar los agentes

**Opción A (recomendada con 4 personas): una terminal de Claude Code por agente, cada una en su worktree.**

El líder, tras C0, crea los worktrees:
```bash
cd geo-copilot
for a in A-nucleo B-juez C-ejecucion D-ui-ajustes E-ui-analisis; do
  git worktree add "../gc-$a" -b "ag/$a" contratos-v1
  ln -s "$PWD/.venv" "../gc-$a/.venv"          # un único entorno virtual compartido
  cp .env.example "../gc-$a/.env"              # sin clave real: los agentes no la necesitan
done
```
Cada persona abre su terminal:
```bash
cd ../gc-A-nucleo && claude
```
y pega el prompt de lanzamiento de su agente (M8). `runs/` y `cache/` son locales a cada worktree, así que no se pisan.

**Opción B (si estás solo): un orquestador con subagentes.** En la sesión del líder, después de C0:
```
Lanza en paralelo, en segundo plano y cada uno con isolation "worktree", los agentes A, B, C, D y E
con los prompts de la sección M8 de PLAN_OPENROUTER.md (uno por agente, copiados literalmente).
No escribas código tú. Cuando cada uno termine, resume qué archivos tocó y si sus tests pasan,
comprueba con `git diff --name-only contratos-v1` que solo tocó archivos de su fila en M3,
y avísame para hacer la integración I1.
```
Con la opción B pierdes la supervisión humana de los planes, así que conviene revisar a mano el diff de cada agente antes de integrar.

### M7. Calendario de lanzamiento

T = momento en que empieza C0. Duraciones orientativas para una tarde de hackathon.

```
T+0:00 ──── OLA 0 ───────────────────────────────────────────────────────────
           L: G0 + C0 (contratos, stubs, fixtures, puertos)             [bloquea a todos]
T+0:45 ──── OLA 1 (5 agentes a la vez) ──────────────────────────────────────
           A: G1 tests → G2 cliente → G3 llm.py              (≈ 1 h 45)
           B: G4 juez paralelo (contra stubs de A) → G5       (≈ 1 h 45)
           C: servidor falso completo → G6 jobs → fixtures    (≈ 1 h 30)
           D: G7 config.toml, shell(), Ajustes                (≈ 2 h)
           E: G8 Nuevo análisis, ui_jobs, Historial           (≈ 2 h 30, usa fixtures de progreso)
T+2:15 ──── I1 · integración del backend (L) ────────────────────────────────
           merge A → C → B en main · pytest · run_pipeline real contra el falso
           HITO: pipeline completo con provider=openrouter y 0 pasos degradados (contra el falso)
T+2:30 ──── OLA 2 ───────────────────────────────────────────────────────────
           D y E: rebase sobre main y sustituir stubs por las piezas reales
           F (opcional, si C ha terminado y hay persona libre): G9 motores en vivo
           C: G11 script real_smoke + G10 lanzador
           L: en el Mac, Ajustes con clave real → mini-run del juez (céntimos)
T+3:45 ──── I2 · integración de la UI (L) ───────────────────────────────────
           merge D → E → F · pytest · arranque manual de la app
T+4:00 ──── OLA 3 ───────────────────────────────────────────────────────────
           Q: verificación de extremo a extremo en sesión limpia (≈ 45 min)
           H: documentación G12 (≈ 45 min; huecos de cifras como PENDIENTE)
           L: real_smoke completo en el Mac → runs/demo_real/ + cache/
T+4:45 ──── I3 · arreglos del informe de Q (agente dueño de cada archivo) ────
           cada fallo de Q vuelve al agente dueño del archivo, no lo arregla Q
T+5:15 ──── H rellena las cifras PENDIENTE con demo_real · congelación ──────
```

**Cadena crítica:** C0 → A (G3) → I1 → E rebase → I2 → Q → I3. Si A se retrasa, B, C y D siguen contra stubs y no se paran.

**Puntos de control del líder (cuándo mirar):**
- T+1:15: ¿A tiene `chat()` con tests? Si no, B sigue con monkeypatch y no espera.
- T+1:45: ¿C tiene `jobs.start()` en mock? E lo necesita en la ola 2.
- T+2:15: si I1 no pasa en 20 min, se integra lo que pase y lo demás vuelve a su agente con el error.
- T+3:45: si la UI no integra, la demo se hace con la UI actual + pipeline real desde CLI y `runs/demo_real/` abierto con «Cargar demo» modificado. Es el plan B.

### M8. Prompts de lanzamiento de cada agente

Todos empiezan igual para fijar el rol. Se pegan tal cual en la terminal del worktree correspondiente.

**Cabecera común (va al principio de cada prompt):**
```
Eres el agente <X> del equipo de PLAN_OPENROUTER.md. Lee la sección M entera, coord/CONTRATOS.md y las secciones 1-4.
Solo puedes escribir en los archivos marcados con E para tu agente en la matriz M3. Todo lo demás es de solo lectura.
No cambies ninguna firma de coord/CONTRATOS.md. Si la necesitas cambiar, escribe la petición en coord/peticiones/<X>.md y sigue con lo que puedas.
No hagas merge ni rebase de main salvo que el líder te lo pida. Commits pequeños con el prefijo de tu fase.
Antes de terminar: pytest -q en verde y `git diff --name-only contratos-v1` solo con archivos tuyos.
Termina con un informe de 10 líneas: qué hiciste, qué falta, qué riesgos ves, y qué necesita el líder para integrar.
```

**Agente A · Núcleo LLM (ola 1):**
```
[cabecera común con X = A]
Tu trabajo: G1 (solo completar los tests si el líder dejó alguno pendiente), G2 (el cliente geo/openrouter.py; el servidor falso es del agente C, solo lo usas) y G3.
Orden: G2 con sus tests → G3 con sus tests.
En G3 respeta la firma de complete_json() y los nombres de excepciones de CONTRATOS.md: el agente B ya está programando contra ellos.
Para probar contra HTTP real usa el servidor falso en el puerto 8760 si C aún no lo ha ampliado (arráncalo tú con la versión mínima de C0).
```

**Agente B · Juez y orquestador (ola 1):**
```
[cabecera común con X = B]
Tu trabajo: G4 y después G5.
El agente A está implementando geo/llm.py a la vez que tú. No lo esperes: en tus tests usa monkeypatch sobre geo.judge_llm.complete_json y lanza las excepciones LLMConfigError, LLMProviderError y LLMCallLimitError que ya existen desde C0.
En G5 implementa Run.estimate() y estimate_pipeline() con la forma exacta de CONTRATOS.md: la UI (agentes D y E) ya los está pintando.
Requisito duro: en modo mock, judge_ensemble y run_all deben producir exactamente lo mismo que antes (test con assert_frame_equal y comparación de metrics.json de runs/demo/).
```

**Agente C · Ejecución y herramientas (ola 1, sigue en ola 2):**
```
[cabecera común con X = C]
Ola 1: completa scripts/fake_openrouter.py (modos FAKE_OR_FAIL y fixtures por prompt_version según G2) y genera tests/fixtures/fake_openrouter/{intake_v1,strategy_v1,writer_client_v1,writer_prospect_v1,compliance_v1}.json a partir de las salidas mock de runs/demo/ para que validen contra los esquemas. Después implementa geo/jobs.py (G6) completo, respetando read_progress() y list_runs() que dejó el líder.
Avisa en tu informe en cuanto jobs.start() funcione en mock: el agente E lo necesita.
Ola 2 (cuando el líder te lo diga): G11 (scripts/real_smoke.py, probado solo contra el servidor falso) y G10 (lanzador y Makefile).
Usa el puerto 8763 para tu servidor falso.
```

**Agente D · UI marco y Ajustes (ola 1):**
```
[cabecera común con X = D]
Tu trabajo: G7. Eres el único dueño de app/ui_shared.py, app/Home.py, .streamlit/config.toml y app/pages/8_Ajustes.py.
No toques ui_jobs.py ni las páginas de análisis: son del agente E. La llamada a guard_active_run() en shell() ya la dejó el líder; no la quites.
Hasta que el agente A integre, list_models() y test_connection() pueden ser stubs: haz que la página funcione con el servidor falso (puerto 8761, OPENROUTER_BASE_URL=http://127.0.0.1:8761) y con errores controlados.
Revisa PRODUCT.md y reutiliza page_header, panel, section, chip, kpi_strip y render_empty. Estilos nuevos solo como clases .geo-* dentro de _CSS.
Streamlit en el puerto 8511. Haz capturas con Playwright en claro y oscuro de Ajustes y de la barra lateral en sus 3 estados de conexión, y revísalas.
```

**Agente E · UI análisis, progreso e historial (ola 1, sigue en ola 2):**
```
[cabecera común con X = E]
Tu trabajo: G8. Eres dueño de app/ui_jobs.py, app/pages/00_Nuevo_analisis.py, app/pages/9_Historial.py, 0_Inicio.py, 5_Plan.py, 6_Propuesta.py y la parte superior de 7_Calidad_y_trazas.py (no toques la sección «Conectores en vivo»).
No toques app/ui_shared.py: es del agente D. Si necesitas un estilo nuevo, pídelo en coord/peticiones/E.md y mientras tanto usa los componentes que ya existen.
Ola 1: construye render_progress() y la página de Nuevo análisis contra las fixtures de tests/fixtures/progress/*.json (cópialas a runs/<id>/progress.json para simular cada estado). Para lanzar, llama a jobs.start(); si todavía lanza NotImplementedError, muestra el error de forma controlada.
Ola 2 (cuando el líder integre A, B y C): rebase sobre main y prueba el flujo real del prompt de G8 con el servidor falso en el puerto 8762 y Streamlit en el 8512.
Elimina todas las llamadas a run_all() de las páginas: `grep -n run_all app/` solo debe devolver ensure_demo_run_ready.
```

**Agente F · Motores en vivo (ola 2, opcional):**
```
[cabecera común con X = F]
Tu trabajo: G9. Dueño de geo/engines/* y de la sección «Conectores en vivo» al final de app/pages/7_Calidad_y_trazas.py (el resto del archivo es del agente E).
Parte de main después de I1. Servidor falso en el 8764 (añádele, si te hace falta, citas url_citation pidiéndolo en coord/peticiones/F.md al agente C) y Streamlit en el 8514.
```

**Agente Q · Verificador independiente (ola 3, sesión limpia):**
```
Eres el agente Q, verificador. No has participado en el desarrollo. Lee PLAN_OPENROUTER.md (secciones M, 1, G7, G8 y el checklist 8) y trabaja sobre main tras la integración I2.
No arregles nada del código de producción. Tu salida es un informe en coord/informe_Q.md y tests en tests/e2e/.
Comprueba con Playwright (Streamlit en 8515, servidor falso en 8765):
1. rm -rf runs cache && pytest -q en verde y sin red (bloquea openrouter.ai en el test con monkeypatch de requests si hace falta).
2. Recorrido completo de G8 con el servidor falso: Ajustes → Nuevo análisis → progreso → navegación durante el progreso → resultados → Historial.
3. Los mismos pasos con FAKE_OR_FAIL=402 y 429_once: la UI muestra pasos simulados por error y el run termina.
4. Ninguna página dispara llamadas sin confirmación: cuenta peticiones al servidor falso al abrir Plan, Propuesta y Calidad de un run ya terminado (deben ser 0).
5. La clave falsa "sk-or-test-123" no aparece en runs/, cache/, trace.jsonl, progress.json ni en el HTML de la app.
6. Capturas en claro y oscuro de cada página; revísalas buscando textos cortados, solapes, inglés en la UI o emojis.
Cada fallo en el informe con: pasos para reproducir, archivo responsable según la matriz M3 y agente dueño.
```

**Agente H · Documentación (ola 3):**
```
[cabecera común con X = H]
Tu trabajo: G12. Parte de main tras I2. Las cifras de coste y acierto solo pueden salir de runs/demo_real/ y de la salida de scripts/real_smoke.py; si aún no existen, escribe PENDIENTE y lista al final qué cifras faltan para que las rellenes cuando el líder te pase los datos.
```

### M9. Protocolo de integración (agente L)

En cada punto I1, I2 e I3:

1. Para cada rama en el orden indicado en M7:
   ```bash
   git fetch . ag/A-nucleo
   git diff --name-only contratos-v1 ag/A-nucleo      # comparar con la fila de A en M3
   git merge --no-ff ag/A-nucleo -m "I1: integra A"
   pytest -q
   ```
2. Si el diff contiene archivos ajenos: no se integra. Se devuelve al agente con la lista.
3. Si `pytest` falla después del merge: `git merge --abort` si aún no se ha confirmado, o `git revert -m 1 HEAD`, y el error vuelve al agente dueño.
4. Leer `coord/peticiones/*.md`. Si una petición de contrato es razonable, el líder cambia `CONTRATOS.md`, crea `contratos-v2` y avisa a los agentes afectados para que hagan rebase.
5. Tras integrar, avisar a los agentes de la siguiente ola: «main en `<hash>`, haz rebase».
6. Mensaje de estado en el canal del equipo: qué entró, qué se devolvió y por qué.

### M10. Dependencias entre agentes de un vistazo

```
            ┌──────────── C0 (L) ────────────┐
            │  contratos · stubs · fixtures   │
            └──┬──────┬──────┬──────┬──────┬──┘
               ▼      ▼      ▼      ▼      ▼
              A      B      C      D      E          ← OLA 1 (en paralelo)
               └──────┴──┬───┘      │      │
                         ▼          │      │
                   I1 (backend)     │      │
                         │          │      │
             ┌───────────┼──────────┴──┐   │
             ▼           ▼             ▼   ▼
        C (G10,G11)   F (G9)      D y E rebase      ← OLA 2
             │           │             │
             └───────────┴──────┬──────┘
                                ▼
                          I2 (UI)
                                │
                     ┌──────────┼──────────┐
                     ▼          ▼          ▼
                     Q          H     L real_smoke   ← OLA 3
                     └──────────┼──────────┘
                                ▼
                       I3 (arreglos) → congelación
```

## 1. Diagnóstico del código actual (verificado sobre el zip)

Estas observaciones salen de leer el código. Claude Code debe comprobarlas al empezar cada fase, porque son la causa de casi todos los cambios.

### 1.1 Repositorio
| Hecho | Consecuencia |
|---|---|
| La carpeta raíz se llama `carpeta sin título` y no es un repo git. | Renombrar a `geo-copilot/` y hacer `git init` antes de tocar nada. Los espacios en la ruta rompen algunos comandos de shell. |
| El kit está duplicado: `kit/Kit Participantes Hackaton/` (el que usa `config.py`) y `Kit Participantes Hackaton/` en la raíz (ignorado en `.gitignore`). | No borrar nada del kit (regla de `CLAUDE.md`). Solo documentar que el bueno es `kit/`. |
| `runs/` y `cache/` están en `.gitignore` y no vienen en el zip. | **8 tests fallan** en un clon limpio (`test_simulate.py` ×3, `test_docs_verified.py` y otros) con `FileNotFoundError: runs/demo/metrics.json` o `runs/demo/evaluaciones.parquet`. Hace falta un fixture que genere `runs/demo/` en modo mock. |
| Python 3.13 funciona; `requirements.txt` no fija versiones máximas. | Sin cambios. Solo se añade `requests` de forma explícita (ya viene con Streamlit, pero mejor declararlo). |

### 1.2 Capa LLM (`geo/llm.py`, `geo/config.py`)
| Hecho | Consecuencia |
|---|---|
| Proveedores: `mock`, `anthropic`, `openai`. Cada uno usa su SDK y su clave. | Se añade `openrouter`. Los otros dos se mantienen para no romper nada, pero la UI solo ofrece «Simulado» y «OpenRouter». |
| `config.py` lee `LLM_PROVIDER`, `LLM_MODEL`, claves y topes **al importar el módulo**. | Si la UI cambia los ajustes, los módulos que importaron esas constantes no se enteran. Todo lo editable debe leerse en tiempo de llamada (`settings.get(...)`). |
| `complete_json()` resuelve el modelo con `model or LLM_MODEL`. Solo `writer.py` mira `LLM_MODEL_WRITER` (líneas ~440 y ~720). | `strategy.py` usa el modelo pequeño aunque debería usar el grande. Se centraliza la resolución por rol. |
| `_TRACKER` (llamadas, tokens) es global y no tiene lock. | Con el juez en paralelo los contadores se corrompen. Hace falta `threading.Lock`. |
| `estimate_cost()` usa un precio fijo (0,25 / 1,25 por millón). | Con OpenRouter el coste real viene en `usage.cost` y el precio de cada modelo en `/models`. |
| `_call_provider_raw()` tiene `@retry` de tenacity con 4 intentos sobre `LLMProviderError`, también para errores no recuperables (clave inválida). | Con una clave mala se esperan 4 reintentos por cada una de las ~624 llamadas del juez. Hay que distinguir errores recuperables (429, 5xx, red) de no recuperables (401, 402, 403, 404). |
| `MAX_BUDGET_EUR` existe en `config.py` pero solo lo usa el mini-estudio. | El pipeline completo no tiene tope de gasto. Se añade. |

### 1.3 Juez LLM (`geo/judge_llm.py`, `geo/judge.py`)
| Hecho | Consecuencia |
|---|---|
| Bucle secuencial: una llamada por ejecución con marcas detectadas. `RESUMEN_IMPLEMENTACION.md` cuenta 624 llamadas, ~1,22 M tokens de entrada y ~62 k de salida. | En secuencial, con 2-5 s por llamada, son 20-50 minutos. Con 8 hilos baja a 3-6 minutos. |
| Si una sola llamada lanza excepción, falla todo `judge_ensemble` y el orquestador degrada **el paso entero** a reglas. | Un 429 puntual tira a la basura 600 juicios ya pagados. Los fallos deben ser por ejecución, no por paso. |
| `estimate_judge_llm_workload()` estima 850 tokens de entrada y 180 de salida por llamada con precio fijo. | Se recalcula con el precio real del modelo elegido. |

### 1.4 Orquestador (`geo/orchestrator.py`)
| Hecho | Consecuencia |
|---|---|
| `_run_tracked_step()` hace fallback a mock/reglas si falla el LLM y solo lo apunta en `trace.jsonl` (`degradado=True`). | En la demo puede parecer que funciona con IA real cuando en realidad ha caído a mock. La degradación tiene que verse en la UI. |
| La traza guarda `model = os.getenv("LLM_MODEL")` para todos los pasos. | Mal para estrategia y redacción, que usan otro modelo. |
| `Run(run_id="X")` toma `provider` del entorno, no de `state.json`. | **Bug:** al reabrir un análisis hecho con OpenRouter desde una sesión configurada en mock, las páginas 5, 6 y 7 relanzan pasos con el proveedor equivocado. |
| `run_all()` no avisa de su avance. | La UI no puede pintar progreso. Se añaden callbacks. |

### 1.5 Interfaz (`app/`)
| Hecho | Consecuencia |
|---|---|
| `0_Inicio.py` tiene un expander «Configurar una ejecución propia» con selector `mock / anthropic / openai`, y ejecuta `run_all()` dentro de un `st.spinner` en el propio script. | Con un LLM real la pestaña se bloquea minutos. Si el usuario cambia de página, Streamlit corta el script a mitad y el análisis queda a medias. Hay que ejecutar en un hilo de fondo. |
| `5_Plan.py:42`, `6_Propuesta.py:19` y `7_Calidad_y_trazas.py:20` llaman a `run.run_all(auto_approve=True, force=False)` si falta algún artefacto. `6_Propuesta.py:79` llama con `force=True`. | Con OpenRouter, abrir una página puede disparar llamadas de pago sin aviso, o lanzar un segundo pipeline sobre un run que ya se está ejecutando en segundo plano. Se bloquea mientras hay un trabajo en curso. |
| El brief subido se guarda en `/tmp/<nombre>`. | Se pierde al reiniciar. Se guarda dentro de `runs/<run_id>/brief_original.<ext>`. |
| No hay página de ajustes, ni historial de análisis, ni indicador de conexión. | Son el núcleo de «que parezca una aplicación». |
| `shell()` pinta el aviso de datos sintéticos y la tarjeta del run activo con `run.provider`. | Se amplía con el estado de conexión y los pasos degradados. |
| Sistema de diseño propio en `ui_shared.py` (tokens claro/oscuro, Geist, acento naranja de la marca). | Reutilizarlo. Nada de estilos nuevos sueltos: se añaden clases `.geo-*` al bloque `_CSS`. |

### 1.6 Motores en vivo (`geo/engines/`)
| Hecho | Consecuencia |
|---|---|
| Cuatro conectores con SDK y clave propios (OpenAI Responses, Gemini grounding, Anthropic web_search, Perplexity Sonar), modelos fijos en código. | OpenRouter permite los cuatro con una clave y el plugin `web`. G9 añade un conector único. |
| El texto de simulación de los conectores nombra clínicas reales. | Al ser datos simulados, conviene que el texto lo diga claramente (ya lo hace con «[Simulación…]»). Sin cambios. |

---

## 2. Decisiones de arquitectura

| Decisión | Elegido | Descartado y por qué |
|---|---|---|
| Proveedor real | OpenRouter (API compatible con OpenAI) | Mantener tres claves (Anthropic, OpenAI, Google): más configuración y más puntos de fallo en la demo |
| Cliente HTTP | `requests` directo contra `/chat/completions` | SDK `openai` con `base_url`: oculta campos propios de OpenRouter (`usage.cost`, `annotations`, `citations`) tras `model_extra` |
| Salida estructurada | `response_format: {"type": "json_object"}` + validación Pydantic existente; si el modelo responde 400 por `response_format`, se reintenta sin él | `json_schema` estricto: no todos los modelos lo soportan y el esquema de Pydantic ya se manda en el prompt de sistema |
| Coste | `usage.cost` real de cada respuesta (créditos de OpenRouter ≈ USD) convertido a € con `USD_EUR`; estimación previa con precios de `/models` | Precio fijo en código |
| Modelos | Dos roles: `LLM_MODEL` (juez, intake, revisor) y `LLM_MODEL_WRITER` (estrategia, redacción). Seleccionables en la UI desde el catálogo | Un modelo para todo (o caro o flojo redactando) |
| Paralelismo | `ThreadPoolExecutor` con `LLM_CONCURRENCY` (por defecto 8) solo en el juez | asyncio: obliga a reescribir `complete_json` y sus llamadas |
| Ejecución desde la UI | Hilo de fondo por análisis + `runs/<id>/progress.json`; la UI lo lee cada segundo con `st.fragment(run_every=1)` | Ejecutar en el script de Streamlit: bloquea y se corta al navegar. Celery/RQ: excesivo |
| Ajustes | `geo/settings.py` lee y escribe `.env` (permisos 600) y actualiza `os.environ` | Guardar la clave en `st.session_state`: se pierde al recargar. Guardarla en `runs/`: se filtraría en el zip de entrega |
| Degradación | Se mantiene, pero se registra en `state.json["degradados"]` y se muestra en la UI con un aviso visible | Fallar sin fallback: la demo se cae si hay un 429 |
| Tope de gasto | `MAX_BUDGET_EUR` por ejecución, comprobado antes de cada llamada | Solo tope de llamadas |

---

## 3. Referencia de la API de OpenRouter (comprobada en docs, octubre de 2026)

Claude Code debe volver a consultar https://openrouter.ai/docs si algo no cuadra. Lo esencial:

- **Base:** `https://openrouter.ai/api/v1`. Configurable con `OPENROUTER_BASE_URL` (lo usa el servidor falso de los tests).
- **Cabeceras:** `Authorization: Bearer <OPENROUTER_API_KEY>` (obligatoria). Opcionales: `HTTP-Referer` (URL de la app) y `X-Title` o `X-OpenRouter-Title` (nombre de la app, «GEO Copilot»).
- **Chat:** `POST /chat/completions` con `model`, `messages`, `temperature`, `max_tokens`, `response_format`.
- **Uso y coste:** las respuestas no streaming traen `usage` con `prompt_tokens`, `completion_tokens`, `total_tokens` y `cost` (en créditos). Se puede enviar `"usage": {"include": true}` por compatibilidad; no molesta.
- **Errores:** cuerpo `{"error": {"code": <int>, "message": "...", "metadata": {...}}}`. Tratar como **no recuperables** 400 (salvo el caso `response_format`), 401 (clave), 402 (sin saldo), 403 (moderación o permiso), 404 (modelo). **Recuperables** con backoff: 408, 429, 500, 502, 503, 504 y errores de red. Ojo: algunos errores llegan con HTTP 200 y `error` en el cuerpo; comprobarlo también.
- **Catálogo:** `GET /models` (no necesita clave). Cada modelo trae `id`, `name`, `context_length` y `pricing.prompt` / `pricing.completion` en USD **por token** como cadenas. Multiplicar por 1.000.000 para mostrar «$/M».
- **Estado de la clave:** `GET /key` (con clave) devuelve `data` con `label`, `usage` (gasto acumulado), `limit` y si es de nivel gratuito. Útil para «Probar conexión».
- **Búsqueda web (solo G9):** `"plugins": [{"id": "web", "max_results": 5}]` o el sufijo `:online` en el modelo. Para OpenAI, Anthropic, Perplexity y Google usa búsqueda nativa por defecto. Las citas llegan en `choices[0].message.annotations[]` con `type: "url_citation"` y `url_citation: {url, title, content, start_index, end_index}`. Coste extra por búsqueda (Exa ~0,007 $ por petición si el modelo no tiene búsqueda nativa).
- **Modelos:** no fijar IDs a ciegas. Los valores por defecto se validan contra `/models` al abrir Ajustes y la UI avisa si un ID no existe. Ejemplos razonables a comprobar: un modelo rápido y barato de la familia Gemini Flash o Claude Haiku para el juez, y uno de gama media (Claude Sonnet, GPT de gama media) para redacción.

---

## 4. Variables de entorno nuevas

`.env.example` queda así (sustituye al actual, conservando las claves antiguas al final):

```ini
# Proveedor: mock (sin red, sin coste) | openrouter (real)
LLM_PROVIDER=mock

# OpenRouter (una sola clave para todos los modelos). No subir nunca al repositorio.
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Modelos por rol (IDs de https://openrouter.ai/models)
LLM_MODEL=google/gemini-2.5-flash          # juez, intake y revisor normativo
LLM_MODEL_WRITER=anthropic/claude-sonnet-4.5   # estrategia y redacción

# Rendimiento y límites por ejecución
LLM_CONCURRENCY=8
MAX_LLM_CALLS=1500
MAX_BUDGET_EUR=5.0
USD_EUR=0.92

# Motores en vivo (G9, opcional)
ENGINE_MODEL_CHATGPT=openai/gpt-4o-mini
ENGINE_MODEL_GEMINI=google/gemini-2.5-flash
ENGINE_MODEL_CLAUDE=anthropic/claude-haiku-4.5
ENGINE_MODEL_PERPLEXITY=perplexity/sonar

# Proveedores directos heredados (no se usan desde la UI)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

Los IDs de modelo son ejemplos que hay que validar contra `/models` en G7.

---

## 5. Fases

### G0 · Base verde y repositorio
**Agente:** L · **Ola:** 0 (dentro de C0)
**Objetivo:** partir de un repo con git y con los 41 tests en verde en un clon limpio.

**Especificación:**
- Renombrar la carpeta a `geo-copilot` (fuera de Claude Code, a mano: `mv "carpeta sin título" geo-copilot`).
- `git init`, commit inicial con el estado tal cual.
- `tests/conftest.py`: fixture `scope="session", autouse=True` que, si no existe `runs/demo/propuesta.json`, ejecuta el pipeline en mock:
  ```python
  @pytest.fixture(scope="session", autouse=True)
  def demo_run_ready() -> None:
      os.environ["LLM_PROVIDER"] = "mock"
      if not (RUNS_DIR / "demo" / "propuesta.json").exists():
          Run(run_id="demo", modo="cliente", brief_path=BRIEF_MD, provider="mock").run_all(auto_approve=True)
  ```
  Además, forzar `LLM_PROVIDER=mock` y vaciar `OPENROUTER_API_KEY` en el entorno de todos los tests, para que un `.env` real del desarrollador no dispare llamadas de pago.
- Añadir `requests>=2.31` a `requirements.txt`.
- Añadir a `CLAUDE.md` las tres líneas de la sección 0.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 0, 1 y G0.
1. Comprueba que el repo tiene git; si no, inicialízalo y haz un commit con el estado actual.
2. Ejecuta pytest -q y anota qué falla. Confirma que los fallos se deben a que no existe runs/demo/.
3. En tests/conftest.py añade un fixture de sesión autouse que genere runs/demo/ con el pipeline en mock si no existe, y que fuerce LLM_PROVIDER=mock y OPENROUTER_API_KEY vacía durante los tests (monkeypatch o os.environ con restauración).
4. Añade requests>=2.31 a requirements.txt.
5. Añade al final de CLAUDE.md las líneas de la sección 0 de PLAN_OPENROUTER.md.
No toques nada de geo/ ni de app/ en esta fase.
```

**Aceptación:** `rm -rf runs cache && pytest -q` → todo en verde. Commit `G0: base verde`.

---

### G1 · Ajustes persistentes (`geo/settings.py`)
**Agente:** L (implementación en C0) y A (tests pendientes) · **Ola:** 0-1
**Objetivo:** un único sitio para leer y escribir la configuración editable desde la UI, leída siempre en tiempo de llamada.

**Archivos:** `geo/settings.py` (nuevo), `.env.example`, `geo/config.py` (solo comentarios y el valor por defecto de `LLM_PROVIDER`), `tests/test_settings.py` (nuevo).

**Especificación:**
```python
ENV_PATH: Path = ROOT_DIR / ".env"
DEFAULTS: dict[str, str]          # todas las claves de la sección 4 con su valor por defecto
SECRET_KEYS: set[str]             # OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY

def get(key: str) -> str           # os.environ > DEFAULTS; quita comentarios en línea ("8  # x" -> "8") salvo en secretos
def get_int(key: str) -> int
def get_float(key: str) -> float
def current() -> dict[str, str]
def save(values: dict[str, str]) -> Path
    # Reescribe .env conservando líneas y comentarios ajenos, sustituye las claves existentes,
    # añade las nuevas al final, chmod 600 y actualiza os.environ.
def mask(secret: str) -> str        # "sk-or-v1-abc…wxyz"
def has_openrouter_key() -> bool
```
- `config.py` hace `load_dotenv()` al importar: se mantiene. Las constantes `LLM_PROVIDER`, `LLM_MODEL`, etc. siguen existiendo por compatibilidad, pero **ningún código nuevo las usa**; se usa `settings.get()`.
- Nunca imprimir la clave. `current()` devuelve la clave en claro solo para el formulario; la UI la muestra enmascarada.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 1.2, 4 y G1.
Implementa geo/settings.py con la API exacta de G1. Sustituye .env.example por el de la sección 4.
Tests en tests/test_settings.py usando tmp_path y monkeypatch sobre settings.ENV_PATH:
(a) save() crea el .env con permisos 600 y actualiza os.environ;
(b) save() conserva comentarios y claves que no conoce;
(c) save() sustituye una clave existente sin duplicarla;
(d) get() quita comentarios en línea en valores normales pero no en secretos;
(e) mask() nunca devuelve más de 11 caracteres visibles de la clave.
pytest -q en verde.
```

**Aceptación:** tests en verde; `python -c "from geo import settings; print(settings.current())"` muestra los valores por defecto.

---

### G2 · Cliente OpenRouter (`geo/openrouter.py`)
**Agente:** A (cliente) y C (servidor falso completo; versión mínima en C0) · **Ola:** 1
**Objetivo:** módulo pequeño, sin dependencias nuevas, que hable con OpenRouter y devuelva texto, tokens, coste real y citas.

**Archivos:** `geo/openrouter.py` (nuevo), `scripts/fake_openrouter.py` (nuevo), `tests/test_openrouter.py` (nuevo).

**Especificación del cliente:**
```python
class OpenRouterError(RuntimeError):
    status: int | None
    retryable: bool

@dataclass
class ChatResult:
    text: str
    model: str            # el que devuelve OpenRouter (puede diferir del pedido si hay alias)
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    citations: list[str]  # URLs de annotations[].url_citation.url y de citations[] (Perplexity)
    raw: dict

def chat(messages, *, model, temperature=0.0, json_mode=False, web_search=False,
         max_tokens=4096, api_key=None, retries=4) -> ChatResult
def list_models(force=False) -> list[dict]      # id, name, price_in_per_m, price_out_per_m, context; caché 1 h con lock
def model_price(model_id) -> tuple[float, float] | None
def key_info(api_key=None) -> dict              # GET /key
def test_connection(model, api_key=None) -> dict  # key_info + llamada mínima {"ok": true}; latencia y coste
```
Reglas de `chat()`:
1. Payload: `model`, `messages`, `temperature`, `max_tokens`, `usage: {"include": true}`; `response_format: {"type": "json_object"}` si `json_mode`; `plugins: [{"id": "web", "max_results": 5}]` si `web_search` y el modelo no es `perplexity/*`.
2. Si responde 400 y había `response_format`, quitarlo y repetir **una vez** sin contar como reintento.
3. Errores no recuperables (sección 3) → `OpenRouterError(retryable=False)` inmediato, con mensaje en español que incluya una pista: 401 «Clave inválida o revocada», 402 «Sin saldo en OpenRouter», 404 «Modelo no encontrado».
4. Recuperables → backoff `min(2**intento, 10)` s hasta `retries`.
5. HTTP 200 con `error` en el cuerpo → tratar como error recuperable.
6. Sin `choices` → error recuperable.
7. `timeout=120` s por petición.
8. Cabeceras `HTTP-Referer` y `X-Title: GEO Copilot`.

**Servidor falso (`scripts/fake_openrouter.py`):** `http.server` en un puerto configurable que implementa `/models`, `/key` y `/chat/completions`. Para el chat:
- Si el mensaje de usuario contiene `"marcas_detectadas"`, extrae el JSON de `<datos>…</datos>` y devuelve un `JuicioEjecucion` válido (todas las marcas con `Comparación neutra`, fuerza 1, `cita_textual` = primeros 80 caracteres del fragmento).
- Para el resto de prompts, devuelve el JSON que se le pase por un fichero de fixtures (`tests/fixtures/fake_openrouter/<prompt_version>.json`) o `{}` si no hay (lo que fuerza la degradación y sirve para probarla).
- `usage` con tokens fijos y `cost: 0.0001`.
- Modos de fallo por variable de entorno: `FAKE_OR_FAIL=401|402|429_once|500_always|bad_json`.
- Arranque: `python scripts/fake_openrouter.py --port 8765`. Se usa con `OPENROUTER_BASE_URL=http://127.0.0.1:8765`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 2, 3 y G2.
Implementa geo/openrouter.py con requests (sin SDK) y la API exacta de G2, incluidas las 8 reglas de chat().
Implementa scripts/fake_openrouter.py según G2 (http.server, sin dependencias).
Tests en tests/test_openrouter.py con monkeypatch de requests.post/requests.get (sin red):
(a) chat() devuelve texto, tokens y cost_usd;
(b) extrae citas de annotations url_citation y de citations[];
(c) 400 con json_mode reintenta sin response_format y funciona;
(d) 401 lanza OpenRouterError(retryable=False) sin reintentar (cuenta de llamadas = 1);
(e) 429 una vez y luego 200 → éxito (parchea time.sleep);
(f) list_models convierte el precio por token a $/M;
(g) la clave nunca aparece en el mensaje de ninguna excepción.
pytest -q en verde.
```

**Aceptación:** tests en verde. Con el servidor falso arrancado: `OPENROUTER_BASE_URL=http://127.0.0.1:8765 OPENROUTER_API_KEY=x python -c "from geo.openrouter import test_connection; print(test_connection('fake/model'))"` imprime latencia y coste.

---

### G3 · Integración en `geo/llm.py`
**Agente:** A · **Ola:** 1 · **Depende de:** G2
**Objetivo:** `complete_json()` funciona con `provider="openrouter"`, elige el modelo por rol, cuenta coste real, es seguro con hilos y respeta el tope de gasto.

**Archivos:** `geo/llm.py`, `geo/writer.py` (solo resolución de modelo), `tests/test_llm_openrouter.py` (nuevo).

**Especificación:**
1. Nuevas excepciones: `LLMConfigError(RuntimeError)` para errores no recuperables (sin clave, 401, 402, 403, 404). `LLMProviderError` queda para los recuperables. El `@retry` de tenacity **solo** reintenta `LLMProviderError`, y para `openrouter` se llama a `chat(..., retries=2)` para no multiplicar esperas (2 de tenacity × 2 internos como máximo).
2. `resolve_model(provider, prompt_version, model=None) -> str`:
   - `model` explícito gana.
   - `prompt_version` que empieza por `strategy` o `writer` → `LLM_MODEL_WRITER` (si está vacío, `LLM_MODEL`).
   - Resto (`intake`, `judge`, `compliance`) → `LLM_MODEL`.
   - Para `mock` devuelve `"mock"`.
   - `writer.py` deja de leer `LLM_MODEL_WRITER` por su cuenta y pasa `model=None`.
3. `_call_provider_raw()` devuelve `(texto, tok_in, tok_out, coste_usd | None)`. Rama `openrouter` con `chat(json_mode=True)`. Las ramas `anthropic` y `openai` devuelven `None` como coste.
4. Tracker:
   - `lock = threading.Lock()`; todos los incrementos dentro del lock.
   - Nuevo campo `cost_eur` acumulado y `cost_is_real` (True si al menos un coste vino de `usage.cost`).
   - Función `_account(provider, model, tok_in, tok_out, cost_usd)`: si hay `cost_usd`, suma `cost_usd * USD_EUR`; si no, usa `model_price()` del catálogo; si tampoco, `estimate_cost()` actual.
   - `get_llm_stats()` añade `cost_is_real` y devuelve `estimated_cost_eur = cost_eur` cuando haya coste acumulado.
5. Tope de gasto: antes de cada llamada real, si `cost_eur >= MAX_BUDGET_EUR` → `LLMCallLimitError("Se alcanzó el tope de gasto de la ejecución (X €).")`.
6. Caché: la clave ya incluye proveedor y modelo, así que cambiar de modelo invalida la caché sin más. Guardar también `cost_usd` en el JSON de caché (informativo).
7. Un fallo de validación Pydantic sigue con su reintento único con el error en el mensaje (comportamiento actual).
8. `estimate_cost()` se mantiene con su firma; se añade `estimate_cost_for_model(model, tok_in, tok_out) -> float` que usa el catálogo y cae al precio por defecto.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 1.2, 2 y G3.
Modifica geo/llm.py según los 8 puntos de G3 sin cambiar la firma pública de complete_json() (solo añade). Ajusta geo/writer.py para que no resuelva el modelo por su cuenta.
Tests en tests/test_llm_openrouter.py con monkeypatch de geo.openrouter.chat (sin red):
(a) complete_json(provider="openrouter") valida contra un esquema y suma coste real en get_llm_stats();
(b) resolve_model elige LLM_MODEL_WRITER para writer_client_v1 y strategy_v1, y LLM_MODEL para judge_v1;
(c) una segunda llamada idéntica sale de caché (calls no aumenta, cache_hits sí);
(d) 401 → LLMConfigError sin reintentos de tenacity;
(e) superado MAX_BUDGET_EUR → LLMCallLimitError;
(f) 50 llamadas desde 8 hilos dejan calls == 50 exacto.
Todos los tests anteriores siguen en verde (el modo mock no cambia).
```

**Aceptación:** tests en verde; `LLM_PROVIDER=mock python scripts/run_pipeline.py --auto-approve` sigue funcionando igual.

---

### G4 · Juez LLM en paralelo con progreso
**Agente:** B · **Ola:** 1 · **Depende de:** contratos de C0 (no espera a A)
**Objetivo:** las ~624 llamadas del juez en minutos, con progreso visible y sin perder trabajo por fallos puntuales.

**Archivos:** `geo/judge_llm.py`, `geo/judge.py`, `tests/test_judge_parallel.py` (nuevo).

**Especificación:**
- Extraer el cuerpo del bucle actual a `_judge_one(ej_id, present_rows) -> JuicioEjecucion` (prepara `<datos>`, el `mock_builder` y llama a `complete_json`). Ojo con los cierres (closures) dentro de bucles: pasar `present_rows` y `fuentes_ej` como argumentos, no capturarlos.
- **Fase 1 (red):** `ThreadPoolExecutor(max_workers=LLM_CONCURRENCY)`; en mock, `max_workers=1`. Recorrer con `as_completed`.
  - Éxito → `resultados[ej_id]`.
  - `LLMConfigError` o `LLMCallLimitError` → cancelar el resto y relanzar (el orquestador degradará el paso).
  - Cualquier otra excepción → `fallos[ej_id] = mensaje`; esa ejecución se evaluará por reglas en la fase 2.
  - Tras cada futura completada, `on_progress(hechos, total)` si existe.
  - Si fallan **todas**, lanzar `LLMProviderError` con el primer mensaje.
- **Fase 2 (CPU):** el bucle actual que construye las filas `Evaluacion`, leyendo de `resultados`. Si una ejecución no está en `resultados`, las marcas presentes se rellenan con el juez de reglas (comportamiento ya previsto para «marcas que faltan»), con `juez="reglas"` y `confianza_juez=0.6`.
- Exponer `JUDGE_LAST_RUN: dict` con `llamadas`, `fallos` y hasta 5 ejemplos de fallo, para la traza.
- `judge_llm()` y `judge_ensemble()` aceptan `on_progress: Callable[[int, int], None] | None = None`.
- `estimate_judge_llm_workload()` acepta `model: str | None` y usa `estimate_cost_for_model`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 1.3 y G4.
Refactoriza geo/judge_llm.py en dos fases (red en paralelo, construcción de filas después) según G4, sin cambiar el resultado en modo mock: el DataFrame de judge_ensemble en mock debe ser idéntico antes y después (compáralo en un test con assert_frame_equal ordenando por ejecucion_id y marca).
Añade on_progress a judge_llm y judge_ensemble, JUDGE_LAST_RUN y el parámetro model en estimate_judge_llm_workload.
Tests en tests/test_judge_parallel.py con monkeypatch de complete_json:
(a) mock idéntico al de antes;
(b) on_progress se llama total veces y el último valor es (total, total);
(c) si 3 ejecuciones lanzan LLMProviderError, el resto conserva el juicio LLM y esas 3 salen por reglas;
(d) LLMConfigError en la primera llamada aborta todo;
(e) con LLM_CONCURRENCY=8 y una latencia simulada de 0,05 s, 80 llamadas tardan menos de 1,5 s.
python scripts/validate_judge.py --judge ensemble sigue funcionando en mock.
```

**Aceptación:** tests en verde y validación del juez sin cambios en mock (100 % en tipo de mención, fuerza y sentimiento).

---

### G5 · Orquestador: eventos, degradación visible y reapertura correcta
**Agente:** B · **Ola:** 1, después de G4
**Objetivo:** que la UI sepa en todo momento qué paso corre, cuánto lleva, cuánto cuesta y si algo cayó a mock.

**Archivos:** `geo/orchestrator.py`, `tests/test_pipeline_mock.py` (ampliar), `tests/test_orchestrator_events.py` (nuevo).

**Especificación:**
1. **Bug de reapertura:** en `Run.__init__`, si se pasa `run_id` y existe `state.json`, `modo`, `provider`, `brief_path` y `marca_prospecto` se toman del estado (los argumentos explícitos solo ganan si se pasan).
2. `state.json` guarda `"models": {"juez_y_revisor": ..., "estrategia_y_redaccion": ...}` al crearse (vacío en mock).
3. Callbacks opcionales en la instancia: `run.on_event(paso, estado, info)` con `estado ∈ {"start", "degraded", "done", "error"}` y `run.on_progress(paso, hechos, total)`. Envolver cada llamada en `try/except` para que un fallo de la UI nunca rompa el pipeline.
4. `_run_tracked_step()`:
   - Emite `start` al empezar, `degraded` si entra en el fallback (con el error), `done` al acabar (con `degradado`, `llm_calls`, `cost_eur`, `duration_s`) y `error` si falla sin fallback.
   - La traza usa el modelo real del paso (`resolve_model(self.provider, prompt_version)`; `"código"` para los pasos `deterministic_*`), y añade `provider` y `cost_is_real`.
   - Si el paso se degradó, `state["degradados"][paso] = mensaje`.
   - Parámetro `extra_trace: Callable[[], dict] | None` para añadir datos; el paso `judge` lo usa con `{"juez_llm": dict(JUDGE_LAST_RUN)}`.
5. `run_all()` pasa `on_progress` a `judge_ensemble` (`lambda d, t: self.on_progress("judge", d, t)`).
6. **Guardia de coste:** método `estimate(self) -> dict` que devuelve llamadas y € previstos por paso, usando `estimate_judge_llm_workload(model=...)` para el juez y una constante por paso para los demás (intake 1 llamada ~3 k/1 k tokens; estrategia 1 ~9 k/4,5 k; redactor 1-3 ~4 k/1,5 k; revisor 2 ~8 k/0,1 k). Lo usa la UI antes de lanzar.
7. `degradados` también se resetean al relanzar con `force=True`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 1.4 y G5.
Implementa en geo/orchestrator.py los 7 puntos de G5. No cambies el orden de pasos ni los checkpoints.
Tests:
(a) Run(run_id=X) reabierto con LLM_PROVIDER=openrouter en el entorno conserva provider="mock" si se creó en mock;
(b) con un on_event que apunta eventos, un run_all en mock produce start/done para los 10 pasos en orden;
(c) con complete_json parcheado para lanzar LLMConfigError en el paso plan, el evento es degraded, state["degradados"] contiene "plan" y la traza dice degradado=True;
(d) la traza del paso write lleva el modelo de LLM_MODEL_WRITER cuando provider=openrouter (parchea la llamada);
(e) estimate() devuelve n_llamadas > 600 para el juez con el kit.
El test de extremo a extremo en mock sigue por debajo de 60 s.
```

**Aceptación:** tests en verde.

---

### G6 · Trabajos en segundo plano (`geo/jobs.py`)
**Agente:** C · **Ola:** 1 · **Depende de:** contratos de C0
**Objetivo:** lanzar un análisis desde la UI sin bloquearla y poder navegar mientras avanza.

**Archivos:** `geo/jobs.py` (nuevo), `tests/test_jobs.py` (nuevo).

**Especificación:**
```python
def start(*, modo, provider, brief_path, marca_prospecto, meta=None) -> str  # devuelve run_id
def is_running(run_id) -> bool
def any_running() -> str | None
def read_progress(run_id) -> dict | None
def list_runs() -> list[dict]   # run_id, marca, modo, provider, created_at, status, cost_eur, degradados
```
- Registro `_JOBS: dict[str, threading.Thread]` a nivel de módulo, con lock. Streamlit mantiene el módulo cargado entre recargas del script, así que el registro sobrevive a la navegación.
- **Un solo análisis a la vez** (`start()` lanza `RuntimeError` si hay otro vivo). Evita mezclar contadores del tracker global y gastar el doble.
- El hilo ejecuta `run.run_all(auto_approve=True, force=True)` con `run.on_event` y `run.on_progress` conectados a un objeto `_Progress`.
- `_Progress` escribe `runs/<id>/progress.json` de forma atómica (escribir `.tmp` y `replace`), como máximo cada 0,4 s salvo eventos de paso, con:
  ```json
  {"run_id": "...", "status": "running|done|error|interrupted", "started_at": "...", "elapsed_s": 12.3,
   "provider": "openrouter", "models": {...},
   "steps": {"intake": {"status": "done", "duration_s": 1.2, "llm_calls": 1}, "judge": {"status": "running"}, ...},
   "current": "judge", "judge": {"done": 214, "total": 624},
   "llm_calls": 216, "cost_eur": 0.081, "cost_is_real": true, "error": null}
  ```
- `read_progress()` marca `interrupted` si el fichero dice `running` pero no hay hilo vivo (servidor reiniciado).
- El brief subido se copia a `runs/<run_id>/brief_original.<ext>` **antes** de crear el hilo; `brief_path` apunta ahí.
- `list_runs()` ordena con `demo` primero y el resto por fecha descendente.
- Nunca escribir la clave en `progress.json` ni en `state.json`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, sección G6. Implementa geo/jobs.py con la API y el formato de progress.json de G6.
Tests en tests/test_jobs.py (mock, sin red):
(a) start() en mock termina con status "done" y los 10 pasos en done (espera con un bucle de sondeo de hasta 90 s);
(b) un segundo start() mientras corre el primero lanza RuntimeError;
(c) read_progress() de un progress.json "running" sin hilo devuelve "interrupted";
(d) list_runs() devuelve demo primero;
(e) grep de la clave falsa "sk-or-test-123" en todo runs/<id>/ no encuentra nada.
```

**Aceptación:** tests en verde.

---

### G7 · Interfaz I: estructura de aplicación y página de Ajustes
**Agente:** D · **Ola:** 1 (contra stubs) · **Integra en:** I2
**Objetivo:** que al abrir la app se vea un producto: navegación clara, estado de conexión siempre visible y una pantalla de ajustes donde se pega la clave, se prueba y se eligen modelos.

**Archivos:** `.streamlit/config.toml` (nuevo), `app/Home.py`, `app/ui_shared.py`, `app/pages/8_Ajustes.py` (nuevo).

**Especificación de `.streamlit/config.toml`:**
```toml
[client]
toolbarMode = "minimal"        # oculta el menú de desarrollador y "Deploy"
showSidebarNavigation = true

[server]
headless = true
runOnSave = false
maxUploadSize = 20

[browser]
gatherUsageStats = false

[theme]
base = "light"
primaryColor = "#E8590C"
font = "sans serif"
```
(La tipografía Geist ya la inyecta `ui_shared.py`.)

**Navegación nueva en `Home.py`:**
```
(sin sección)  Inicio · Nuevo análisis
Análisis       Ficha · Competencia · Diagnóstico · Hallazgos
Estrategia     Plan · Propuesta
Control        Calidad y trazas · Historial · Ajustes
```
`Nuevo análisis` y `Historial` llegan en G8; en G7 se crean como páginas con un estado vacío (`render_empty`).

**Barra lateral (`shell()`):**
1. Tarjeta del análisis activo (la actual), añadiendo debajo del `run_id` una línea con el proveedor legible: «IA real · OpenRouter» o «Simulado (sin coste)», y el coste del run si existe en `progress.json`.
2. Si `state["degradados"]` no está vacío: chip `warn` «Pasos en modo simulado: plan, write» con enlace a Calidad y trazas.
3. Indicador de conexión, al pie de la barra lateral:
   - Sin clave → chip gris «OpenRouter sin configurar» + `st.page_link` a Ajustes.
   - Con clave y `LLM_PROVIDER=openrouter` → chip `good` «OpenRouter · <modelo del juez>».
   - Con clave y `LLM_PROVIDER=mock` → chip neutro «Modo simulado».
   No hacer peticiones de red desde `shell()`: solo leer ajustes. La validación real está en Ajustes.
4. Botones «Nuevo análisis» (primario) y «Cargar demo» (secundario).

**Página Ajustes (`8_Ajustes.py`)**, con `page_header("Ajustes", "Conexión con OpenRouter, modelos y límites de gasto.")` y tres paneles (`panel()`):

*Panel 1 · Conexión*
- `st.radio` horizontal «Motor de IA por defecto»: «Simulado (sin red ni coste)» / «OpenRouter (IA real)». Deshabilitar OpenRouter si no hay clave, con texto de ayuda.
- `st.text_input(type="password")` para la clave. Si ya hay una guardada, mostrar debajo `mask(clave)` y dejar el campo vacío; vacío al guardar = conservar la actual.
- Botón «Probar conexión» → `test_connection(LLM_MODEL, api_key=<la del campo o la guardada>)` dentro de `st.spinner`. Resultado en `st.success` con: etiqueta de la clave, gasto acumulado y límite (de `/key`), modelo que respondió, latencia y coste de la prueba. Errores en `st.error` con el mensaje en español de `OpenRouterError` (nunca la clave).
- Enlace de ayuda a https://openrouter.ai/keys.

*Panel 2 · Modelos*
- Cargar `list_models()` con `@st.cache_data(ttl=3600)`; si falla (sin red), avisar y pasar a `st.text_input` libres.
- Dos `st.selectbox` con búsqueda: «Juez, intake y revisor» (`LLM_MODEL`) y «Estrategia y redacción» (`LLM_MODEL_WRITER`). `format_func` → `"{name} · {id} · ${in:.2f} / ${out:.2f} por M"`.
- Si el valor guardado no está en el catálogo: `st.warning` «El modelo X no existe en OpenRouter».
- Debajo, una tabla `st.dataframe` de 3 filas con el coste estimado de un análisis completo con esa combinación, llamando a `Run.estimate()` con un run temporal o a una función equivalente sin crear carpeta (crear `geo.orchestrator.estimate_pipeline(provider, models)` si hace falta).
- Expander «Motores del estudio en vivo» con los cuatro `ENGINE_MODEL_*` (solo si se hace G9).

*Panel 3 · Límites*
- `st.slider` concurrencia del juez (1-16, por defecto 8) con ayuda: «Más hilos = más rápido, pero más riesgo de 429».
- `st.number_input` tope de llamadas y tope de gasto en € por análisis.

Botón final «Guardar ajustes» (primario) → `settings.save(...)` → `st.toast("Ajustes guardados")`. Recordar que el `.env` está en `.gitignore`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 1.5 y G7. Revisa app/ui_shared.py para reutilizar page_header, panel, section, chip y render_empty, y añade las clases CSS que necesites al bloque _CSS (nada de estilos en línea nuevos).
1. Crea .streamlit/config.toml como en G7.
2. Reorganiza la navegación de app/Home.py como en G7 (Nuevo análisis e Historial como páginas vacías por ahora).
3. Amplía shell() con los 4 puntos de G7. Sin llamadas de red en shell().
4. Crea app/pages/8_Ajustes.py con los tres paneles y el guardado.
Todo en español de España, sin emojis, coherente con PRODUCT.md.
Arranca streamlit run app/Home.py y comprueba con Playwright (Chromium ya instalado, sin red hacia OpenRouter) que: la página Ajustes carga, guardar escribe .env, y el indicador de la barra lateral cambia a "Modo simulado" o "OpenRouter" según el ajuste. Haz capturas en claro y oscuro y revísalas.
```

**Aceptación:** la app arranca sin errores; capturas revisadas; con el servidor falso (`OPENROUTER_BASE_URL=http://127.0.0.1:8765`) «Probar conexión» muestra éxito, y con `FAKE_OR_FAIL=401` muestra «Clave inválida o revocada».

---

### G8 · Interfaz II: Nuevo análisis, progreso en vivo e historial
**Agente:** E · **Ola:** 1 (contra fixtures de progreso) y 2 (contra jobs real) · **Integra en:** I2
**Objetivo:** lanzar un análisis real con un clic, ver cómo avanza paso a paso y volver a cualquier análisis anterior.

**Archivos:** `app/pages/00_Nuevo_analisis.py` (nuevo), `app/pages/9_Historial.py` (nuevo), `app/ui_jobs.py` (componente de progreso y guardia; `ui_shared.py` es del agente D y no se toca), `app/pages/0_Inicio.py`, `app/pages/5_Plan.py`, `app/pages/6_Propuesta.py`, `app/pages/7_Calidad_y_trazas.py`.

**Página Nuevo análisis** (formulario en dos columnas, `st.form` para no recargar a cada cambio):

Columna izquierda · Qué analizar
- «Tipo de análisis»: `st.segmented_control` Cliente (con brief) / Prospecto (sin brief).
- Cliente: `st.radio` «Brief»: «Usar el brief de ejemplo (Clínica Alborada Visión)» / «Subir archivo (.md, .docx, .txt)» / «Pegar texto». Con «Pegar texto», `st.text_area` de 12 líneas; se guarda como `brief_original.md`.
- Prospecto: `st.selectbox` con las marcas de `marcas.csv` salvo Alborada.
- Nota fija: «El estudio de citación es el del kit: 624 respuestas de ChatGPT, Gemini, Perplexity y Claude. La IA real se usa para interpretar el brief, evaluar cada respuesta, diseñar el plan, redactar y revisar.»

Columna derecha · Cómo ejecutarlo
- «Motor de IA»: Simulado / OpenRouter (deshabilitado sin clave, con `st.page_link` a Ajustes).
- Con OpenRouter: modelos activos (solo lectura, con enlace a Ajustes para cambiarlos) y tarjeta de estimación con `kpi_strip`: llamadas previstas, tokens previstos, coste estimado en € y tiempo estimado (`llamadas_juez / concurrencia × 3 s + 60 s`). Si el coste supera `MAX_BUDGET_EUR`, aviso y botón deshabilitado.
- `st.checkbox` «He revisado el coste estimado» obligatorio con OpenRouter.
- Botón «Lanzar análisis» (primario). Al pulsar: validar, `jobs.start(...)`, `st.session_state["active_run_id"] = run_id`, `st.rerun()`.
- Si `jobs.any_running()`: no mostrar el formulario; mostrar el progreso del trabajo en curso.

**Componente de progreso (`ui_jobs.render_progress(run_id)`)**, dentro de `@st.fragment(run_every=1)`:
- Cabecera: marca, modo, proveedor, tiempo transcurrido, llamadas y coste acumulado («real» o «estimado» según `cost_is_real`).
- Lista de los 10 pasos con nombre legible (reutilizar `STEP_LABELS` de `0_Inicio.py`, copiándolo a `ui_jobs.py`; `0_Inicio.py` pasa a importarlo de ahí) y estado con chip: pendiente (gris), en curso (azul con punto), hecho (verde), simulado por error (ámbar, con el error en `st.caption`), error (rojo). Junto a cada paso hecho: duración y llamadas.
- Paso `judge` en curso: `st.progress(done/total, text="Evaluando respuestas: 214 de 624")`.
- Al terminar (`done`): `st.success` con resumen y botones «Ver diagnóstico» y «Ver propuesta» (`st.page_link`). Si hay degradados, `st.warning` que los nombra.
- Si `error`: `st.error` con el mensaje y un expander con el traceback.
- Si `interrupted`: aviso y botón «Relanzar» (vuelve a llamar a `jobs.start` con los mismos parámetros leídos de `state.json`).
- El fragmento deja de refrescar cuando el estado ya no es `running` (renderizar sin `run_every` en ese caso, o comprobar al inicio y llamar a `st.rerun()` una vez para salir del fragmento).

**Guardia en páginas de análisis (`ui_jobs.guard_active_run()`)**, llamada desde `shell()` (la llamada ya la dejó el líder en C0):
- Si el run activo está corriendo, las páginas Ficha → Calidad muestran `render_progress()` y hacen `st.stop()`. Inicio, Nuevo análisis, Historial y Ajustes siguen navegables.
- Si el run activo está incompleto (falta `propuesta.json`) y no corre: `render_empty("Análisis incompleto", ...)` con botón «Relanzar» en lugar de llamar a `run_all()`.
- Eliminar las llamadas implícitas a `run.run_all(...)` de `5_Plan.py:42`, `6_Propuesta.py:19` y `7_Calidad_y_trazas.py:20` (la guardia ya cubre esos casos).
- `6_Propuesta.py:79` (regenerar la propuesta): si el proveedor del run es `openrouter`, pedir confirmación con el coste estimado de redacción y revisión; ejecutar con `jobs`, no en el script.

**Página Historial:**
- Tabla con `list_runs()`: marca, modo, proveedor («IA real» / «Simulado»), fecha, estado (chip), coste, pasos simulados por error.
- Cada fila con botón «Abrir» (fija `active_run_id` y lleva a Diagnóstico) y «Descargar propuesta» si existe el `.docx`.
- Botón «Duplicar con IA real» en runs simulados: precarga Nuevo análisis con los mismos parámetros (`st.session_state["nuevo_prefill"]`).
- No borrar runs desde la UI (evita perder la demo).

**Inicio (`0_Inicio.py`):**
- Quitar el expander «Configurar una ejecución propia» (sustituido por Nuevo análisis).
- Panel nuevo arriba: «Empieza aquí» con dos tarjetas: «Abrir demostración» (lo actual) y «Nuevo análisis con IA real» (enlace; si no hay clave, el texto dice «Configura OpenRouter en Ajustes»).
- Mantener el recorrido y el estado técnico.

**Marcas de origen:** donde la UI ya usa `render_origin_chip("ai")` («Redactado por IA»), cambiar el texto según el proveedor del run: «Redactado por IA · <modelo>» si fue real y no se degradó; «Plantilla (modo simulado)» si fue mock o se degradó ese paso. Es la forma honesta de enseñarlo al jurado. `render_origin_chip(kind, text)` ya acepta un texto propio, así que E solo cambia las llamadas en sus páginas y no toca `ui_shared.py`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, secciones 1.5, G6 y G8. Usa geo/jobs.py para todo lo que ejecute el pipeline desde la interfaz: ninguna página puede llamar a run_all() directamente.
1. Mueve STEP_LABELS a app/ui_jobs.py e implementa en ese archivo render_progress(run_id) con st.fragment(run_every=1) y guard_active_run() según G8.
2. Crea app/pages/00_Nuevo_analisis.py y app/pages/9_Historial.py según G8.
3. Modifica 0_Inicio.py, 5_Plan.py, 6_Propuesta.py y 7_Calidad_y_trazas.py según G8 (quitar run_all implícitos, regeneración vía jobs con confirmación de coste).
4. Ajusta las marcas de origen IA/plantilla según el proveedor y state["degradados"].
Prueba de extremo a extremo con Playwright y el servidor falso (scripts/fake_openrouter.py con fixtures para intake, strategy, writer y compliance que valgan contra los esquemas; genera esos JSON a partir de la salida mock de runs/demo/):
- Ajustes → clave falsa → OpenRouter → guardar.
- Nuevo análisis → brief de ejemplo → lanzar → ver el progreso del juez avanzar → navegar a Ajustes y volver → el progreso sigue → termina en done.
- Diagnóstico, Hallazgos, Plan y Propuesta cargan sin error con ese run.
- Historial muestra el run nuevo y la demo.
- Repetir con FAKE_OR_FAIL=402: el run termina con los pasos LLM en "simulado por error" y la UI lo avisa.
Haz capturas de cada estado y revísalas antes de dar la fase por terminada.
```

**Aceptación:** el recorrido con el servidor falso funciona entero; ninguna página llama a `run_all()` (`grep -n "run_all" app/` solo devuelve `ui_shared.ensure_demo_run_ready`); capturas revisadas en claro y oscuro.

---

### G9 · (Opcional) Motores del estudio en vivo vía OpenRouter
**Agente:** F · **Ola:** 2 · **Depende de:** I1
**Solo si G0-G8 están en verde.** Máximo 1,5 h.

**Archivos:** `geo/engines/openrouter_engine.py` (nuevo), `geo/engines/__init__.py`, `app/pages/7_Calidad_y_trazas.py` (sección «Conectores en vivo»).

**Especificación:**
- `MOTOR_SETTING = {"ChatGPT": "ENGINE_MODEL_CHATGPT", "Gemini": ..., "Claude": ..., "Perplexity": ...}`.
- `run(motor, prompt, *, repeticion=1, use_cache=True) -> (respuesta, dominios, meta)`:
  - Sistema neutro: «Eres un asistente conversacional. Responde en español de España a la consulta del usuario como lo harías normalmente, citando las fuentes web que consultes.»
  - `chat(..., web_search=True, temperature=0.7, max_tokens=1200)`. Temperatura > 0 a propósito: cada repetición es una muestra, como en el estudio original.
  - Dominios con `extract_domain()` sobre `citations`, sin duplicados.
  - Caché en `cache/engines/openrouter_<sha>.json` (clave: modelo, repetición y prompt).
- `run_engine()`: si `LLM_PROVIDER=openrouter` y hay clave, ir por OpenRouter; si falla y `allow_mock_fallback`, seguir con el conector directo o la simulación actuales.
- `estimate_mini_study_cost()` con precios del catálogo + 0,007 $ por búsqueda web en modelos sin búsqueda nativa.
- UI: la sección actual de «Conectores en vivo» pasa a ejecutarse con `jobs` (o, como es corta, en el script con `st.status`) y muestra por fila: motor, modelo real, dominios citados y coste.
- **Aislamiento:** las filas `LIVE-xxxx` nunca entran en `runs/<id>/` del análisis del kit. Se guardan en `runs/live/<fecha>/ejecuciones_live.parquet`.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, sección G9. Implementa geo/engines/openrouter_engine.py y el enrutado en run_engine() según G9, manteniendo la degradación actual.
Actualiza la sección "Conectores en vivo" de 7_Calidad_y_trazas.py para mostrar modelo, dominios y coste reales.
Tests con monkeypatch de geo.openrouter.chat: run_engine("Perplexity", ...) con LLM_PROVIDER=openrouter devuelve degradado=False y los dominios de las citas; sin clave sigue el comportamiento antiguo (tests de test_engines.py en verde).
```

---

### G10 · Lanzador «como una aplicación»
**Agente:** C · **Ola:** 2
**Objetivo:** abrir GEO Copilot con doble clic, en una ventana propia sin barra del navegador.

**Archivos:** `scripts/geo_copilot.py` (nuevo), `GEO Copilot.command` (macOS, nuevo), `Makefile` (nuevo).

**Especificación:**
- `scripts/geo_copilot.py`:
  1. Comprueba que existe `.venv`; si no, avisa con el comando de instalación.
  2. Busca un puerto libre desde 8501.
  3. Lanza `streamlit run app/Home.py --server.port <p> --server.headless true` como subproceso.
  4. Espera a que `http://localhost:<p>/_stcore/health` responda `ok` (máx. 30 s).
  5. Abre una ventana de aplicación: si encuentra Chrome, Edge o Brave, `--app=http://localhost:<p> --window-size=1440,900`; si no, `webbrowser.open`.
  6. Al cerrar con Ctrl+C, termina el subproceso.
- `GEO Copilot.command`: `cd "$(dirname "$0")" && .venv/bin/python scripts/geo_copilot.py` con `chmod +x`.
- `Makefile`: `install`, `test`, `app`, `demo` (genera `runs/demo/` en mock), `fake-or` (servidor falso).
- Añadir `app/static/` como `static` si se quiere servir el logo como favicon (ya hay `page_icon`).

**Prompt:**
```
Lee PLAN_OPENROUTER.md, sección G10. Crea scripts/geo_copilot.py, "GEO Copilot.command" y un Makefile según G10. Prueba en Linux que el script arranca Streamlit, detecta la salud y se cierra limpio con Ctrl+C (en el contenedor no habrá Chrome: debe caer a webbrowser sin error).
```

---

### G11 · Prueba real con clave y caché de la demo
**Agente:** C escribe el script (ola 2); L lo ejecuta en el Mac con la clave real (ola 2-3)
**Objetivo:** comprobar con dinero real (céntimos) que todo funciona y dejar la caché lista para que la demo no dependa de la red.

Esta fase la ejecutas **tú** en tu Mac con la clave. Claude Code solo prepara el script.

**Archivos:** `scripts/real_smoke.py` (nuevo).

**Especificación de `scripts/real_smoke.py`:**
1. Exige `LLM_PROVIDER=openrouter` y clave; si no, sale con mensaje.
2. `test_connection()` y muestra gasto acumulado y límite de la clave.
3. Imprime la estimación de `estimate_pipeline()` y pide confirmación (`--yes` para saltarla).
4. Ejecuta un **mini-run** primero: el juez solo sobre las 15 ejecuciones de `muestra_evaluada.csv` (filtrar `df_det`), y compara contra la muestra humana con `geo.validation.compare` → imprime accuracy y kappa del juez LLM y del ensemble. Coste: céntimos.
5. Si pasa, ejecuta el pipeline completo con `run_id="demo_real"` y `force=True`.
6. Resumen final: llamadas, tokens, coste real en €, pasos degradados (debe ser 0), cifras trazables del revisor.

**Orden recomendado:**
```bash
cp .env.example .env            # pega la clave en Ajustes o en .env
make test                       # todo en verde, sin red
python scripts/real_smoke.py    # mini-run + pipeline completo, revisa el coste antes de confirmar
make app                        # abre runs/demo_real/ desde Historial y recorre la demo
```

**Para la demo del jurado:**
- `runs/demo_real/` y `cache/` quedan generados. Si en la presentación falla la red, la caché devuelve las mismas respuestas sin llamadas (0 llamadas nuevas, coste 0).
- Dejar el proveedor en OpenRouter y abrir `demo_real` desde Historial. La barra lateral mostrará «IA real · OpenRouter».
- Plan B: «Cargar demo» (mock) sigue funcionando sin red.

**Prompt:**
```
Lee PLAN_OPENROUTER.md, sección G11. Implementa scripts/real_smoke.py con los 6 pasos. No lo ejecutes contra OpenRouter real; pruébalo contra scripts/fake_openrouter.py con OPENROUTER_BASE_URL.
```

**Aceptación (en tu Mac):** mini-run con acierto del juez LLM comparable al de reglas en fuerza y sentimiento; pipeline completo sin pasos degradados; coste real dentro de `MAX_BUDGET_EUR`.

---

### G12 · Documentación
**Agente:** H · **Ola:** 3
**Archivos:** `README.md`, `ARQUITECTURA.md`, `RESUMEN_IMPLEMENTACION.md`, `CLAUDE.md`.

**Contenido mínimo:**
- README: instalación, «Configurar OpenRouter en 1 minuto» (crear clave en openrouter.ai/keys, pegarla en Ajustes, Probar conexión), cómo lanzar un análisis real, coste orientativo por análisis, lanzador de app, plan B sin red.
- ARQUITECTURA: diagrama mermaid actualizado con `jobs` → `Run` → pasos, el tracker de coste y los callbacks de progreso; tabla «qué hace el LLM y con qué modelo»; decisión OpenRouter frente a tres proveedores; paralelismo y tolerancia a fallos del juez; degradación visible.
- RESUMEN_IMPLEMENTACION: añadir G0-G12 y las cifras reales de `demo_real` (llamadas, coste, acierto del juez LLM).
- CLAUDE.md: actualizar proveedores válidos (`mock | openrouter`).

**Prompt:**
```
Lee PLAN_OPENROUTER.md, sección G12, y actualiza la documentación. Las cifras de coste y acierto que cites deben salir de runs/demo_real/trace.jsonl y de la salida de scripts/real_smoke.py; si no existen todavía, deja el hueco marcado como PENDIENTE en lugar de inventarlas.
```

---

## 6. Calendario

El calendario con las olas, los puntos de integración y la cadena crítica está en **M7**. Resumen:

| Momento | Quién | Qué |
|---|---|---|
| T+0:00 | L | G0 + C0 |
| T+0:45 | A, B, C, D, E | Ola 1 en paralelo |
| T+2:15 | L | I1: integra backend (A → C → B) |
| T+2:30 | C, D, E, F; L en el Mac | Ola 2: herramientas, UI contra piezas reales, motores en vivo, mini-run real |
| T+3:45 | L | I2: integra UI (D → E → F) |
| T+4:00 | Q, H; L en el Mac | Ola 3: verificación, documentación, demo_real |
| T+4:45 | dueños de cada archivo | I3: arreglos del informe de Q |
| T+5:15 | todos | Congelación |

**Regla de corte:** si en I1 el pipeline no funciona con OpenRouter contra el servidor falso, F no se lanza y C pasa directamente a ayudar con pruebas de G11.

---

## 7. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| 429 por concurrencia alta | Backoff en `chat()`, fallos por ejecución en el juez, slider de concurrencia en Ajustes (bajar a 4) |
| Modelo sin soporte de `response_format` | Reintento automático sin él; la validación Pydantic con reintento sigue detrás |
| Un modelo devuelve JSON con texto alrededor | `_extract_json_str()` actual ya lo limpia |
| Se agota el saldo a mitad | 402 = `LLMConfigError`: el paso se degrada, la UI lo muestra en ámbar y el resto sigue en mock |
| Gasto inesperado al abrir páginas | Eliminadas las llamadas implícitas a `run_all()`; confirmación de coste para regenerar |
| La clave acaba en el zip de entrega | Solo en `.env` (ignorado); test de G6 que busca la clave en `runs/`; nunca en trazas |
| El servidor se reinicia con un análisis en curso | `progress.json` marca `interrupted` y la UI ofrece «Relanzar»; los pasos hechos se reaprovechan y la caché evita repetir llamadas del juez |
| IDs de modelo obsoletos | Validación contra `/models` en Ajustes y aviso visible |
| Sin red en la presentación | Caché de `demo_real` + demo mock + vídeo de respaldo |
| Contadores mezclados con dos análisis a la vez | `jobs.start()` permite uno solo |
| Dos agentes editan el mismo archivo | Matriz M3 + comprobación `git diff --name-only` antes de cada merge |
| Un agente cambia un contrato por su cuenta | Contratos solo en `coord/CONTRATOS.md`, cambios solo por L con nueva etiqueta y rebase de los afectados |
| Un agente se queda esperando a otro | Todos programan contra stubs o fixtures de C0; nadie necesita la implementación de otro hasta la ola 2 |
| Integración que no cuadra a última hora | Tres integraciones pequeñas (I1, I2, I3) en lugar de una al final |
| El verificador da por buena su propia obra | Q se lanza en sesión limpia, no escribe código de producción y devuelve cada fallo a su dueño |

---

## 8. Checklist final

- [ ] `rm -rf runs cache && pytest -q` en verde, sin red.
- [ ] Ninguna página llama a `run_all()` directamente.
- [ ] Ajustes: guardar clave, probar conexión, elegir modelos con precio, límites.
- [ ] Nuevo análisis: estimación de coste antes de lanzar, progreso en vivo del juez, navegación libre mientras corre.
- [ ] Historial con demo, runs simulados y runs reales.
- [ ] Barra lateral: proveedor, coste del run, pasos degradados.
- [ ] Marcas «Redactado por IA · modelo» solo cuando de verdad lo fue.
- [ ] `runs/demo_real/` generado con OpenRouter, 0 pasos degradados, coste real anotado.
- [ ] Revisor: 100 % de cifras trazables también con redacción real.
- [ ] Clave fuera del repo y de `runs/`.
- [ ] README y ARQUITECTURA actualizados con cifras reales.
- [ ] `coord/informe_Q.md` sin fallos abiertos de severidad alta.
- [ ] `git worktree list` limpio: ramas `ag/*` integradas o descartadas.
