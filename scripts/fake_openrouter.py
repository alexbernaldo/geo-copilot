"""Servidor HTTP falso compatible con la API de OpenRouter para tests y desarrollo."""

from __future__ import annotations

import argparse
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

PORT_DEFAULT = 8765


def _fail_mode() -> str | None:
    return os.environ.get("FAKE_OR_FAIL")


_call_counter = {"n": 0}


def _load_fixture(prompt_version: str) -> dict:
    base = os.path.join("tests", "fixtures", "fake_openrouter")
    path = os.path.join(base, f"{prompt_version}.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _detect_prompt_version(messages) -> str:
    # busca en el system o user alguna pista; por defecto intake_v1
    text = " ".join(m.get("content", "") for m in messages)
    for pv in ["intake_v1", "strategy_v1", "writer_client_v1", "writer_prospect_v1", "compliance_v1", "judge_v1"]:
        if pv in text:
            return pv
    # heurísticas por palabras
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
                {"id": "fake/model", "name": "Fake Model", "context_length": 8192,
                 "pricing": {"prompt": "0.0000001", "completion": "0.0000002"}},
                {"id": "google/gemini-2.5-flash", "name": "Gemini Flash", "context_length": 1000000,
                 "pricing": {"prompt": "0.0000001", "completion": "0.0000004"}},
            ]
            self._send(200, {"data": models})
            return
        if path == "/key":
            key = self.headers.get("Authorization", "")
            self._send(200, {"data": {"label": "test-key", "usage": 0.0, "limit": 10.0, "is_free_tier": True}})
            return
        self._send(404, {"error": {"code": 404, "message": "not found"}})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/chat/completions":
            self._send(404, {"error": {"code": 404, "message": "not found"}})
            return

        mode = _fail_mode()
        # 429_once
        if mode == "429_once":
            _call_counter["n"] += 1
            if _call_counter["n"] == 1:
                self._send(429, {"error": {"code": 429, "message": "rate limited"}})
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

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            req = json.loads(raw)
        except Exception:
            req = {}
        messages = req.get("messages", [])
        user_msg = ""
        for m in messages:
            if m.get("role") == "user":
                user_msg = m.get("content", "")
        text_all = " ".join(m.get("content", "") for m in messages)

        # juez: marcas_detectadas
        if "marcas_detectadas" in text_all:
            import re
            # extraer JSON de <datos>...</datos>
            m = re.search(r"<datos>(.*?)</datos>", text_all, re.DOTALL)
            payload = {}
            if m:
                try:
                    payload = json.loads(m.group(1))
                except Exception:
                    payload = {}
            marcas = payload.get("marcas_detectadas", []) if isinstance(payload, dict) else []
            fragmento = payload.get("fragmento", "") if isinstance(payload, dict) else ""
            cita = (fragmento or "")[:80]
            juicios = []
            for mk in marcas:
                juicios.append({
                    "marca": mk,
                    "comparacion": "Comparación neutra",
                    "fuerza": 1,
                    "sentimiento": "neutro",
                    "cita_textual": cita,
                })
            result = {"juicios": juicios}
        else:
            pv = _detect_prompt_version(messages)
            result = _load_fixture(pv)

        resp_obj = {
            "id": "fake-1",
            "model": req.get("model", "fake/model"),
            "choices": [{"message": {"role": "assistant", "content": json.dumps(result, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.0001},
        }
        self._send(200, resp_obj)

    def log_message(self, *args):
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT_DEFAULT)
    args = parser.parse_args()
    httpd = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"fake_openrouter listening on {args.port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
