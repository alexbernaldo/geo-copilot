"""Lanzador de la aplicación GEO Copilot."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
APP = ROOT_DIR / "app" / "Home.py"


def _free_port(start: int = 8501) -> int:
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
        print("Falta .venv. Ejecuta: python -m venv .venv && .venv/bin/pip install -r requirements.txt")
        sys.exit(1)
    port = _free_port(8501)
    cmd = [str(venv / "bin" / "python"), "-m", "streamlit", "run", str(APP),
           "--server.port", str(port), "--server.headless", "true"]
    proc = subprocess.Popen(cmd, cwd=str(ROOT_DIR))
    url = f"http://localhost:{port}"
    # wait for health
    import urllib.request
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as r:
                if r.read().decode().strip() == "ok":
                    break
        except Exception:
            time.sleep(1)
    # open app window
    for browser in ("google-chrome", "chromium", "msedge", "brave-browser"):
        import shutil
        if shutil.which(browser):
            subprocess.Popen([browser, f"--app={url}", "--window-size=1440,900"])
            break
    else:
        webbrowser.open(url)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
