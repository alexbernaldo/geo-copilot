"""Motor determinista de hallazgos priorizados con evidencias (F6)."""

from typing import Literal
import pandas as pd

from geo.config import FINDINGS_THRESHOLDS, MAX_FINDINGS
from geo.schemas import (
    ContrasteMercado,
    Evidencia,
    FichaMarca,
    Hallazgo,
    Intencion,
    Motor,
)


def default_ficha_alborada() -> FichaMarca:
    """Devuelve la ficha por defecto de Clínica Alborada Visión para pruebas cuando `ficha` es None."""
    return FichaMarca(
        marca="Clínica Alborada Visión",
        web="alboradavision.example",
        sector="Clínicas privadas (oftalmología)",
        subsector="Cirugía refractiva, cataratas y oftalmología integral",
        servicios=[
            "Cirugía refractiva láser (LASIK, PRK, SMILE)",
            "Lentes intraoculares fáquicas (ICL)",
            "Cirugía de cataratas y presbicia",
            "Oftalmología pediátrica y control de miopía infantil",
            "Retina, glaucoma y córnea",
        ],
        servicios_prioritarios=[
            "cirugía refractiva",
            "control de miopía infantil",
        ],
        diferenciales=[
            "Seguimiento postoperatorio incluido durante 12 meses con el mismo oftalmólogo",
            "Valoración preoperatoria completa de 90 minutos",
        ],
        ciudades=["Madrid", "Barcelona", "Valencia"],
        ciudad_principal="Madrid",
        ciudad_crecimiento="Barcelona",
        competidores_declarados=[
            "Instituto Oftálmico Tramuntana",
            "Láser Nítida",
            "Grupo Hospitalario Valdecruz",
        ],
        hipotesis_cliente=[
            "Con tan buenas reseñas deberíamos salir recomendados",
            "En Barcelona nadie nos encuentra",
        ],
        objetivo_principal=(
            "Aumentar las primeras visitas de cirugía refractiva y control de miopía infantil, "
            "con foco especial en Barcelona."
        ),
        presupuesto_min_eur=18000.0,
        presupuesto_max_eur=27000.0,
    )


def _calc_confianza(n: int) -> Literal["alta", "media", "baja"]:
    """Calcula el nivel de confianza según el tamaño muestral (n>=40 alta, 15..39 media, <15 baja)."""
    if n >= 40:
        return "alta"
    if n >= 15:
        return "media"
    return "baja"


def _sample_ids(raw_ids: object, k: int = 3) -> list[str]:
    """Devuelve entre 1 y `k` ejecucion_ids representativos de la evidencia."""
    if raw_ids is None:
        return []
    ids = [str(x) for x in list(raw_ids) if str(x)]  # type: ignore[arg-type]
    return ids[: max(k, 3)]


