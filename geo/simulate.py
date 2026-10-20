"""Simulador what-if del Score de Citación (F14)."""

from typing import Any, Sequence
import numpy as np
import pandas as pd

from geo.loader import load_ejecuciones
from geo.metrics import _enrich_evals, score
from geo.schemas import Ejecucion, Objetivo, Plan

DISCLAIMER_SIMULADOR: str = "Escenario hipotético, no una predicción."


def get_brand_baseline_params(
    evals: pd.DataFrame,
    marca: str,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion] | None = None,
) -> dict[str, Any]:
    """Extrae los parámetros espontáneos actuales de `marca` para inicializar los controles del simulador."""
    df_ej = ejecuciones if ejecuciones is not None else load_ejecuciones()
    full = _enrich_evals(evals, df_ej)
    esp = full[(full["espontanea"] == True) & (full["marca"] == marca)].copy()  # noqa: E712

    if esp.empty:
        return {
            "n_espontanea": 0,
            "tasa_aparicion": 0.0,
            "aparicion_por_ciudad": {"Madrid": 0.0, "Barcelona": 0.0, "Genérico": 0.0},
            "pesos_ciudad": {"Madrid": 0.1, "Barcelona": 0.1, "Genérico": 0.8},
            "aparicion_por_motor": {},
            "pesos_motor": {},
            "fuerza_presentes": 0.0,
            "peso_posicion_presentes": 0.0,
            "calidad_fuente_presentes": 0.2,
            "pct_fuentes_calidad": 0.0,
            "mean_high_quality": 0.95,
            "mean_low_quality": 0.55,
        }

    n_total = len(esp)
    tasa_ap = float(esp["aparece"].astype(float).mean())

    esp["ciudad_norm"] = esp["ciudad"].fillna("Genérico").replace("", "Genérico")
    ap_ciudad: dict[str, float] = {}
    pesos_ciudad: dict[str, float] = {}
    for c_name, grp in esp.groupby("ciudad_norm"):
        ap_ciudad[str(c_name)] = float(grp["aparece"].astype(float).mean())
        pesos_ciudad[str(c_name)] = float(len(grp) / n_total)

    ap_motor: dict[str, float] = {}
    pesos_motor: dict[str, float] = {}
    for m_name, grp in esp.groupby("motor"):
        ap_motor[str(m_name)] = float(grp["aparece"].astype(float).mean())
        pesos_motor[str(m_name)] = float(len(grp) / n_total)

    pres = esp[esp["aparece"] == 1]
    if len(pres) > 0:
        fuerza_pres = float(pres["fuerza"].astype(float).mean())
        peso_pos_pres = float(pres["peso_posicion"].astype(float).mean())
        cal_series = pres["calidad_fuente"].dropna().astype(float)
        cal_pres = float(cal_series.mean()) if len(cal_series) > 0 else 0.2

        high_mask = cal_series >= 0.9
        pct_high = float(high_mask.mean()) if len(cal_series) > 0 else 0.0
        mean_high = float(cal_series[high_mask].mean()) if high_mask.any() else 0.95
        mean_low = float(cal_series[~high_mask].mean()) if (~high_mask).any() else 0.55
    else:
        fuerza_pres = 1.5
        peso_pos_pres = 1.8
        cal_pres = 0.6
        pct_high = 0.25
        mean_high = 0.95
        mean_low = 0.55

    return {
        "n_espontanea": n_total,
        "tasa_aparicion": tasa_ap,
        "aparicion_por_ciudad": ap_ciudad,
        "pesos_ciudad": pesos_ciudad,
        "aparicion_por_motor": ap_motor,
        "pesos_motor": pesos_motor,
        "fuerza_presentes": fuerza_pres,
        "peso_posicion_presentes": peso_pos_pres,
        "calidad_fuente_presentes": cal_pres,
        "pct_fuentes_calidad": pct_high,
        "mean_high_quality": mean_high,
        "mean_low_quality": mean_low,
    }


