"""Comparación de evaluaciones frente a muestra_evaluada.csv (accuracy, kappa, matriz de confusión)."""

from typing import Any
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

CAMPOS_VALIDACION: tuple[str, ...] = (
    "tipo_mencion",
    "fuerza",
    "sentimiento",
    "tipo_fuente",
)


def _norm_label(val: object) -> str:
    """Convierte valores nulos o NaN en '<ausente>' y el resto en str para métricas de clasificación."""
    if val is None or pd.isna(val):
        return "<ausente>"
    return str(val).strip()


def compare(
    pred: pd.DataFrame,
    muestra: pd.DataFrame,
    *,
    only_present: bool = True,
    exclude_ejecucion_ids: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Compara las predicciones del juez contra muestra_evaluada.csv por campo.

    Por defecto evalúa sobre las filas donde la marca aparece (`only_present=True`), que es donde el juez
    toma decisiones no triviales, e incluye también el cálculo global si `only_present=False`.
    Devuelve por cada campo en ('tipo_mencion', 'fuerza', 'sentimiento', 'tipo_fuente'):
      - accuracy: float
      - kappa: float
      - n: int
      - aciertos: int
      - labels: list[str]
      - confusion_matrix: list[list[int]]
      - discrepancias: list[dict]
    """
    merged = muestra.merge(
        pred,
        on=["ejecucion_id", "marca"],
        suffixes=("_muestra", "_pred"),
        how="inner",
    )

    if exclude_ejecucion_ids:
        merged = merged[~merged["ejecucion_id"].isin(exclude_ejecucion_ids)].copy()

    if only_present:
        merged = merged[merged["aparece_muestra"] == 1].copy()

    report: dict[str, dict[str, Any]] = {}
    for campo in CAMPOS_VALIDACION:
        col_m = f"{campo}_muestra"
        col_p = f"{campo}_pred"

        y_true = [_norm_label(v) for v in merged[col_m]]
        y_pred = [_norm_label(v) for v in merged[col_p]]
        n = len(y_true)
        aciertos = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        accuracy = aciertos / n if n > 0 else 0.0

        labels = sorted(set(y_true) | set(y_pred))
        if n > 0 and len(labels) > 1:
            kappa = float(cohen_kappa_score(y_true, y_pred, labels=labels))
            cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
        elif n > 0:
            kappa = 1.0
            cm = [[n]]
        else:
            kappa = 0.0
            cm = []

        discrepancias: list[dict[str, Any]] = []
        for (_, row), t_val, p_val in zip(merged.iterrows(), y_true, y_pred):
            if t_val != p_val:
                discrepancias.append(
                    {
                        "ejecucion_id": row["ejecucion_id"],
                        "marca": row["marca"],
                        "posicion": None
                        if pd.isna(row.get("posicion_muestra"))
                        else int(row["posicion_muestra"]),
                        "esperado": t_val,
                        "predicho": p_val,
                        "fragmento": row.get("fragmento"),
                    }
                )

        report[campo] = {
            "accuracy": accuracy,
            "kappa": kappa,
            "n": n,
            "aciertos": aciertos,
            "labels": labels,
            "confusion_matrix": cm,
            "discrepancias": discrepancias,
        }

    return report
