"""Prueba real con clave OpenRouter y caché de la demo."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo import settings
from geo.config import MUESTRA_EVALUADA_CSV, RUNS_DIR, BRIEF_MD
from geo.openrouter import test_connection
from geo.orchestrator import estimate_pipeline, Run
from geo import validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    if settings.get("LLM_PROVIDER") != "openrouter" or not settings.has_openrouter_key():
        print("Requiere LLM_PROVIDER=openrouter y clave. Configura en Ajustes o .env.")
        sys.exit(1)

    info = test_connection(settings.get("LLM_MODEL"))
    print("Conexión:", info)
    print("Gasto acumulado:", info["key"].get("usage"), "/", info["key"].get("limit"))

    est = estimate_pipeline("openrouter", {"juez_y_revisor": settings.get("LLM_MODEL"), "estrategia_y_redaccion": settings.get("LLM_MODEL_WRITER")})
    print("Estimación:", est)
    if not args.yes:
        ans = input("¿Continuar con el mini-run? [y/N] ")
        if ans.lower() != "y":
            sys.exit(0)

    # mini-run: judge solo sobre muestra_evaluada (filtrar det)
    import pandas as pd
    from geo.loader import load_ejecuciones, load_marcas, load_fuentes
    from geo.detection import detect
    from geo.judge import judge_ensemble
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    catalogo = load_fuentes()
    muestra = pd.read_csv(MUESTRA_EVALUADA_CSV, encoding="utf-8-sig")
    ids = set(muestra["ejecucion_id"].astype(str).tolist()) if "ejecucion_id" in muestra.columns else set()
    df_det = detect(df_ej, marcas)
    if ids:
        df_det = df_det[df_det["ejecucion_id"].astype(str).isin(ids)]
    df_eval = judge_ensemble(df_det, df_ej, marcas, catalogo, provider="openrouter", persist_path=None)
    try:
        rep = validation.compare(df_eval, pd.read_csv(MUESTRA_EVALUADA_CSV, encoding="utf-8-sig"))
        print("Validación:", rep)
    except Exception as exc:
        print("Validación no disponible:", exc)

    if not args.yes:
        ans = input("¿Ejecutar pipeline completo demo_real? [y/N] ")
        if ans.lower() != "y":
            sys.exit(0)

    run = Run(run_id="demo_real", modo="cliente", brief_path=BRIEF_MD, provider="openrouter")
    prop = run.run_all(auto_approve=True, force=True)
    print("Pipeline completado", run.run_id)
    print("Pasos degradados:", run.state.get("degradados", {}))


if __name__ == "__main__":
    main()