def simulate(
    evals: pd.DataFrame,
    marca: str,
    cambios: dict[str, Any] | None = None,
    *,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion] | None = None,
) -> dict[str, Any]:
    """Simula el impacto en el Score de Citación espontáneo y el puesto en el ranking aplicando `cambios`.

    Reutiliza `geo.metrics.score` sobre el DataFrame espontáneo de la marca.
    Parámetros admitidos en `cambios`:
      - `aparicion_por_ciudad`: dict[str, float] (ej. {"Madrid": 0.60, "Barcelona": 0.35})
      - `aparicion_por_motor`: dict[str, float] (ej. {"ChatGPT": 0.35, "Claude": 0.30, ...})
      - `tasa_aparicion_objetivo`: float (0..1, opcional; si se indica, prevalece sobre deltas parciales)
      - `fuerza_media_objetivo`: float (0..3, fuerza media en apariciones)
      - `peso_posicion_objetivo`: float (1..3, peso de posición medio en apariciones)
      - `pct_fuentes_calidad`: float (0..1, proporción de apariciones con fuentes de calidad >= 0.9)
      - `calidad_fuente_objetivo`: float (0.2..1.0, calidad media de fuente directa opcional)
    """
    df_ej = ejecuciones if ejecuciones is not None else load_ejecuciones()
    full = _enrich_evals(evals, df_ej)
    esp_all = full[full["espontanea"] == True].copy()  # noqa: E712

    # 1. Calcular scores y ranking actuales de todas las marcas en espontáneo
    scores_actuales: dict[str, dict[str, float | int]] = {}
    for m_name, grp in esp_all.groupby("marca"):
        scores_actuales[str(m_name)] = score(grp)

    brand_df_actual = esp_all[esp_all["marca"] == marca].copy()
    sc_actual = scores_actuales.get(marca, score(brand_df_actual))
    base = get_brand_baseline_params(full, marca, ejecuciones=df_ej)

    cambios_dict = cambios or {}

    # 2. Calcular tasa de aparición objetivo a partir de los controles
    tasa_ap_base = float(base["tasa_aparicion"])
    delta_ciudad = 0.0
    if "aparicion_por_ciudad" in cambios_dict and cambios_dict["aparicion_por_ciudad"]:
        for c_name, target_val in cambios_dict["aparicion_por_ciudad"].items():
            actual_c = base["aparicion_por_ciudad"].get(c_name, tasa_ap_base)
            weight_c = base["pesos_ciudad"].get(c_name, 0.0)
            delta_ciudad += (float(target_val) - actual_c) * weight_c

    delta_motor = 0.0
    if "aparicion_por_motor" in cambios_dict and cambios_dict["aparicion_por_motor"]:
        for m_name, target_val in cambios_dict["aparicion_por_motor"].items():
            actual_m = base["aparicion_por_motor"].get(m_name, tasa_ap_base)
            weight_m = base["pesos_motor"].get(m_name, 0.0)
            delta_motor += (float(target_val) - actual_m) * weight_m

    if "tasa_aparicion_objetivo" in cambios_dict and cambios_dict["tasa_aparicion_objetivo"] is not None:
        target_tasa_ap = float(np.clip(float(cambios_dict["tasa_aparicion_objetivo"]), 0.0, 1.0))
    else:
        target_tasa_ap = float(np.clip(tasa_ap_base + delta_ciudad + delta_motor, 0.0, 1.0))

    # 3. Fuerza media y peso de posición en apariciones
    fuerza_pres_base = float(base["fuerza_presentes"])
    if "fuerza_media_objetivo" in cambios_dict and cambios_dict["fuerza_media_objetivo"] is not None:
        target_fuerza_pres = float(np.clip(float(cambios_dict["fuerza_media_objetivo"]), 0.0, 3.0))
    else:
        target_fuerza_pres = fuerza_pres_base

    peso_pos_base = float(base["peso_posicion_presentes"])
    if "peso_posicion_objetivo" in cambios_dict and cambios_dict["peso_posicion_objetivo"] is not None:
        target_peso_pos_pres = float(np.clip(float(cambios_dict["peso_posicion_objetivo"]), 1.0, 3.0))
    else:
        target_peso_pos_pres = peso_pos_base

    # 4. Calidad de fuente objetivo
    pct_high_base = float(base["pct_fuentes_calidad"])
    cal_pres_base = float(base["calidad_fuente_presentes"])
    if "calidad_fuente_objetivo" in cambios_dict and cambios_dict["calidad_fuente_objetivo"] is not None:
        target_cal_pres = float(np.clip(float(cambios_dict["calidad_fuente_objetivo"]), 0.2, 1.0))
        target_pct_high = pct_high_base
    elif "pct_fuentes_calidad" in cambios_dict and cambios_dict["pct_fuentes_calidad"] is not None:
        target_pct_high = float(np.clip(float(cambios_dict["pct_fuentes_calidad"]), 0.0, 1.0))
        if abs(target_pct_high - pct_high_base) < 1e-9:
            target_cal_pres = cal_pres_base
        else:
            mean_h = float(base["mean_high_quality"])
            mean_l = float(base["mean_low_quality"])
            target_cal_pres = float(np.clip(target_pct_high * mean_h + (1.0 - target_pct_high) * mean_l, 0.2, 1.0))
    else:
        target_pct_high = pct_high_base
        target_cal_pres = cal_pres_base

    # 5. Si no hay cambios efectivos, usar el DataFrame original sin tocar para identidad exacta
    no_effective_change = (
        abs(target_tasa_ap - tasa_ap_base) < 1e-9
        and abs(target_fuerza_pres - fuerza_pres_base) < 1e-9
        and abs(target_peso_pos_pres - peso_pos_base) < 1e-9
        and abs(target_cal_pres - cal_pres_base) < 1e-9
    )

    if no_effective_change or brand_df_actual.empty:
        brand_df_sim = brand_df_actual.copy()
    else:
        brand_df_sim = brand_df_actual.copy().reset_index(drop=True)
        n_rows = len(brand_df_sim)
        target_ap_sum = target_tasa_ap * n_rows

        ap_vals = np.zeros(n_rows, dtype=float)
        if target_ap_sum > 0:
            k_ones = min(n_rows, max(1, int(np.floor(target_ap_sum))))
            if target_ap_sum < 1.0:
                # Mantener al menos 1 fila con aparece == 1 si target_ap_sum >= 1; si es < 1, escalar
                ap_vals[0] = 1.0
                if n_rows > 1:
                    ap_vals[1] = target_ap_sum - 1.0
            else:
                ap_vals[:k_ones] = 1.0
                rem = target_ap_sum - k_ones
                if rem > 1e-9 and k_ones < n_rows:
                    ap_vals[k_ones] = rem

        brand_df_sim["aparece"] = ap_vals
        brand_df_sim["peso_posicion"] = target_tasa_ap * target_peso_pos_pres
        brand_df_sim["fuerza"] = target_tasa_ap * target_fuerza_pres
        brand_df_sim["calidad_fuente"] = target_cal_pres

    sc_sim = score(brand_df_sim)

    # 6. Construir tabla de ranking espontáneo actual vs simulado
    ranking_rows: list[dict[str, Any]] = []
    for m_name, sc_m in scores_actuales.items():
        sc_act_m = float(sc_m["score"])
        sc_sim_m = float(sc_sim["score"]) if m_name == marca else sc_act_m
        ranking_rows.append(
            {
                "marca": m_name,
                "score_actual": round(sc_act_m, 2),
                "score_simulado": round(sc_sim_m, 2),
            }
        )

    df_rank_act = pd.DataFrame(ranking_rows).sort_values(
        by=["score_actual", "marca"], ascending=[False, True]
    ).reset_index(drop=True)
    df_rank_act["puesto_actual"] = df_rank_act.index + 1

    df_rank_sim = df_rank_act.sort_values(
        by=["score_simulado", "marca"], ascending=[False, True]
    ).reset_index(drop=True)
    df_rank_sim["puesto_simulado"] = df_rank_sim.index + 1

    puesto_actual = int(
        df_rank_act.loc[df_rank_act["marca"] == marca, "puesto_actual"].iloc[0]
    )
    puesto_simulado = int(
        df_rank_sim.loc[df_rank_sim["marca"] == marca, "puesto_simulado"].iloc[0]
    )

    score_actual_val = round(float(sc_actual["score"]), 2)
    score_sim_val = round(float(sc_sim["score"]), 2)

    return {
        "marca": marca,
        "score_actual": score_actual_val,
        "score_simulado": score_sim_val,
        "delta_score": round(score_sim_val - score_actual_val, 2),
        "puesto_actual": puesto_actual,
        "puesto_simulado": puesto_simulado,
        "delta_puesto": int(puesto_actual - puesto_simulado),
        "tasa_aparicion_actual": round(tasa_ap_base, 4),
        "tasa_aparicion_simulada": round(target_tasa_ap, 4),
        "fuerza_presentes_actual": round(fuerza_pres_base, 4),
        "fuerza_presentes_simulada": round(target_fuerza_pres, 4),
        "pct_fuentes_calidad_actual": round(pct_high_base, 4),
        "pct_fuentes_calidad_simulado": round(target_pct_high, 4),
        "componentes": {
            "actual": {
                "aparicion": round(float(sc_actual["aparicion"]), 2),
                "posicion": round(float(sc_actual["posicion"]), 2),
                "fuerza": round(float(sc_actual["fuerza"]), 2),
                "fuente": round(float(sc_actual["fuente"]), 2),
                "score": score_actual_val,
            },
            "simulado": {
                "aparicion": round(float(sc_sim["aparicion"]), 2),
                "posicion": round(float(sc_sim["posicion"]), 2),
                "fuerza": round(float(sc_sim["fuerza"]), 2),
                "fuente": round(float(sc_sim["fuente"]), 2),
                "score": score_sim_val,
            },
        },
        "ranking_simulado": df_rank_sim[
            ["puesto_simulado", "puesto_actual", "marca", "score_actual", "score_simulado"]
        ],
        "parametros_base": base,
        "aviso": DISCLAIMER_SIMULADOR,
    }


