"""Lanzador de la aplicación Preload (FastAPI + React)."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"


def _free_port(start: int = 8000) -> int:
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1


def main() -> None:
    venv = ROOT_DIR / ".venv"
    if not venv.exists():
        print("Falta el entorno virtual .venv. Ejecuta: make install")
        sys.exit(1)

    # Comprobar frontend/dist; si falta, compilar
    if not FRONTEND_DIST.is_dir() or not (FRONTEND_DIST / "index.html").exists():
        print("Compilando frontend (dist no encontrado)...")
        npm_cmd = shutil.which("npm") or "npm"
        res = subprocess.run([npm_cmd, "run", "build"], cwd=str(ROOT_DIR / "frontend"))
        if res.returncode != 0:
            print("Error compilando el frontend.")
            sys.exit(res.returncode)

    port = _free_port(8000)
    # Windows crea el intérprete en Scripts\python.exe; macOS y Linux en bin/python
    python_bin = str(venv / "Scripts" / "python.exe") if os.name == "nt" else str(venv / "bin" / "python")

    print(f"Iniciando Preload en http://localhost:{port} ...", flush=True)
    proc = subprocess.Popen(
        [
            python_bin,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "info",
        ],
        cwd=str(ROOT_DIR),
    )

    url = f"http://localhost:{port}"
    health_url = f"{url}/api/health"

    # Esperar a que el backend responda /api/health
    ready = False
    for _ in range(40):
        try:
            with urllib.request.urlopen(health_url, timeout=2) as r:
                if r.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.5)

    if not ready:
        print("El servidor tardó demasiado en arrancar.")
        proc.terminate()
        sys.exit(1)

    print(f"Preload listo en {url}", flush=True)

    # Abrir navegador en modo ventana app si es posible
    opened = False
    browsers = (
        ["google-chrome", "chromium", "msedge", "brave-browser"]
        if sys.platform != "darwin"
        else [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "google-chrome",
            "chromium",
            "msedge",
        ]
    )

    for b in browsers:
        executable = shutil.which(b) or (b if os.path.exists(b) else None)
        if executable:
            try:
                subprocess.Popen([executable, f"--app={url}", "--window-size=1440,900"])
                opened = True
                break
            except Exception:
                continue

    if not opened:
        webbrowser.open(url)

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nCerrando Preload limpiamente...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        sys.exit(0)


if __name__ == "__main__":
    main()