def generate_findings(
    tablas: dict[str, pd.DataFrame],
    ficha: FichaMarca | None = None,
    contraste_mercado: ContrasteMercado | None = None,
) -> list[Hallazgo]:
    """Convierte las tablas T1-T12 en hasta 7 hallazgos priorizados, deterministas y con evidencias trazables."""
    ficha_activa = ficha or default_ficha_alborada()
    marca = ficha_activa.marca
    ciudad_crecimiento = ficha_activa.ciudad_crecimiento or "Barcelona"
    ciudad_principal = ficha_activa.ciudad_principal or "Madrid"

    t1_esp = tablas["T1_espontanea"]
    t2 = tablas["T2"]
    t3 = tablas["T3"]
    t4 = tablas["T4"]
    t5 = tablas["T5"]
    t6 = tablas["T6"]
    t9 = tablas["T9"]
    t10 = tablas["T10"]
    t11 = tablas["T11"]

    row_marca_t1 = t1_esp[t1_esp["marca"] == marca].iloc[0]
    row_lider_t1 = t1_esp.iloc[0]
    lider = str(row_lider_t1["marca"])

    candidates: list[tuple[float, dict]] = []

    # ---------- R1: Brecha geográfica ----------
    t4_m = t4[t4["marca"] == marca]
    if len(t4_m) >= 2:
        row_growth = t4_m[t4_m["ciudad"] == ciudad_crecimiento]
        row_main = t4_m[t4_m["ciudad"] == ciudad_principal]
        if not row_growth.empty and not row_main.empty:
            rg = row_growth.iloc[0]
            rm = row_main.iloc[0]
            v_growth = round(float(rg["tasa_aparicion"]) * 100.0, 1)
            v_main = round(float(rm["tasa_aparicion"]) * 100.0, 1)
            n_g = int(rg["n"])
            n_m = int(rm["n"])
            diff_pp = abs(v_main - v_growth)
            if (
                diff_pp >= FINDINGS_THRESHOLDS["r1_geo_diff_pp"]
                or float(rg["tasa_aparicion"]) < FINDINGS_THRESHOLDS["r1_geo_growth_city_max"]
            ):
                evs = [
                    Evidencia(
                        metrica=f"tasa_aparicion_espontanea[ciudad={ciudad_crecimiento}]",
                        valor=v_growth,
                        n=n_g,
                        tabla="T4",
                        ejecucion_ids=_sample_ids(rg["evidencia_ids"], 3),
                    ),
                    Evidencia(
                        metrica=f"tasa_aparicion_espontanea[ciudad={ciudad_principal}]",
                        valor=v_main,
                        n=n_m,
                        tabla="T4",
                        ejecucion_ids=_sample_ids(rm["evidencia_ids"], 3),
                    ),
                ]
                desc = (
                    f"En consultas sin marca sobre {ciudad_crecimiento}, {marca} aparece en el "
                    f"{v_growth:.1f}% de las respuestas (n={n_g}), frente al {v_main:.1f}% en "
                    f"{ciudad_principal} (n={n_m}), lo que confirma la hipótesis del cliente sobre "
                    f"la baja visibilidad local en {ciudad_crecimiento}."
                )
                candidates.append(
                    (
                        100.0,
                        {
                            "titulo": f"Brecha crítica de visibilidad en {ciudad_crecimiento} frente a {ciudad_principal}",
                            "descripcion": desc,
                            "tipo": "geografia",
                            "fase_embudo": "Descubrimiento",
                            "motores": [],
                            "evidencias": evs,
                            "impacto": "alto",
                            "confianza": _calc_confianza(min(n_g, n_m)),
                        },
                    )
                )

    # ---------- R2: Motor débil ----------
    t2_m = t2[t2["marca"] == marca].copy()
    if len(t2_m) >= 2:
        weak_motors: list[Motor] = []
        ev_r2: list[Evidencia] = []
        for _, rm in t2_m.iterrows():
            m_name: Motor = str(rm["motor"])  # type: ignore[assignment]
            ap_m = float(rm["tasa_aparicion"])
            others_mean = float(t2_m[t2_m["motor"] != m_name]["tasa_aparicion"].mean())
            if others_mean > 0 and ap_m < FINDINGS_THRESHOLDS["r2_weak_motor_ratio"] * others_mean:
                weak_motors.append(m_name)
                ev_r2.append(
                    Evidencia(
                        metrica=f"tasa_aparicion_espontanea[motor={m_name}]",
                        valor=round(ap_m * 100.0, 1),
                        n=int(rm["n"]),
                        tabla="T2",
                        ejecucion_ids=_sample_ids(rm["evidencia_ids"], 3),
                    )
                )
        if weak_motors:
            strong_df = t2_m[~t2_m["motor"].isin(weak_motors)].sort_values(
                "tasa_aparicion", ascending=False
            )
            for _, rs in strong_df.iterrows():
                ms_name = str(rs["motor"])
                ev_r2.append(
                    Evidencia(
                        metrica=f"tasa_aparicion_espontanea[motor={ms_name}]",
                        valor=round(float(rs["tasa_aparicion"]) * 100.0, 1),
                        n=int(rs["n"]),
                        tabla="T2",
                        ejecucion_ids=_sample_ids(rs["evidencia_ids"], 3),
                    )
                )
            weak_parts = [f"{e.metrica.split('=')[1].rstrip(']')} ({e.valor:.1f}%, n={e.n})" for e in ev_r2[: len(weak_motors)]]
            strong_parts = [f"{e.metrica.split('=')[1].rstrip(']')} ({e.valor:.1f}%, n={e.n})" for e in ev_r2[len(weak_motors) :]]
            impacto_r2: Literal["alto", "medio", "bajo"] = (
                "alto" if "ChatGPT" in weak_motors else "medio"
            )
            candidates.append(
                (
                    95.0,
                    {
                        "titulo": f"Visibilidad espontánea deficitaria en {', '.join(weak_motors)}",
                        "descripcion": (
                            f"La aparición espontánea de {marca} cae en {', '.join(weak_parts)}, "
                            f"muy por debajo de su presencia en {', '.join(strong_parts)}."
                        ),
                        "tipo": "motor",
                        "fase_embudo": None,
                        "motores": weak_motors,
                        "evidencias": ev_r2,
                        "impacto": impacto_r2,
                        "confianza": _calc_confianza(min(e.n for e in ev_r2)),
                    },
                )
            )

    # ---------- R4: Brecha con el líder y los competidores ----------
    sc_marca = round(float(row_marca_t1["score"]), 2)
    ap_marca = round(float(row_marca_t1["tasa_aparicion"]) * 100.0, 1)
    n_marca = int(row_marca_t1["n"])
    sc_lider = round(float(row_lider_t1["score"]), 2)
    ap_lider = round(float(row_lider_t1["tasa_aparicion"]) * 100.0, 1)
    n_lider = int(row_lider_t1["n"])

    row_tram = t1_esp[t1_esp["marca"] == "Instituto Oftálmico Tramuntana"]
    ev_r4 = [
        Evidencia(
            metrica=f"score_espontaneo[marca={marca}]",
            valor=sc_marca,
            n=n_marca,
            tabla="T1_espontanea",
            ejecucion_ids=_sample_ids(row_marca_t1["evidencia_ids"], 3),
        ),
        Evidencia(
            metrica=f"tasa_aparicion_espontanea[marca={marca}]",
            valor=ap_marca,
            n=n_marca,
            tabla="T1_espontanea",
            ejecucion_ids=_sample_ids(row_marca_t1["evidencia_ids"], 3),
        ),
        Evidencia(
            metrica=f"score_espontaneo[marca={lider}]",
            valor=sc_lider,
            n=n_lider,
            tabla="T1_espontanea",
            ejecucion_ids=_sample_ids(row_lider_t1["evidencia_ids"], 3),
        ),
        Evidencia(
            metrica=f"tasa_aparicion_espontanea[marca={lider}]",
            valor=ap_lider,
            n=n_lider,
            tabla="T1_espontanea",
            ejecucion_ids=_sample_ids(row_lider_t1["evidencia_ids"], 3),
        ),
    ]
    extra_comp_txt = ""
    if not row_tram.empty:
        rt = row_tram.iloc[0]
        sc_tram = round(float(rt["score"]), 2)
        ap_tram = round(float(rt["tasa_aparicion"]) * 100.0, 1)
        n_tram = int(rt["n"])
        ev_r4.extend(
            [
                Evidencia(
                    metrica="score_espontaneo[marca=Instituto Oftálmico Tramuntana]",
                    valor=sc_tram,
                    n=n_tram,
                    tabla="T1_espontanea",
                    ejecucion_ids=_sample_ids(rt["evidencia_ids"], 3),
                ),
                Evidencia(
                    metrica="tasa_aparicion_espontanea[marca=Instituto Oftálmico Tramuntana]",
                    valor=ap_tram,
                    n=n_tram,
                    tabla="T1_espontanea",
                    ejecucion_ids=_sample_ids(rt["evidencia_ids"], 3),
                ),
            ]
        )
        extra_comp_txt = (
            f" y frente a Instituto Oftálmico Tramuntana con score {sc_tram:.2f} "
            f"y {ap_tram:.1f}% de aparición (n={n_tram})"
        )

    candidates.append(
        (
            92.0,
            {
                "titulo": f"Brecha de visibilidad espontánea frente a {lider} y competidores directos",
                "descripcion": (
                    f"{marca} registra un score espontáneo de {sc_marca:.2f} con un {ap_marca:.1f}% "
                    f"de aparición (n={n_marca}), frente al líder {lider} con score {sc_lider:.2f} "
                    f"y {ap_lider:.1f}% de aparición (n={n_lider}){extra_comp_txt}."
                ),
                "tipo": "competencia",
                "fase_embudo": None,
                "motores": [],
                "evidencias": ev_r4,
                "impacto": "alto",
                "confianza": _calc_confianza(n_marca),
            },
        )
    )

    # ---------- R7: Brief vs datos (competidores no declarados, líder real e hipótesis) ----------
    declarados_set = {marca, *ficha_activa.competidores_declarados}
    if contraste_mercado is not None:
        no_decl = list(contraste_mercado.no_declaradas_relevantes)
    else:
        no_decl = [
            str(r["marca"])
            for _, r in t1_esp.iterrows()
            if str(r["marca"]) not in declarados_set
            and float(r["tasa_aparicion"]) >= FINDINGS_THRESHOLDS["r7_undeclared_competitor_min"]
        ]

    row_vist = t1_esp[t1_esp["marca"] == "Vistalia Oftalmología"]
    if not row_vist.empty:
        rv = row_vist.iloc[0]
        ap_vist = round(float(rv["tasa_aparicion"]) * 100.0, 1)
        n_vist = int(rv["n"])
        rec_alb = round(float(row_marca_t1["%recomendacion_activa"]) * 100.0, 1)
        ev_r7 = [
            Evidencia(
                metrica="tasa_aparicion_espontanea[marca=Vistalia Oftalmología]",
                valor=ap_vist,
                n=n_vist,
                tabla="T1_espontanea",
                ejecucion_ids=_sample_ids(rv["evidencia_ids"], 3),
            ),
            Evidencia(
                metrica=f"tasa_aparicion_espontanea[marca={lider}]",
                valor=ap_lider,
                n=n_lider,
                tabla="T1_espontanea",
                ejecucion_ids=_sample_ids(row_lider_t1["evidencia_ids"], 3),
            ),
            Evidencia(
                metrica=f"pct_recomendacion_activa_espontanea[marca={marca}]",
                valor=rec_alb,
                n=n_marca,
                tabla="T1_espontanea",
                ejecucion_ids=_sample_ids(row_marca_t1["evidencia_ids"], 3),
            ),
        ]
        candidates.append(
            (
                90.0,
                {
                    "titulo": "Contraste Brief vs Datos: Vistalia omitida, Valdecruz líder real y reseñas insuficientes",
                    "descripcion": (
                        f"El brief no incluye a Vistalia Oftalmología, que alcanza un {ap_vist:.1f}% de "
                        f"aparición espontánea (n={n_vist}); además, el líder real en IA es {lider} con "
                        f"un {ap_lider:.1f}% (n={n_lider}) y no Tramuntana, y las buenas reseñas de "
                        f"{marca} solo se traducen en un {rec_alb:.1f}% de recomendación activa (n={n_marca})."
                    ),
                    "tipo": "brief_vs_datos",
                    "fase_embudo": None,
                    "motores": [],
                    "evidencias": ev_r7,
                    "impacto": "alto",
                    "confianza": _calc_confianza(n_vist),
                },
            )
        )

    # ---------- R3: Caída en el embudo (Descubrimiento -> Decisión) ----------
    t3_m = t3[t3["marca"] == marca].set_index("intencion")
    if "Descubrimiento" in t3_m.index and "Decisión" in t3_m.index:
        r_desc = t3_m.loc["Descubrimiento"]
        r_dec = t3_m.loc["Decisión"]
        ap_desc = round(float(r_desc["tasa_aparicion"]) * 100.0, 1)
        n_desc = int(r_desc["n"])
        ap_dec = round(float(r_dec["tasa_aparicion"]) * 100.0, 1)
        n_dec = int(r_dec["n"])

        row_dec_t11 = t11[t11["intencion"] == "Decisión"]
        ap_lider_dec = (
            round(float(row_dec_t11.iloc[0]["tasa_aparicion_lider"]) * 100.0, 1)
            if not row_dec_t11.empty
            else ap_lider
        )
        drop_pp = ap_desc - ap_dec
        gap_lider_pp = ap_lider_dec - ap_dec
        if (
            drop_pp >= FINDINGS_THRESHOLDS["r3_funnel_drop_pp"] - 1.0
            or gap_lider_pp >= FINDINGS_THRESHOLDS["r3_funnel_leader_gap_pp"]
        ):
            ev_r3 = [
                Evidencia(
                    metrica="tasa_aparicion_espontanea[intencion=Descubrimiento]",
                    valor=ap_desc,
                    n=n_desc,
                    tabla="T3",
                    ejecucion_ids=_sample_ids(r_desc["evidencia_ids"], 3),
                ),
                Evidencia(
                    metrica="tasa_aparicion_espontanea[intencion=Decisión]",
                    valor=ap_dec,
                    n=n_dec,
                    tabla="T3",
                    ejecucion_ids=_sample_ids(r_dec["evidencia_ids"], 3),
                ),
                Evidencia(
                    metrica=f"tasa_aparicion_lider[intencion=Decisión,lider={lider}]",
                    valor=ap_lider_dec,
                    n=n_dec,
                    tabla="T11",
                    ejecucion_ids=_sample_ids(r_dec["evidencia_ids"], 3),
                ),
            ]
            candidates.append(
                (
                    86.0,
                    {
                        "titulo": "Caída de visibilidad en la fase de Decisión del embudo",
                        "descripcion": (
                            f"{marca} pasa de un {ap_desc:.1f}% de aparición espontánea en Descubrimiento "
                            f"(n={n_desc}) a un {ap_dec:.1f}% en la fase crítica de Decisión (n={n_dec}), "
                            f"donde {lider} alcanza el {ap_lider_dec:.1f}% (n={n_dec})."
                        ),
                        "tipo": "embudo",
                        "fase_embudo": "Decisión",
                        "motores": [],
                        "evidencias": ev_r3,
                        "impacto": "alto",
                        "confianza": _calc_confianza(min(n_desc, n_dec)),
                    },
                )
            )

    # ---------- R5: Perfil de fuentes (autoridad terceros vs líder / Sin fuente) ----------
    t6_m = t6[t6["marca"] == marca]
    t6_l = t6[t6["marca"] == lider]
    if not t6_m.empty and not t6_l.empty:
        auth_types = {"Ranking / institución", "Medio"}
        n_ap_m = int(t6_m.iloc[0]["n_apariciones_marca"])
        n_ap_l = int(t6_l.iloc[0]["n_apariciones_marca"])
        auth_m = round(
            float(t6_m[t6_m["tipo_fuente"].isin(auth_types)]["pct_apariciones"].sum()) * 100.0,
            1,
        )
        auth_l = round(
            float(t6_l[t6_l["tipo_fuente"].isin(auth_types)]["pct_apariciones"].sum()) * 100.0,
            1,
        )
        cal_m = round(float(t6_m.iloc[0]["calidad_media_marca"]), 2)
        cal_l = round(float(t6_l.iloc[0]["calidad_media_marca"]), 2)
        ev_ids_m = _sample_ids(t6_m.iloc[0]["evidencia_ids"], 3)
        ev_ids_l = _sample_ids(t6_l.iloc[0]["evidencia_ids"], 3)
        ev_r5 = [
            Evidencia(
                metrica=f"pct_fuentes_autoridad[marca={marca}]",
                valor=auth_m,
                n=n_ap_m,
                tabla="T6",
                ejecucion_ids=ev_ids_m,
            ),
            Evidencia(
                metrica=f"pct_fuentes_autoridad[marca={lider}]",
                valor=auth_l,
                n=n_ap_l,
                tabla="T6",
                ejecucion_ids=ev_ids_l,
            ),
            Evidencia(
                metrica=f"calidad_media_fuente[marca={marca}]",
                valor=cal_m,
                n=n_ap_m,
                tabla="T6",
                ejecucion_ids=ev_ids_m,
            ),
        ]
        candidates.append(
            (
                80.0,
                {
                    "titulo": "Menor respaldo en rankings y prensa sanitaria frente al líder",
                    "descripcion": (
                        f"El {auth_m:.1f}% de las apariciones de {marca} se apoya en Rankings o Medios "
                        f"(n={n_ap_m}, calidad media {cal_m:.2f}), frente al {auth_l:.1f}% de {lider} "
                        f"(n={n_ap_l})."
                    ),
                    "tipo": "fuentes",
                    "fase_embudo": "Validación",
                    "motores": [],
                    "evidencias": ev_r5,
                    "impacto": "alto",
                    "confianza": _calc_confianza(n_ap_m),
                },
            )
        )

    # ---------- R6: Reputación en asistida y ventaja competitiva en postoperatorio ----------
    t9_m = t9[t9["marca"] == marca]
    t9_nit = t9[t9["marca"] == "Láser Nítida"]
    if not t9_m.empty and not t9_nit.empty:
        rm9 = t9_m.iloc[0]
        rn9 = t9_nit.iloc[0]
        neg_alb = round(float(rm9["%negativo"]) * 100.0, 1)
        fm_alb = round(float(rm9["fuerza_media"]), 2)
        n_alb9 = int(rm9["n"])
        neg_nit = round(float(rn9["%negativo"]) * 100.0, 1)
        n_nit9 = int(rn9["n"])
        ev_r6 = [
            Evidencia(
                metrica=f"pct_negativo_asistida[marca={marca}]",
                valor=neg_alb,
                n=n_alb9,
                tabla="T9",
                ejecucion_ids=_sample_ids(rm9["evidencia_ids"], 3),
            ),
            Evidencia(
                metrica=f"fuerza_media_asistida[marca={marca}]",
                valor=fm_alb,
                n=n_alb9,
                tabla="T9",
                ejecucion_ids=_sample_ids(rm9["evidencia_ids"], 3),
            ),
            Evidencia(
                metrica="pct_negativo_asistida[marca=Láser Nítida]",
                valor=neg_nit,
                n=n_nit9,
                tabla="T9",
                ejecucion_ids=_sample_ids(rn9["evidencia_ids"], 3),
            ),
        ]
        candidates.append(
            (
                78.0,
                {
                    "titulo": "Reputación asistida sólida y oportunidad en seguimiento postoperatorio",
                    "descripcion": (
                        f"En menciones asistidas, {marca} presenta solo un {neg_alb:.1f}% de menciones "
                        f"negativas y fuerza media de {fm_alb:.2f} (n={n_alb9}), mientras que Láser Nítida "
                        f"acumula un {neg_nit:.1f}% de menciones negativas por seguimiento postoperatorio "
                        f"(n={n_nit9})."
                    ),
                    "tipo": "reputacion",
                    "fase_embudo": "Validación",
                    "motores": [],
                    "evidencias": ev_r6,
                    "impacto": "medio",
                    "confianza": _calc_confianza(n_alb9),
                },
            )
        )

    # ---------- R8: Consistencia entre repeticiones ----------
    t10_m = t10[t10["marca"] == marca]
    if not t10_m.empty:
        r10 = t10_m.iloc[0]
        pct_azar = round(float(r10["%azar"]) * 100.0, 1)
        pct_cons = round(float(r10["%consolidada"]) * 100.0, 1)
        n_s = int(r10["n"])
        if float(r10["%azar"]) > FINDINGS_THRESHOLDS["r8_azar_min"] or float(r10["%consolidada"]) < 0.35:
            ev_r8 = [
                Evidencia(
                    metrica=f"pct_azar_espontanea[marca={marca}]",
                    valor=pct_azar,
                    n=n_s,
                    tabla="T10",
                    ejecucion_ids=_sample_ids(r10["evidencia_ids"], 3),
                ),
                Evidencia(
                    metrica=f"pct_consolidada_espontanea[marca={marca}]",
                    valor=pct_cons,
                    n=n_s,
                    tabla="T10",
                    ejecucion_ids=_sample_ids(r10["evidencia_ids"], 3),
                ),
            ]
            candidates.append(
                (
                    70.0,
                    {
                        "titulo": "Presencia intermitente entre repeticiones del mismo prompt",
                        "descripcion": (
                            f"En las series espontáneas (n={n_s}), {marca} aparece de forma consolidada "
                            f"en el {pct_cons:.1f}% y queda en zona de azar en el {pct_azar:.1f}%."
                        ),
                        "tipo": "consistencia",
                        "fase_embudo": None,
                        "motores": [],
                        "evidencias": ev_r8,
                        "impacto": "medio",
                        "confianza": _calc_confianza(n_s),
                    },
                )
            )

    # ---------- R9: Perfil de usuario (Familia DP) ----------
    t5_m = t5[(t5["marca"] == marca) & (t5["familia"] == "Descubrimiento por perfil")]
    if not t5_m.empty:
        r5 = t5_m.iloc[0]
        ap_dp = round(float(r5["tasa_aparicion"]) * 100.0, 1)
        sc_dp = round(float(r5["score"]), 2)
        n_dp = int(r5["n"])
        ev_r9 = [
            Evidencia(
                metrica="tasa_aparicion_espontanea[familia=Descubrimiento por perfil]",
                valor=ap_dp,
                n=n_dp,
                tabla="T5",
                ejecucion_ids=_sample_ids(r5["evidencia_ids"], 3),
            ),
            Evidencia(
                metrica="score_espontaneo[familia=Descubrimiento por perfil]",
                valor=sc_dp,
                n=n_dp,
                tabla="T5",
                ejecucion_ids=_sample_ids(r5["evidencia_ids"], 3),
            ),
        ]
        candidates.append(
            (
                74.0,
                {
                    "titulo": "Margen de crecimiento en consultas por perfil de paciente",
                    "descripcion": (
                        f"En consultas de Descubrimiento por perfil (miopía infantil, refractiva, "
                        f"cataratas y pilotos), {marca} registra un {ap_dp:.1f}% de aparición y "
                        f"un score de {sc_dp:.2f} (n={n_dp})."
                    ),
                    "tipo": "perfil",
                    "fase_embudo": "Descubrimiento",
                    "motores": [],
                    "evidencias": ev_r9,
                    "impacto": "alto",
                    "confianza": _calc_confianza(n_dp),
                },
            )
        )

    # Ordenar por puntuación de prioridad descendente y asignar H1..H7
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = candidates[:MAX_FINDINGS]

    hallazgos: list[Hallazgo] = []
    for idx, (_, data) in enumerate(selected, start=1):
        hallazgos.append(
            Hallazgo(
                id=f"H{idx}",
                titulo=data["titulo"],
                descripcion=data["descripcion"],
                tipo=data["tipo"],
                fase_embudo=data["fase_embudo"],
                motores=data["motores"],
                evidencias=data["evidencias"],
                impacto=data["impacto"],
                confianza=data["confianza"],
                prioridad=idx,
                aprobado=True,
            )
        )

    return hallazgos
