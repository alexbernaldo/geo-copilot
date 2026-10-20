"""CLI para validar el juez (reglas, LLM, ensemble) contra muestra_evaluada.csv."""

import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.detection import detect
from geo.judge_rules import judge_rules
from geo.loader import load_ejecuciones, load_fuentes, load_marcas, load_muestra
from geo.validation import compare


def print_validation_report(
    title: str,
    report_present: dict[str, dict],
    report_all: dict[str, dict],
    show_discrepancies: bool = True,
) -> None:
    """Imprime un informe legible de accuracy, kappa, matriz de confusión y discrepancias."""
    print(f"=== {title} ===")
    print(
        f"{'Campo':<16} | {'Acc (ap=1)':>12} | {'Kappa (ap=1)':>12} | "
        f"{'Acc (todas)':>12} | {'Kappa (todas)':>13}"
    )
    print("-" * 76)
    for campo in ("tipo_mencion", "fuerza", "sentimiento", "tipo_fuente"):
        rp = report_present[campo]
        ra = report_all[campo]
        acc_p = f"{rp['aciertos']}/{rp['n']} ({rp['accuracy']:.1%})"
        acc_a = f"{ra['aciertos']}/{ra['n']} ({ra['accuracy']:.1%})"
        print(
            f"{campo:<16} | {acc_p:>12} | {rp['kappa']:>12.3f} | "
            f"{acc_a:>12} | {ra['kappa']:>13.3f}"
        )

    for campo in ("tipo_mencion", "fuerza", "sentimiento", "tipo_fuente"):
        rp = report_present[campo]
        print(f"\n--- Matriz de confusión ({campo}, aparece=1, n={rp['n']}) ---")
        cm_df = pd.DataFrame(
            rp["confusion_matrix"],
            index=[f"real:{l}" for l in rp["labels"]],
            columns=[f"pred:{l}" for l in rp["labels"]],
        )
        print(cm_df.to_string())
        if show_discrepancies and rp["discrepancias"]:
            print(f"Discrepancias en {campo} ({len(rp['discrepancias'])}):")
            for d in rp["discrepancias"][:10]:
                print(
                    f"  - {d['ejecucion_id']} | {d['marca']} (pos={d['posicion']}): "
                    f"esperado='{d['esperado']}' vs predicho='{d['predicho']}'"
                )


def main() -> None:
    """Punto de entrada CLI para validar el juez."""
    parser = argparse.ArgumentParser(description="Valida el juez GEO contra muestra_evaluada.csv")
    parser.add_argument(
        "--judge",
        choices=["rules", "llm", "ensemble"],
        default="rules",
        help="Tipo de juez a validar (por defecto: rules)",
    )
    args = parser.parse_args()

    marcas = load_marcas()
    df_ej = load_ejecuciones()
    muestra = load_muestra()
    catalogo = load_fuentes()

    # Filtramos solo las 15 ejecuciones de la muestra para validar rápido
    ej_ids_muestra = set(muestra["ejecucion_id"].unique())
    df_ej_muestra = df_ej[df_ej["ejecucion_id"].isin(ej_ids_muestra)].copy()
    df_det = detect(df_ej_muestra, marcas)

    if args.judge == "rules":
        df_pred = judge_rules(df_det, df_ej_muestra, marcas, catalogo)
        rep_present = compare(df_pred, muestra, only_present=True)
        rep_all = compare(df_pred, muestra, only_present=False)
        print_validation_report(
            "Validación del Juez por Reglas (F3)",
            rep_present,
            rep_all,
        )
    else:
        print(f"El modo --judge {args.judge} se habilita en la Fase F4.")


if __name__ == "__main__":
    main()
