"""Cálculo determinista del Score de Citación y tablas T1-T12 (F5)."""

import json
from pathlib import Path
import re
from typing import Any, Literal, Sequence
import pandas as pd

from geo.config import INTENCIONES, MOTORES, SCORE_WEIGHTS
from geo.schemas import Ejecucion, Marca

Ambito = Literal["espontanea", "asistida", "total", "apariciones", "ejecuciones"]

MAX_EVIDENCE_IDS_SERIALIZED: int = 50


def _truncate_ids(ids: Sequence[str], limit: int = MAX_EVIDENCE_IDS_SERIALIZED) -> list[str]:
    """Devuelve ids únicos manteniendo el orden y truncando a `limit` elementos."""
    seen: set[str] = set()
    out: list[str] = []
    for x in ids:
        s = str(x)
        if s not in seen:
            seen.add(s)
            out.append(s)
            if len(out) >= limit:
                break
    return out


def score(df: pd.DataFrame) -> dict[str, float | int]:
    """Calcula el Score de Citación (0-100) y sus 4 componentes sobre un DataFrame de evaluaciones.

    Fórmula (metodología, sección 7):
      tasa_aparicion = mean(aparece)
      aparicion      = 30 * tasa_aparicion
      posicion       = 20 * mean(peso_posicion) / 3
      fuerza         = 30 * max(mean(fuerza), 0) / 3
      fuente         = 20 * tasa_aparicion * mean(calidad_fuente | aparece==1)
      score          = aparicion + posicion + fuerza + fuente
    """
    n = int(len(df))
    if n == 0:
        return {
            "n": 0,
            "n_apariciones": 0,
            "tasa_aparicion": 0.0,
            "aparicion": 0.0,
            "posicion": 0.0,
            "fuerza": 0.0,
            "fuente": 0.0,
            "score": 0.0,
        }

    ap_series = df["aparece"].astype(float)
    n_ap = int(ap_series.sum())
    tasa_aparicion = float(ap_series.mean())

    if n_ap == 0:
        return {
            "n": n,
            "n_apariciones": 0,
            "tasa_aparicion": 0.0,
            "aparicion": 0.0,
            "posicion": 0.0,
            "fuerza": 0.0,
            "fuente": 0.0,
            "score": 0.0,
        }

    mean_peso_pos = float(df["peso_posicion"].astype(float).mean())
    mean_fuerza = float(df["fuerza"].astype(float).mean())

    present_df = df[df["aparece"] == 1]
    cal_series = present_df["calidad_fuente"].dropna().astype(float)
    mean_calidad_present = float(cal_series.mean()) if len(cal_series) > 0 else 0.2

    comp_aparicion = float(SCORE_WEIGHTS["aparicion"]) * tasa_aparicion
    comp_posicion = float(SCORE_WEIGHTS["posicion"]) * (mean_peso_pos / 3.0)
    comp_fuerza = float(SCORE_WEIGHTS["fuerza"]) * (max(mean_fuerza, 0.0) / 3.0)
    comp_fuente = float(SCORE_WEIGHTS["fuente"]) * tasa_aparicion * mean_calidad_present
    total_score = comp_aparicion + comp_posicion + comp_fuerza + comp_fuente

    return {
        "n": n,
        "n_apariciones": n_ap,
        "tasa_aparicion": tasa_aparicion,
        "aparicion": comp_aparicion,
        "posicion": comp_posicion,
        "fuerza": comp_fuerza,
        "fuente": comp_fuente,
        "score": total_score,
    }


def _enrich_evals(
    evals: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
) -> pd.DataFrame:
    """Une el DataFrame de evaluaciones con los metadatos de cada ejecución si aún no están presentes."""
    if isinstance(ejecuciones, pd.DataFrame):
        df_ej = ejecuciones
    else:
        df_ej = pd.DataFrame([e.model_dump() for e in ejecuciones])

    needed_cols = [
        "ejecucion_id",
        "prompt_id",
        "familia",
        "intencion",
        "instanciacion",
        "prompt_ejecutado",
        "motor",
        "repeticion",
        "ciudad",
        "espontanea",
        "fuentes",
    ]
    available_cols = [c for c in needed_cols if c in df_ej.columns]
    cols_to_merge = ["ejecucion_id"] + [
        c for c in available_cols if c != "ejecucion_id" and c not in evals.columns
    ]
    if len(cols_to_merge) > 1:
        return evals.merge(df_ej[cols_to_merge], on="ejecucion_id", how="left")
    return evals.copy()


