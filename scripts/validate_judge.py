"""CLI para validar el juez (reglas, LLM, ensemble) contra muestra_evaluada.csv."""

import argparse
import os
from pathlib import Path
import sys
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.config import LLM_PROVIDER
from geo.detection import detect
from geo.judge import combine_rules_and_llm
from geo.judge_llm import FEW_SHOT_EJECUCION_IDS, estimate_judge_llm_workload, judge_llm
from geo.judge_rules import judge_rules
from geo.llm import get_llm_stats
from geo.loader import load_ejecuciones, load_fuentes, load_marcas, load_muestra
from geo.validation import compare


def print_single_validation_report(
    title: str,
    report_present: dict[str, dict],
    report_all: dict[str, dict],
    show_discrepancies: bool = True,
) -> None:
    """Imprime un informe detallado de un juez individual (accuracy, kappa, matriz de confusión y discrepancias)."""
    print(f"=== {title} ===")
    print(
        f"{'Campo':<16} | {'Acc (ap=1)':>14} | {'Kappa (ap=1)':>12} | "
        f"{'Acc (todas)':>15} | {'Kappa (todas)':>13}"
    )
    print("-" * 80)
    for campo in ("tipo_mencion", "fuerza", "sentimiento", "tipo_fuente"):
        rp = report_present[campo]
        ra = report_all[campo]
        acc_p = f"{rp['aciertos']}/{rp['n']} ({rp['accuracy']:.1%})"
        acc_a = f"{ra['aciertos']}/{ra['n']} ({ra['accuracy']:.1%})"
        print(
            f"{campo:<16} | {acc_p:>14} | {rp['kappa']:>12.3f} | "
            f"{acc_a:>15} | {ra['kappa']:>13.3f}"
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


def print_comparative_table(
    rep_rules: dict[str, dict],
    rep_llm: dict[str, dict],
    rep_ens: dict[str, dict],
    excluded_ids: set[str],
) -> None:
    """Imprime la tabla comparativa Reglas vs LLM vs Ensemble excluyendo las 3 ejecuciones few-shot."""
    print(
        f"\n=== Tabla Comparativa: Reglas vs LLM vs Ensemble "
        f"(aparece=1, excluidas few-shot {sorted(excluded_ids)}) ==="
    )
    print(
        f"{'Campo':<16} | {'Reglas (Acc / κ)':>20} | {'LLM (Acc / κ)':>20} | {'Ensemble (Acc / κ)':>20}"
    )
    print("-" * 86)
    for campo in ("tipo_mencion", "fuerza", "sentimiento", "tipo_fuente"):
        r = rep_rules[campo]
        l = rep_llm[campo]
        e = rep_ens[campo]
        s_r = f"{r['accuracy']:.1%} / {r['kappa']:.3f}"
        s_l = f"{l['accuracy']:.1%} / {l['kappa']:.3f}"
        s_e = f"{e['accuracy']:.1%} / {e['kappa']:.3f}"
        print(f"{campo:<16} | {s_r:>20} | {s_l:>20} | {s_e:>20}")


def main() -> None:
    """Punto de entrada CLI para validar el juez."""
    parser = argparse.ArgumentParser(description="Valida el juez GEO contra muestra_evaluada.csv")
    parser.add_argument(
        "--judge",
        choices=["rules", "llm", "ensemble"],
        default="rules",
        help="Tipo de juez a validar (rules | llm | ensemble)",
    )
    parser.add_argument(
        "--full-corpus",
        action="store_true",
        help="Ejecuta además el juez sobre las 624 ejecuciones del corpus completo",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Salta la confirmación interactiva antes de lanzar llamadas reales al LLM",
    )
    args = parser.parse_args()

    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().lower() or "mock"
    marcas = load_marcas()
    df_ej = load_ejecuciones()
    muestra = load_muestra()
    catalogo = load_fuentes()

    ej_ids_muestra = set(muestra["ejecucion_id"].unique())
    df_ej_target = df_ej if args.full_corpus else df_ej[df_ej["ejecucion_id"].isin(ej_ids_muestra)].copy()
    df_det = detect(df_ej_target, marcas)

    if args.judge == "rules":
        df_rules = judge_rules(df_det, df_ej_target, marcas, catalogo)
        rep_present = compare(df_rules, muestra, only_present=True)
        rep_all = compare(df_rules, muestra, only_present=False)
        print_single_validation_report(
            "Validación del Juez por Reglas (F3 · 15 ejecuciones de muestra)",
            rep_present,
            rep_all,
        )
        return

    # Estimación previa de llamadas, tokens y coste (F4)
    est = estimate_judge_llm_workload(df_det, df_ej_target)
    print("=== Estimación previa de llamadas LLM ===")
    print(f"Proveedor activo   : {provider}")
    print(f"Llamadas máximas   : {est['n_calls']}")
    print(f"Tokens entrada est.: {est['tokens_in_est']}")
    print(f"Tokens salida est. : {est['tokens_out_est']}")
    print(f"Coste estimado     : ~{est['cost_est_eur']:.4f} EUR")

    if provider != "mock" and not args.yes:
        ans = input("¿Deseas continuar con las llamadas reales al LLM? [s/N]: ").strip().lower()
        if ans not in ("s", "si", "sí", "y", "yes"):
            print("Ejecución cancelada por el usuario.")
            return

    df_rules = judge_rules(df_det, df_ej_target, marcas, catalogo)
    df_llm = judge_llm(df_det, df_ej_target, marcas, catalogo, provider=provider)
    df_ens = combine_rules_and_llm(df_rules, df_llm, df_ej_target, marcas, catalogo)

    target_df = df_llm if args.judge == "llm" else df_ens
    label = "Juez LLM (F4)" if args.judge == "llm" else "Juez Ensemble Reglas + LLM (F4)"

    rep_present = compare(
        target_df,
        muestra,
        only_present=True,
        exclude_ejecucion_ids=FEW_SHOT_EJECUCION_IDS,
    )
    rep_all = compare(
        target_df,
        muestra,
        only_present=False,
        exclude_ejecucion_ids=FEW_SHOT_EJECUCION_IDS,
    )
    print_single_validation_report(
        f"Validación de {label} (excluidas few-shot {sorted(FEW_SHOT_EJECUCION_IDS)})",
        rep_present,
        rep_all,
        show_discrepancies=False,
    )

    rep_rules_comp = compare(
        df_rules,
        muestra,
        only_present=True,
        exclude_ejecucion_ids=FEW_SHOT_EJECUCION_IDS,
    )
    rep_llm_comp = compare(
        df_llm,
        muestra,
        only_present=True,
        exclude_ejecucion_ids=FEW_SHOT_EJECUCION_IDS,
    )
    rep_ens_comp = compare(
        df_ens,
        muestra,
        only_present=True,
        exclude_ejecucion_ids=FEW_SHOT_EJECUCION_IDS,
    )
    print_comparative_table(
        rep_rules_comp,
        rep_llm_comp,
        rep_ens_comp,
        FEW_SHOT_EJECUCION_IDS,
    )

    stats = get_llm_stats()
    print(
        f"\nEstadísticas LLM: llamadas nuevas={stats['calls']}, "
        f"aciertos de caché={stats['cache_hits']}, "
        f"tokens_in={stats['tokens_in']}, tokens_out={stats['tokens_out']}, "
        f"coste_est={stats['estimated_cost_eur']:.6f} EUR"
    )


if __name__ == "__main__":
    main()
