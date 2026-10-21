"""Servidor HTTP falso compatible con la API de OpenRouter para tests y desarrollo.

Uso: python scripts/fake_openrouter.py --port 8763

Rutas: GET /models, GET /key, POST /chat/completions, POST /_config (marcas que citan los motores).
Fallos (variable de entorno FAKE_OR_FAIL, leída en cada petición): 401 | 402 | 429_once | 500_always | 500_once | bad_json.
Retraso opcional por petición: FAKE_OR_DELAY_MS.

Respuestas estructuradas (cuando la petición lleva mensaje de sistema o response_format json):
- juez (marcas_detectadas), y cualquier prompt cuya versión aparece en el texto (intake_v1, strategy_v1, ...):
  tests/fixtures/fake_openrouter/<prompt_version>.json (si falta: {}).
- brands_v1, prompt_bank_v1 y sources_v1: se generan a partir de los datos de la petición (<datos>...</datos>)
  y de las fixtures brands_v1.json, prompt_bank_v1.json y sources_v1.json.
Respuestas de motor (petición sin mensaje de sistema ni response_format): texto que menciona marcas, con citas
`url_citation` (o `citations` de nivel superior para perplexity/*) cuando la petición activa la búsqueda web.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
import unicodedata
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT_DEFAULT = 8763
ROOT = Path(__file__).resolve().parent.parent

_lock = threading.Lock()
_call_counter = {"n": 0, "errores_500": 0}
_config: dict = {"marcas": []}

KNOWN_VERSIONS = [
    "brands_v1",
    "prompt_bank_v1",
    "sources_v1",
    "intake_v1",
    "strategy_v1",
    "writer_client_v1",
    "writer_prospect_v1",
    "compliance_v1",
    "judge_v1",
]

MODELS = [
    ("fake/model", "Fake Model", 8192, "0.0000001", "0.0000002"),
    ("google/gemini-2.5-flash", "Gemini Flash", 1000000, "0.0000001", "0.0000004"),
    ("openai/gpt-4o-mini", "GPT-4o mini", 128000, "0.00000015", "0.0000006"),
    ("anthropic/claude-haiku-4.5", "Claude Haiku 4.5", 200000, "0.000001", "0.000005"),
    ("anthropic/claude-sonnet-4.5", "Claude Sonnet 4.5", 200000, "0.000003", "0.000015"),
    ("perplexity/sonar", "Perplexity Sonar", 128000, "0.000001", "0.000001"),
]


def reset_state() -> None:
    """Reinicia los contadores (para tests que reutilizan el servidor)."""
    with _lock:
        _call_counter["n"] = 0
        _call_counter["errores_500"] = 0
        _config["marcas"] = []


def _fail_mode() -> str | None:
    return os.environ.get("FAKE_OR_FAIL")


def _fixtures_dir() -> Path:
    env = os.environ.get("FAKE_OR_FIXTURES")
    return Path(env) if env else ROOT / "tests" / "fixtures" / "fake_openrouter"


def _load_fixture(prompt_version: str) -> dict:
    path = _fixtures_dir() / f"{prompt_version}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _slug(text: str) -> str:
    return _norm(text).replace(" ", "-") or "marca"


def _domain(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    host = (urlparse(raw).netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


def _datos(messages_or_text) -> dict:
    if isinstance(messages_or_text, list):
        texts = [m.get("content", "") for m in reversed(messages_or_text) if m.get("role") == "user"]
        texts.append(" ".join(m.get("content", "") for m in messages_or_text if isinstance(m.get("content", ""), str)))
    elif isinstance(messages_or_text, str):
        texts = [messages_or_text]
    else:
        texts = []

    for text in texts:
        for m in reversed(list(re.finditer(r"<datos>(.*?)</datos>", text, re.DOTALL))):
            try:
                obj = json.loads(m.group(1).strip())
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
    return {}


def _detect_prompt_version(messages) -> str:
    text = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content", ""), str))
    for pv in KNOWN_VERSIONS:
        if pv in text:
            return pv
    low = text.lower()
    if "marcas_detectadas" in low:
        return "judge_v1"
    if "plan" in low and "estrateg" in low:
        return "strategy_v1"
    if "propuesta" in low or "redact" in low:
        return "writer_client_v1"
    if "compliance" in low or "revisor" in low:
        return "compliance_v1"
    if "intake" in low or "brief" in low:
        return "intake_v1"
    return "intake_v1"


# ---------------------------------------------------------------- generadores estructurados


def _gen_brands(payload: dict) -> dict:
    ficha = payload.get("ficha") or {}
    limites = payload.get("limites") or {}
    fix = _load_fixture("brands_v1")
    pool = fix.get("pool") or []
    marca = str(ficha.get("marca") or "Marca del proyecto")
    web = _domain(str(ficha.get("web") or "")) or f"{_slug(marca)}.example"
    out = [
        {
            "nombre": marca,
            "nivel": "foco",
            "rol": "MARCA DEL BRIEF",
            "dominio": web,
            "alias": [marca.split()[0]] if " " in marca else [],
            "motivo": "Marca del proyecto.",
            "fuente_url": f"https://{web}/",
        }
    ]
    usados = {_norm(marca)}
    for c in ficha.get("competidores_declarados") or []:
        if _norm(c) in usados:
            continue
        usados.add(_norm(c))
        out.append(
            {
                "nombre": c,
                "nivel": "foco",
                "rol": "competidor declarado",
                "dominio": f"{_slug(c)}.example",
                "alias": [],
                "motivo": "Declarado en el brief.",
                "fuente_url": f"https://{_slug(c)}.example/",
            }
        )
    max_total = int(limites.get("max_total") or 12)
    for i, p in enumerate(pool):
        if len(out) >= max_total + 2:
            break
        if _norm(p["nombre"]) in usados:
            continue
        usados.add(_norm(p["nombre"]))
        out.append(
            {
                "nombre": p["nombre"],
                "nivel": "foco" if i < 3 else "contexto",
                "rol": "líder de mercado" if i == 0 else "competidor detectado",
                "dominio": p["dominio"],
                "alias": list(p.get("alias") or []),
                "motivo": "Aparece en el mercado indicado.",
                "fuente_url": f"https://{p['dominio']}/",
            }
        )
    with _lock:
        # Las respuestas de motor posteriores citan las marcas de la propuesta.
        _config["marcas"] = [
            {"nombre": m["nombre"], "dominio": m.get("dominio") or f"{_slug(m['nombre'])}.example"}
            for m in out
        ]
    return {"marcas": out}


def _gen_bank(payload: dict) -> dict:
    ficha = payload.get("ficha") or {}
    fix = _load_fixture("prompt_bank_v1")
    sector = re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", str(ficha.get("sector") or ""))).strip().lower() or "este sector"
    servicios = ficha.get("servicios_prioritarios") or []
    servicio = str(servicios[0]).lower() if servicios else sector
    plantillas = []
    for t in fix.get("plantillas") or []:
        item = dict(t)
        item["plantilla"] = str(t["plantilla"]).replace("{sector}", sector).replace("{servicio}", servicio)
        plantillas.append(item)
    if os.environ.get("FAKE_OR_BANK_BAD"):
        # plantilla espontánea que nombra la marca del proyecto: el código debe rechazarla
        plantillas.append(
            {
                "familia": "DG",
                "prioridad": "P1",
                "uso": "Publicable",
                "instanciacion": "generico",
                "plantilla": f"¿Es {ficha.get('marca', 'esta marca')} la mejor opción de {sector}?",
            }
        )
    return {"plantillas": plantillas}


def _gen_sources(payload: dict) -> dict:
    overrides = _load_fixture("sources_v1").get("overrides") or {}
    kw = [
        (("facebook", "instagram", "reddit", "foro", "youtube", "tiktok"), "Red social / foro"),
        (("opiniones", "resenas", "trustpilot", "valoraciones"), "Plataforma de reseñas"),
        (("gob", "colegio", "sociedad", "universidad", "ranking", "asociacion"), "Ranking / institución"),
        (("directorio", "comparador", "guia", "buscador", "listado"), "Directorio / comparador"),
        (("diario", "periodico", "noticias", "revista", "prensa", "economia"), "Medio"),
    ]
    res = []
    for d in payload.get("dominios") or []:
        tipo = overrides.get(d)
        if not tipo:
            low = _norm(d)
            tipo = next((t for ks, t in kw if any(k in low for k in ks)), "Directorio / comparador")
        res.append({"dominio": d, "tipo": tipo})
    return {"dominios": res}


def _gen_judge(text_all: str) -> dict:
    payload = _datos(text_all)
    marcas = payload.get("marcas_detectadas", [])
    fragmento = payload.get("fragmento", "")
    cita = (fragmento or "")[:80]
    return {
        "juicios": [
            {
                "marca": mk,
                "comparacion": "Comparación neutra",
                "fuerza": 1,
                "sentimiento": "neutro",
                "cita_textual": cita,
            }
            for mk in marcas
        ]
    }


# ---------------------------------------------------------------- respuestas de motor

TERCEROS = [
    "directorio-sector.example",
    "diario-economia.example",
    "opiniones-clientes.example",
    "foro-consumidores.example",
    "guia-profesionales.example",
]


def _engine_brands() -> list[dict]:
    with _lock:
        marcas = list(_config["marcas"])
    if marcas:
        return marcas
    pool = _load_fixture("brands_v1").get("pool") or []
    return [{"nombre": p["nombre"], "dominio": p["dominio"]} for p in pool] or [
        {"nombre": "Marca Alfa", "dominio": "marca-alfa.example"},
        {"nombre": "Marca Beta", "dominio": "marca-beta.example"},
        {"nombre": "Marca Gamma", "dominio": "marca-gamma.example"},
    ]


def _gen_engine(model: str, prompt: str, web: bool) -> tuple[str, list[str]]:
    marcas = _engine_brands()
    seed = zlib.crc32(f"{model}|{prompt}".encode("utf-8"))
    mencionadas = [m for m in marcas if _norm(m["nombre"]) in _norm(prompt)]
    resto = [m for m in marcas if m not in mencionadas]
    if resto:
        k = seed % len(resto)
        resto = resto[k:] + resto[:k]
    elegidas = (mencionadas + resto)[: max(3, len(mencionadas))]
    lineas = []
    for i, m in enumerate(elegidas, start=1):
        adj = ("la opción más recomendable", "una alternativa muy bien valorada", "una opción sólida")[min(i - 1, 2)]
        lineas.append(f"{i}. {m['nombre']}: {adj}.")
    texto = "Según las fuentes consultadas, estas son las opciones más relevantes:\n" + "\n".join(lineas)
    urls = []
    if web:
        for m in elegidas[:2]:
            dom = m.get("dominio") or f"{_slug(m['nombre'])}.example"
            urls.append(f"https://www.{dom}/")
        urls.append(f"https://{TERCEROS[seed % len(TERCEROS)]}/articulo-{seed % 97}")
    return texto, urls


# ---------------------------------------------------------------- servidor


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/models":
            models = [
                {
                    "id": mid,
                    "name": name,
                    "context_length": ctx,
                    "pricing": {"prompt": pin, "completion": pout},
                }
                for mid, name, ctx, pin, pout in MODELS
            ]
            self._send(200, {"data": models})
            return
        if path == "/key":
            self._send(200, {"data": {"label": "test-key", "usage": 0.0, "limit": 10.0, "is_free_tier": True}})
            return
        self._send(404, {"error": {"code": 404, "message": "not found"}})

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            obj = json.loads(raw)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/_config":
            req = self._read_json()
            with _lock:
                _config["marcas"] = [
                    {"nombre": m["nombre"], "dominio": m.get("dominio") or f"{_slug(m['nombre'])}.example"}
                    for m in req.get("marcas", [])
                ]
            self._send(200, {"ok": True, "marcas": len(_config["marcas"])})
            return
        if path != "/chat/completions":
            self._send(404, {"error": {"code": 404, "message": "not found"}})
            return

        delay = os.environ.get("FAKE_OR_DELAY_MS")
        if delay:
            time.sleep(int(delay) / 1000.0)

        mode = _fail_mode()
        if mode == "429_once":
            with _lock:
                _call_counter["n"] += 1
                primera = _call_counter["n"] == 1
            if primera:
                self._send(429, {"error": {"code": 429, "message": "rate limited"}})
                return
        if mode == "500_once":
            with _lock:
                _call_counter["errores_500"] += 1
                primera = _call_counter["errores_500"] == 1
            if primera:
                self._send(500, {"error": {"code": 500, "message": "server error"}})
                return
        if mode == "401":
            self._send(401, {"error": {"code": 401, "message": "invalid key"}})
            return
        if mode == "402":
            self._send(402, {"error": {"code": 402, "message": "no credits"}})
            return
        if mode == "500_always":
            self._send(500, {"error": {"code": 500, "message": "server error"}})
            return
        if mode == "bad_json":
            body = b"{not valid json"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        req = self._read_json()
        model = req.get("model", "fake/model")
        messages = req.get("messages", [])
        text_all = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content", ""), str))
        web = bool(req.get("plugins")) or str(model).startswith("perplexity/")
        structured = bool(req.get("response_format")) or any(m.get("role") == "system" for m in messages)

        extra: dict = {}
        message: dict = {"role": "assistant"}
        usage = {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.0001}
        if structured:
            if "marcas_detectadas" in text_all:
                result = _gen_judge(text_all)
            else:
                pv = _detect_prompt_version(messages)
                payload = _datos(messages)
                if pv == "brands_v1":
                    result = _gen_brands(payload)
                elif pv == "prompt_bank_v1":
                    result = _gen_bank(payload)
                elif pv == "sources_v1":
                    result = _gen_sources(payload)
                else:
                    result = _load_fixture(pv)
            message["content"] = json.dumps(result, ensure_ascii=False)
            if web:
                urls = [f"https://{TERCEROS[0]}/fuente"]
                message["annotations"] = [{"type": "url_citation", "url_citation": {"url": u}} for u in urls]
        else:
            prompt = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
            texto, urls = _gen_engine(str(model), str(prompt), web)
            message["content"] = texto
            usage = {
                "prompt_tokens": 120 + len(prompt) // 4,
                "completion_tokens": max(1, len(texto) // 4),
                "cost": 0.0012,
            }
            if urls:
                if str(model).startswith("perplexity/"):
                    extra["citations"] = urls
                else:
                    message["annotations"] = [
                        {"type": "url_citation", "url_citation": {"url": u, "title": _domain(u)}} for u in urls
                    ]

        resp_obj = {"id": "fake-1", "model": model, "choices": [{"message": message}], "usage": usage, **extra}
        self._send(200, resp_obj)

    def log_message(self, *args):
        return


def make_server(port: int = 0, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """Crea el servidor (port=0: puerto libre). Llamar a serve_forever() en un hilo o en el proceso principal."""
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    return httpd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    args = parser.parse_args()
    httpd = make_server(args.port)
    print(f"fake_openrouter listening on {args.port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
