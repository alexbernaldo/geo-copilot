# Contratos (firmas congeladas, C0)

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
