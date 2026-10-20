"""Script para imprimir recuentos y cifras clave de verificación."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.loader import (
    as_ejecuciones,
    dominios_desconocidos,
    load_ejecuciones,
    load_fuentes,
    load_marcas,
    load_muestra,
    load_prompts,
)


def main() -> None:
    """Imprime los recuentos de verificación de datos del kit."""
    marcas = load_marcas()
    prompts = load_prompts()
    fuentes = load_fuentes()
    df_ej = load_ejecuciones()
    ejecuciones = as_ejecuciones()
    df_muestra = load_muestra()
    desconocidos = dominios_desconocidos()

    marca_brief = next((m.nombre for m in marcas if m.es_marca_brief), "N/A")
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


if __name__ == "__main__":
    main()