def apply_simulation_to_plan_objectives(plan: Plan, sim_result: dict[str, Any]) -> Plan:
    """Incorpora el escenario simulado como `Objetivo` estructurado en `plan.objetivos` (botón 'Usar como objetivo')."""
    sc_act = float(sim_result["score_actual"])
    sc_sim = float(sim_result["score_simulado"])
    p_act = int(sim_result["puesto_actual"])
    p_sim = int(sim_result["puesto_simulado"])
    ap_sim = round(float(sim_result["tasa_aparicion_simulada"]) * 100.0, 1)

    kpi_label = (
        f"Meta what-if ({DISCLAIMER_SIMULADOR}): Score espontáneo "
        f"(puesto {p_act}º → {p_sim}º, aparición {ap_sim:.1f} %)"
    )
    obj_min = round(min(sc_act, sc_sim) if sc_sim <= sc_act else max(sc_act, sc_sim * 0.95), 2)
    obj_max = round(max(sc_sim, obj_min), 2)

    nuevo_obj = Objetivo(
        kpi=kpi_label,
        valor_actual=sc_act,
        valor_objetivo_min=obj_min,
        valor_objetivo_max=obj_max,
        plazo_meses=12,
        hallazgos=["H1", "H3", "H6"],
    )

    cleaned_objs = [
        o for o in plan.objetivos if not o.kpi.startswith("Meta what-if")
    ]
    cleaned_objs.append(nuevo_obj)
    return plan.model_copy(update={"objetivos": cleaned_objs})
