"""Script para imprimir recuentos y cifras clave de verificación (F1 y F5)."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.detection import detect
from geo.judge_rules import judge_rules
from geo.loader import (
    as_ejecuciones,
    dominios_desconocidos,
    load_ejecuciones,
    load_fuentes,
    load_marcas,
    load_muestra,
    load_prompts,
)
from geo.metrics import bundle


def main() -> None:
    """Imprime los recuentos de verificación de datos del kit y las tablas clave de F5."""
    marcas = load_marcas()
    prompts = load_prompts()
    fuentes = load_fuentes()
    df_ej = load_ejecuciones()
    ejecuciones = as_ejecuciones()
    df_muestra = load_muestra()
    desconocidos = dominios_desconocidos()

    marca_brief = next((m.nombre for m in marcas if m.es_marca_brief), "Clínica Alborada Visión")
    por_motor = df_ej["motor"].value_counts().to_dict()
    n_espontaneas = int(df_ej["espontanea"].sum())
    n_asistidas = int((~df_ej["espontanea"]).sum())
    ciudades = df_ej["ciudad"].value_counts(dropna=True).to_dict()
    n_sin_fuentes = int(df_ej["fuentes"].apply(lambda x: len(x) == 0).sum())
    pares_evaluar = sum(len(e.marcas_a_evaluar) for e in ejecuciones)

    print("=== GEO Copilot · Smoke Numbers (F1: Carga de datos) ===")
    print(f"Marcas cargadas           : {len(marcas)} (Marca del brief: {marca_brief})")
    print(f"Prompts cargados          : {len(prompts)}")
    print(f"Fuentes en catálogo       : {len(fuentes)} (Dominios desconocidos: {len(desconocidos)})")
    print(f"Ejecuciones totales       : {len(df_ej)}")
    print(f"  - Por motor             : {por_motor}")
    print(f"  - Espontáneas           : {n_espontaneas}")
    print(f"  - Asistidas             : {n_asistidas}")
    print(f"  - Por ciudad            : {ciudades}")
    print(f"  - Sin fuentes (sin web) : {n_sin_fuentes} ({n_sin_fuentes / len(df_ej):.1%})")
    print(f"  - Pares (ej × marca)    : {pares_evaluar}")
    print(
        f"Muestra evaluada          : {len(df_muestra)} filas "
        f"({df_muestra['ejecucion_id'].nunique()} Ejecucion_ID únicos)"
    )

    # F5: Score y tablas clave
    df_det = detect(df_ej, marcas)
    evals = judge_rules(df_det, df_ej, marcas, fuentes)
    tablas = bundle(evals, df_ej, marcas)

    cols_view = [
        "puesto",
        "marca",
        "n",
        "tasa_aparicion",
        "pos_media",
        "fuerza_media",
        "%recomendacion_activa",
        "score",
    ]
    print("\n=== F5 · T1 Ranking Espontáneo ===")
    t1_esp = tablas["T1_espontanea"][cols_view].copy()
    t1_esp["tasa_aparicion"] = (t1_esp["tasa_aparicion"] * 100).round(1)
    t1_esp["pos_media"] = t1_esp["pos_media"].round(2)
    t1_esp["fuerza_media"] = t1_esp["fuerza_media"].round(2)
    t1_esp["%recomendacion_activa"] = (t1_esp["%recomendacion_activa"] * 100).round(1)
    t1_esp["score"] = t1_esp["score"].round(2)
    print(t1_esp.to_string(index=False))

    print(f"\n=== F5 · T2 {marca_brief} por Motor (Espontánea) ===")
    t2_alb = tablas["T2"][tablas["T2"]["marca"] == marca_brief][
        ["motor", "n", "tasa_aparicion", "pos_media", "fuerza_media", "score"]
    ].copy()
    t2_alb["tasa_aparicion"] = (t2_alb["tasa_aparicion"] * 100).round(1)
    t2_alb["pos_media"] = t2_alb["pos_media"].round(2)
    t2_alb["fuerza_media"] = t2_alb["fuerza_media"].round(2)
    t2_alb["score"] = t2_alb["score"].round(2)
    print(t2_alb.to_string(index=False))

    print(f"\n=== F5 · T4 {marca_brief} por Ciudad (Espontánea) ===")
    t4_alb = tablas["T4"][tablas["T4"]["marca"] == marca_brief][
        ["ciudad", "n", "tasa_aparicion", "pos_media", "fuerza_media", "score"]
    ].copy()
    t4_alb["tasa_aparicion"] = (t4_alb["tasa_aparicion"] * 100).round(1)
    t4_alb["pos_media"] = t4_alb["pos_media"].round(2)
    t4_alb["fuerza_media"] = t4_alb["fuerza_media"].round(2)
    t4_alb["score"] = t4_alb["score"].round(2)
    print(t4_alb.to_string(index=False))

    print(f"\n=== F5 · T3 {marca_brief} por Fase del Embudo (Espontánea) ===")
    t3_alb = tablas["T3"][tablas["T3"]["marca"] == marca_brief][
        ["intencion", "n", "tasa_aparicion", "pos_media", "fuerza_media", "score"]
    ].copy()
    t3_alb["tasa_aparicion"] = (t3_alb["tasa_aparicion"] * 100).round(1)
    t3_alb["pos_media"] = t3_alb["pos_media"].round(2)
    t3_alb["fuerza_media"] = t3_alb["fuerza_media"].round(2)
    t3_alb["score"] = t3_alb["score"].round(2)
    print(t3_alb.to_string(index=False))


if __name__ == "__main__":
    main()