def tabla(
    df: pd.DataFrame,
    by: list[str],
    ambito: Literal["espontanea", "asistida", "total"] = "espontanea",
) -> pd.DataFrame:
    """Agrupa evaluaciones por `by` en el ámbito indicado y calcula métricas y componentes del score."""
    work = df.copy()
    if "espontanea" in work.columns:
        if ambito == "espontanea":
            work = work[work["espontanea"] == True].copy()  # noqa: E712
        elif ambito == "asistida":
            work = work[work["espontanea"] == False].copy()  # noqa: E712

    if work.empty:
        return pd.DataFrame(
            columns=[
                *by,
                "ambito",
                "n",
                "n_apariciones",
                "tasa_aparicion",
                "pos_media",
                "fuerza_media",
                "fuerza_media_apariciones",
                "%recomendacion_activa",
                "%negativo",
                "%desconocimiento",
                "aparicion",
                "posicion",
                "fuerza",
                "fuente",
                "score",
                "evidencia_ids",
            ]
        )

    rows: list[dict[str, Any]] = []
    for keys, grp in work.groupby(by, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        key_dict = dict(zip(by, keys))

        sc = score(grp)
        n = int(sc["n"])
        present = grp[grp["aparece"] == 1]
        n_ap = int(len(present))

        pos_vals = present["posicion"].dropna().astype(float)
        pos_media = float(pos_vals.mean()) if len(pos_vals) > 0 else None

        fuerza_media = float(grp["fuerza"].astype(float).mean()) if n > 0 else 0.0
        fuerza_media_ap = (
            float(present["fuerza"].astype(float).mean()) if n_ap > 0 else 0.0
        )

        pct_rec_activa = (
            float((grp["tipo_mencion"] == "Recomendación activa").sum()) / n
            if n > 0
            else 0.0
        )
        pct_negativo = (
            float((grp["sentimiento"] == "negativo").sum()) / n if n > 0 else 0.0
        )
        pct_desconocimiento = (
            float(grp["desconocimiento"].astype(bool).sum()) / n if n > 0 else 0.0
        )

        ev_source = present if n_ap > 0 else grp
        ev_ids = _truncate_ids(ev_source["ejecucion_id"].astype(str).tolist())

        rows.append(
            {
                **key_dict,
                "ambito": ambito,
                "n": n,
                "n_apariciones": n_ap,
                "tasa_aparicion": float(sc["tasa_aparicion"]),
                "pos_media": pos_media,
                "fuerza_media": fuerza_media,
                "fuerza_media_apariciones": fuerza_media_ap,
                "%recomendacion_activa": pct_rec_activa,
                "%negativo": pct_negativo,
                "%desconocimiento": pct_desconocimiento,
                "aparicion": float(sc["aparicion"]),
                "posicion": float(sc["posicion"]),
                "fuerza": float(sc["fuerza"]),
                "fuente": float(sc["fuente"]),
                "score": float(sc["score"]),
                "evidencia_ids": ev_ids,
            }
        )

    out = pd.DataFrame(rows)
    out = out.sort_values(by="score", ascending=False).reset_index(drop=True)
    return out


def _extract_objections(fragmento: str | None) -> list[str]:
    """Extrae oraciones de objeción o advertencia ('Eso sí, ...' o quejas) de un fragmento."""
    if not fragmento:
        return []
    matches: list[str] = []
    for sent in re.split(r"(?<=[.!?])\s+|\n+", fragmento):
        s_clean = sent.strip()
        s_low = s_clean.lower()
        if any(
            kw in s_low
            for kw in (
                "eso sí",
                "eso si",
                "quejas",
                "listas de espera",
                "coste notablemente superior",
                "atención administrativa desigual",
                "seguimiento postoperatorio",
                "pocas opiniones",
                "agenda",
                "instalaciones",
            )
        ):
            matches.append(s_clean)
    return matches


def bundle(
    evals: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
    *,
    persist_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Genera las tablas obligatorias T1-T12 (siempre con columna `ambito` y `evidencia_ids`).

    Si `persist_dir` se especifica, guarda `tablas/*.parquet` y `metrics.json` con las cifras clave
    de la marca del brief.
    """
    if isinstance(ejecuciones, pd.DataFrame):
        df_ej = ejecuciones.copy()
    else:
        df_ej = pd.DataFrame([e.model_dump() for e in ejecuciones])

    full = _enrich_evals(evals, df_ej)
    marca_brief = next(
        (m.nombre for m in marcas if m.es_marca_brief), "Clínica Alborada Visión"
    )

    # ---------- T1: Ranking de marcas por score (espontánea y asistida separadas) ----------
    t1_esp = tabla(full, by=["marca"], ambito="espontanea")
    t1_esp["puesto"] = range(1, len(t1_esp) + 1)

    t1_asis = tabla(full, by=["marca"], ambito="asistida")
    t1_asis["puesto"] = range(1, len(t1_asis) + 1)

    t1 = pd.concat([t1_esp, t1_asis], ignore_index=True)

    # ---------- T2: Marca × motor (espontánea) ----------
    t2 = tabla(full, by=["marca", "motor"], ambito="espontanea")

    # ---------- T3: Marca × fase del embudo (espontánea; asistida aparte) ----------
    t3_esp = tabla(full, by=["marca", "intencion"], ambito="espontanea")
    t3_asis = tabla(full, by=["marca", "intencion"], ambito="asistida")
    order_map = {inten: idx for idx, inten in enumerate(INTENCIONES)}
    t3_esp["_ord"] = t3_esp["intencion"].map(order_map)
    t3_esp = t3_esp.sort_values(["marca", "_ord"]).drop(columns=["_ord"]).reset_index(drop=True)
    t3_asis["_ord"] = t3_asis["intencion"].map(order_map)
    t3_asis = t3_asis.sort_values(["marca", "_ord"]).drop(columns=["_ord"]).reset_index(drop=True)

    # ---------- T4: Marca × ciudad (espontánea, solo prompts 'ciudad') ----------
    full_ciudad = full[full["instanciacion"] == "ciudad"].copy()
    t4 = tabla(full_ciudad, by=["marca", "ciudad"], ambito="espontanea")

    # ---------- T5: Marca × familia de prompt (espontánea) ----------
    t5 = tabla(full, by=["marca", "familia"], ambito="espontanea")

    # ---------- T6: Perfil de fuentes por marca (% apariciones por tipo de fuente y calidad media) ----------
    ap_only = full[full["aparece"] == 1].copy()
    t6_rows: list[dict[str, Any]] = []
    for m_name, grp_m in ap_only.groupby("marca", sort=False):
        total_ap = len(grp_m)
        cal_media_marca = float(grp_m["calidad_fuente"].dropna().astype(float).mean()) if total_ap > 0 else 0.2
        for tf, grp_tf in grp_m.groupby("tipo_fuente", dropna=False, sort=False):
            tf_str = str(tf) if pd.notna(tf) else "Sin fuente"
            n_tf = len(grp_tf)
            t6_rows.append(
                {
                    "marca": m_name,
                    "tipo_fuente": tf_str,
                    "ambito": "apariciones",
                    "n_apariciones_marca": total_ap,
                    "n": n_tf,
                    "pct_apariciones": n_tf / total_ap if total_ap > 0 else 0.0,
                    "calidad_media_tipo": float(grp_tf["calidad_fuente"].dropna().astype(float).mean())
                    if n_tf > 0
                    else 0.2,
                    "calidad_media_marca": cal_media_marca,
                    "evidencia_ids": _truncate_ids(grp_tf["ejecucion_id"].astype(str).tolist()),
                }
            )
    t6 = pd.DataFrame(t6_rows)

    # ---------- T7: Dominios más citados donde aparece la marca del brief vs el líder ----------
    lider_nombre = (
        str(t1_esp.iloc[0]["marca"]) if not t1_esp.empty else "Grupo Hospitalario Valdecruz"
    )
    t7_rows: list[dict[str, Any]] = []
    for target_brand, etiqueta in [(marca_brief, "marca_brief"), (lider_nombre, "lider")]:
        ej_ids_brand = set(
            full.loc[
                (full["espontanea"] == True)  # noqa: E712
                & (full["marca"] == target_brand)
                & (full["aparece"] == 1),
                "ejecucion_id",
            ].astype(str)
        )
        sub_ej = df_ej[df_ej["ejecucion_id"].isin(ej_ids_brand)]
        n_ej_brand = len(sub_ej)
        dom_to_ejs: dict[str, list[str]] = {}
        for _, r_ej in sub_ej.iterrows():
            for dom in r_ej["fuentes"]:
                dom_to_ejs.setdefault(dom, []).append(str(r_ej["ejecucion_id"]))
        for dom, ej_list in sorted(dom_to_ejs.items(), key=lambda x: len(x[1]), reverse=True):
            t7_rows.append(
                {
                    "marca": target_brand,
                    "rol_comparado": etiqueta,
                    "dominio": dom,
                    "ambito": "ejecuciones",
                    "n": len(ej_list),
                    "n_ejecuciones_marca": n_ej_brand,
                    "tasa_citacion_en_apariciones": len(ej_list) / n_ej_brand if n_ej_brand > 0 else 0.0,
                    "evidencia_ids": _truncate_ids(ej_list),
                }
            )
    t7 = pd.DataFrame(t7_rows)

    # ---------- T8: Duelos 1 a 1 (prompts 'par') por par y motor ----------
    par_df = full[full["instanciacion"] == "par"].copy()
    duel_records: list[dict[str, Any]] = []
    for ej_id, grp_ej in par_df.groupby("ejecucion_id", sort=False):
        if len(grp_ej) < 2:
            continue
        grp_sorted = grp_ej.sort_values("marca")
        r_a = grp_sorted.iloc[0]
        r_b = grp_sorted.iloc[1]
        par_label = f"{r_a['marca']} vs {r_b['marca']}"
        motor = str(r_a["motor"])

        fa, fb = int(r_a["fuerza"]), int(r_b["fuerza"])
        pa = 99 if pd.isna(r_a["posicion"]) else int(r_a["posicion"])
        pb = 99 if pd.isna(r_b["posicion"]) else int(r_b["posicion"])

        if fa > fb or (fa == fb and pa < pb):
            ganador = str(r_a["marca"])
        elif fb > fa or (fb == fa and pb < pa):
            ganador = str(r_b["marca"])
        else:
            ganador = "Empate"

        duel_records.append(
            {
                "ejecucion_id": str(ej_id),
                "par": par_label,
                "marca_a": str(r_a["marca"]),
                "marca_b": str(r_b["marca"]),
                "motor": motor,
                "ganador": ganador,
            }
        )

    df_duels = pd.DataFrame(duel_records)
    t8_rows: list[dict[str, Any]] = []
    if not df_duels.empty:
        for (par_label, motor), grp_d in df_duels.groupby(["par", "motor"], sort=False):
            m_a = str(grp_d.iloc[0]["marca_a"])
            m_b = str(grp_d.iloc[0]["marca_b"])
            n_d = len(grp_d)
            wins_a = int((grp_d["ganador"] == m_a).sum())
            wins_b = int((grp_d["ganador"] == m_b).sum())
            ties = int((grp_d["ganador"] == "Empate").sum())
            if wins_a > wins_b:
                ganador_global = m_a
            elif wins_b > wins_a:
                ganador_global = m_b
            else:
                ganador_global = "Empate"
            t8_rows.append(
                {
                    "par": par_label,
                    "marca_a": m_a,
                    "marca_b": m_b,
                    "motor": motor,
                    "ambito": "asistida",
                    "n": n_d,
                    "victorias_a": wins_a,
                    "victorias_b": wins_b,
                    "empates": ties,
                    "ganador": ganador_global,
                    "evidencia_ids": _truncate_ids(grp_d["ejecucion_id"].tolist()),
                }
            )
    t8 = pd.DataFrame(t8_rows)

    # ---------- T9: Calidad de la mención asistida y objeciones recurrentes ----------
    asis_df = full[full["espontanea"] == False].copy()  # noqa: E712
    t9_rows: list[dict[str, Any]] = []
    for m_name, grp_m in asis_df.groupby("marca", sort=False):
        n_m = len(grp_m)
        present_m = grp_m[grp_m["aparece"] == 1]
        n_ap = len(present_m)
        neg_rows = grp_m[grp_m["sentimiento"] == "negativo"]
        obj_counts: dict[str, int] = {}
        for frag in neg_rows["fragmento"]:
            for obj in _extract_objections(None if pd.isna(frag) else str(frag)):
                obj_counts[obj] = obj_counts.get(obj, 0) + 1
        top_objs = [
            f"{txt} ({cnt})"
            for txt, cnt in sorted(obj_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
        ev_source = neg_rows if len(neg_rows) > 0 else present_m
        t9_rows.append(
            {
                "marca": m_name,
                "ambito": "asistida",
                "n": n_m,
                "n_apariciones": n_ap,
                "tasa_aparicion": n_ap / n_m if n_m > 0 else 0.0,
                "fuerza_media": float(present_m["fuerza"].astype(float).mean())
                if n_ap > 0
                else 0.0,
                "%recomendacion_activa": float(
                    (grp_m["tipo_mencion"] == "Recomendación activa").sum()
                )
                / n_m
                if n_m > 0
                else 0.0,
                "%negativo": float(len(neg_rows)) / n_m if n_m > 0 else 0.0,
                "%desconocimiento": float(grp_m["desconocimiento"].astype(bool).sum()) / n_m
                if n_m > 0
                else 0.0,
                "objeciones_recurrentes": " | ".join(top_objs) if top_objs else "Sin objeciones recurrentes",
                "evidencia_ids": _truncate_ids(ev_source["ejecucion_id"].astype(str).tolist()),
            }
        )
    t9 = pd.DataFrame(t9_rows).sort_values("fuerza_media", ascending=False).reset_index(drop=True)

    # ---------- T10: Consistencia entre repeticiones (espontánea) ----------
    esp_df = full[full["espontanea"] == True].copy()  # noqa: E712
    rep_groups: list[dict[str, Any]] = []
    for (p_exec, motor, m_name), grp_r in esp_df.groupby(
        ["prompt_ejecutado", "motor", "marca"], sort=False
    ):
        n_reps_ap = int(grp_r["aparece"].sum())
        if n_reps_ap == 3:
            estado = "consolidada"
        elif n_reps_ap in (1, 2):
            estado = "azar"
        else:
            estado = "ausente"
        rep_groups.append(
            {
                "prompt_ejecutado": p_exec,
                "motor": motor,
                "marca": m_name,
                "repeticiones_con_aparicion": n_reps_ap,
                "estado": estado,
                "ejecucion_ids": grp_r["ejecucion_id"].astype(str).tolist(),
            }
        )
    df_reps = pd.DataFrame(rep_groups)
    t10_rows: list[dict[str, Any]] = []
    for m_name, grp_m in df_reps.groupby("marca", sort=False):
        n_series = len(grp_m)
        n_cons = int((grp_m["estado"] == "consolidada").sum())
        n_azar = int((grp_m["estado"] == "azar").sum())
        n_aus = int((grp_m["estado"] == "ausente").sum())
        azar_ejs: list[str] = []
        for ejs in grp_m.loc[grp_m["estado"] == "azar", "ejecucion_ids"]:
            azar_ejs.extend(ejs)
        t10_rows.append(
            {
                "marca": m_name,
                "ambito": "espontanea",
                "n": n_series,
                "n_consolidada": n_cons,
                "n_azar": n_azar,
                "n_ausente": n_aus,
                "%consolidada": n_cons / n_series if n_series > 0 else 0.0,
                "%azar": n_azar / n_series if n_series > 0 else 0.0,
                "%ausente": n_aus / n_series if n_series > 0 else 0.0,
                "evidencia_ids": _truncate_ids(azar_ejs),
            }
        )
    t10 = pd.DataFrame(t10_rows).sort_values("%consolidada", ascending=False).reset_index(drop=True)

    # ---------- T11: Embudo de la marca del brief frente al líder y a la media de competidores ----------
    t11_rows: list[dict[str, Any]] = []
    for inten in INTENCIONES:
        sub_i = t3_esp[t3_esp["intencion"] == inten]
        row_b = sub_i[sub_i["marca"] == marca_brief]
        row_l = sub_i[sub_i["marca"] == lider_nombre]
        comp_i = sub_i[sub_i["marca"] != marca_brief]

        ap_b = float(row_b.iloc[0]["tasa_aparicion"]) if not row_b.empty else 0.0
        sc_b = float(row_b.iloc[0]["score"]) if not row_b.empty else 0.0
        f_b = float(row_b.iloc[0]["fuerza_media"]) if not row_b.empty else 0.0
        n_b = int(row_b.iloc[0]["n"]) if not row_b.empty else 0
        ev_b = list(row_b.iloc[0]["evidencia_ids"]) if not row_b.empty else []

        ap_l = float(row_l.iloc[0]["tasa_aparicion"]) if not row_l.empty else 0.0
        sc_l = float(row_l.iloc[0]["score"]) if not row_l.empty else 0.0

        ap_comp = float(comp_i["tasa_aparicion"].mean()) if not comp_i.empty else 0.0
        sc_comp = float(comp_i["score"].mean()) if not comp_i.empty else 0.0

        t11_rows.append(
            {
                "intencion": inten,
                "ambito": "espontanea",
                "marca_brief": marca_brief,
                "lider": lider_nombre,
                "n": n_b,
                "tasa_aparicion_marca": ap_b,
                "tasa_aparicion_lider": ap_l,
                "tasa_aparicion_media_competidores": ap_comp,
                "brecha_aparicion_vs_lider_pp": (ap_b - ap_l) * 100.0,
                "score_marca": sc_b,
                "score_lider": sc_l,
                "score_media_competidores": sc_comp,
                "fuerza_media_marca": f_b,
                "evidencia_ids": _truncate_ids(ev_b),
            }
        )
    t11 = pd.DataFrame(t11_rows)

    # ---------- T12: Motor × fuente: % de ejecuciones sin búsqueda por motor ----------
    t12_rows: list[dict[str, Any]] = []
    for motor in MOTORES:
        sub_m = df_ej[df_ej["motor"] == motor]
        n_m = len(sub_m)
        no_search = sub_m[sub_m["fuentes"].apply(lambda x: len(x) == 0)]
        n_no = len(no_search)
        t12_rows.append(
            {
                "motor": motor,
                "ambito": "ejecuciones",
                "n": n_m,
                "n_sin_busqueda": n_no,
                "n_con_busqueda": n_m - n_no,
                "%sin_busqueda": n_no / n_m if n_m > 0 else 0.0,
                "evidencia_ids": _truncate_ids(no_search["ejecucion_id"].astype(str).tolist()),
            }
        )
    t12 = pd.DataFrame(t12_rows)

    tablas: dict[str, pd.DataFrame] = {
        "T1": t1,
        "T1_espontanea": t1_esp,
        "T1_asistida": t1_asis,
        "T2": t2,
        "T3": t3_esp,
        "T3_asistida": t3_asis,
        "T4": t4,
        "T5": t5,
        "T6": t6,
        "T7": t7,
        "T8": t8,
        "T9": t9,
        "T10": t10,
        "T11": t11,
        "T12": t12,
    }

    if persist_dir is not None:
        tablas_dir = persist_dir / "tablas"
        tablas_dir.mkdir(parents=True, exist_ok=True)
        for name, df_tab in tablas.items():
            df_tab.to_parquet(tablas_dir / f"{name}.parquet", index=False)

        summary = build_brand_summary_metrics(tablas, marca_brief=marca_brief)
        (persist_dir / "metrics.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return tablas


def build_brand_summary_metrics(
    tablas: dict[str, pd.DataFrame],
    marca_brief: str = "Clínica Alborada Visión",
) -> dict[str, Any]:
    """Construye el diccionario `metrics.json` con las cifras clave y trazables de la marca del brief."""
    t1_esp = tablas["T1_espontanea"]
    t1_asis = tablas["T1_asistida"]
    t2 = tablas["T2"]
    t3 = tablas["T3"]
    t4 = tablas["T4"]
    t9 = tablas["T9"]
    t10 = tablas["T10"]

    row_esp = t1_esp[t1_esp["marca"] == marca_brief].iloc[0].to_dict() if not t1_esp.empty else {}
    row_asis = t1_asis[t1_asis["marca"] == marca_brief].iloc[0].to_dict() if not t1_asis.empty else {}
    row_lider = t1_esp.iloc[0].to_dict() if not t1_esp.empty else {}
    row_t9 = t9[t9["marca"] == marca_brief].iloc[0].to_dict() if not t9.empty else {}
    row_t10 = t10[t10["marca"] == marca_brief].iloc[0].to_dict() if not t10.empty else {}

    por_motor = {
        str(r["motor"]): {
            "tasa_aparicion": round(float(r["tasa_aparicion"]), 4),
            "score": round(float(r["score"]), 2),
            "n": int(r["n"]),
        }
        for _, r in t2[t2["marca"] == marca_brief].iterrows()
    }
    por_ciudad = {
        str(r["ciudad"]): {
            "tasa_aparicion": round(float(r["tasa_aparicion"]), 4),
            "score": round(float(r["score"]), 2),
            "n": int(r["n"]),
        }
        for _, r in t4[t4["marca"] == marca_brief].iterrows()
    }
    por_embudo = {
        str(r["intencion"]): {
            "tasa_aparicion": round(float(r["tasa_aparicion"]), 4),
            "score": round(float(r["score"]), 2),
            "fuerza_media": round(float(r["fuerza_media"]), 3),
            "n": int(r["n"]),
        }
        for _, r in t3[t3["marca"] == marca_brief].iterrows()
    }

    return {
        "marca_brief": marca_brief,
        "lider_espontaneo": str(row_lider.get("marca", "")),
        "puesto_espontaneo": int(row_esp.get("puesto", 0)),
        "total_marcas": int(len(t1_esp)),
        "score_espontaneo": round(float(row_esp.get("score", 0.0)), 2),
        "tasa_aparicion_espontanea": round(float(row_esp.get("tasa_aparicion", 0.0)), 4),
        "pct_recomendacion_activa_espontanea": round(
            float(row_esp.get("%recomendacion_activa", 0.0)), 4
        ),
        "score_lider_espontaneo": round(float(row_lider.get("score", 0.0)), 2),
        "tasa_aparicion_lider_espontanea": round(
            float(row_lider.get("tasa_aparicion", 0.0)), 4
        ),
        "score_asistido": round(float(row_asis.get("score", 0.0)), 2),
        "tasa_aparicion_asistida": round(float(row_asis.get("tasa_aparicion", 0.0)), 4),
        "fuerza_media_asistida": round(float(row_t9.get("fuerza_media", 0.0)), 3),
        "pct_negativo_asistida": round(float(row_t9.get("%negativo", 0.0)), 4),
        "pct_desconocimiento_asistida": round(
            float(row_t9.get("%desconocimiento", 0.0)), 4
        ),
        "pct_azar_espontanea": round(float(row_t10.get("%azar", 0.0)), 4),
        "pct_consolidada_espontanea": round(float(row_t10.get("%consolidada", 0.0)), 4),
        "por_motor_espontanea": por_motor,
        "por_ciudad_espontanea": por_ciudad,
        "por_embudo_espontanea": por_embudo,
    }
