"""Tests de detección de marcas y posición (F2)."""

import pandas as pd

from geo.detection import detect, detect_in_response
from geo.loader import load_ejecuciones, load_marcas, load_muestra
from geo.text import find_first_offset, normalize, segmentos_por_marca
from geo.reference import REFERENCE_DIR


def test_normalize_basic() -> None:
    """Comprueba que normalize elimina tildes, negritas '**', citas '[1]' y colapsa espacios."""
    raw = "  1. **Clínica Alborada Visión**[1] — Atención   óptima [2]  "
    assert normalize(raw) == "1. clinica alborada vision — atencion optima"


def test_false_positive_nitida_lowercase_adjective() -> None:
    """'nítida' en minúscula como adjetivo ('visión nítida') no debe dar positivo para Láser Nítida."""
    marcas = {m.nombre: m for m in load_marcas(REFERENCE_DIR)}
    nitida = marcas["Láser Nítida"]

    # Adjetivo en minúscula -> NO aparece
    assert find_first_offset("El paciente recupera una visión nítida en pocos días.", nitida) is None
    assert find_first_offset("Ofrece imagen nitida y sin halos nocturnos.", nitida) is None

    # En mayúscula o precedido de 'Láser' -> SÍ aparece
    assert find_first_offset("6. **Nítida** — precios cerrados y financiación.", nitida) is not None
    assert find_first_offset("En láser nítida ofrecen tarifas cerradas.", nitida) is not None
    assert find_first_offset("Recomendamos Láser Nítida por su rapidez.", nitida) is not None


def test_false_positive_lasik_generic() -> None:
    """'Lasik' o 'LASIK' como técnica quirúrgica genérica no debe activar Centro Lasik Península."""
    marcas = {m.nombre: m for m in load_marcas(REFERENCE_DIR)}
    lasik_peninsula = marcas["Centro Lasik Península"]

    assert find_first_offset("Especialistas en cirugía LASIK, PRK y lentes ICL.", lasik_peninsula) is None
    assert find_first_offset("El tratamiento con lasik dura pocos minutos.", lasik_peninsula) is None

    # Solo cuenta el nombre o el alias completo 'Lasik Península'
    assert find_first_offset("En Lasik Península realizan el preoperatorio en un día.", lasik_peninsula) is not None
    assert find_first_offset("Centro Lasik Península cuenta con varias sedes.", lasik_peninsula) is not None


def test_alborada_and_street_name_aliases() -> None:
    """Comprueba detección de Alborada y documenta comportamiento de Cervantes y Santa Eulalia."""
    marcas = {m.nombre: m for m in load_marcas(REFERENCE_DIR)}
    alborada = marcas["Clínica Alborada Visión"]
    cervantes = marcas["Clínica del Ojo Cervantes"]
    santa_eulalia = marcas["Instituto Ocular Santa Eulalia"]

    assert find_first_offset("Alborada destaca por su seguimiento postoperatorio.", alborada) is not None
    assert find_first_offset("Clínica Alborada Visión en Madrid y Barcelona.", alborada) is not None
    assert find_first_offset("Alboradaista no es el nombre de la marca.", alborada) is None

    # Límites de palabra para Cervantes y Santa Eulalia
    assert find_first_offset("Cervantes cuenta con un equipo veterano.", cervantes) is not None
    assert find_first_offset("Santa Eulalia destaca por su actividad docente.", santa_eulalia) is not None


def test_segmentos_por_marca_bullets_and_prose() -> None:
    """Comprueba la extracción de segmentos tanto en listas con viñetas como en prosa continua."""
    marcas = load_marcas(REFERENCE_DIR)
    marca_map = {m.nombre: m for m in marcas}
    valdecruz = marca_map["Grupo Hospitalario Valdecruz"]
    alborada = marca_map["Clínica Alborada Visión"]

    bullet_text = (
        "Opciones principales:\n\n"
        "1. **Grupo Hospitalario Valdecruz** — referente hospitalario. Es la que más recomendaría.\n"
        "2. **Clínica Alborada Visión** — seguimiento personalizado.\n\n"
        "**En resumen:** Grupo Hospitalario Valdecruz es la opción más recomendable."
    )
    segs_val = segmentos_por_marca(bullet_text, valdecruz, marcas)
    assert len(segs_val) == 2
    assert "Es la que más recomendaría" in segs_val[0]

    prose_text = (
        "Estas son algunas opciones. "
        "Grupo Hospitalario Valdecruz es un referente por volumen de intervenciones. "
        "Resulta una opción sólida y bien valorada. "
        "Clínica Alborada Visión destaca por el seguimiento personalizado. "
        "Conviene contrastar varias opciones."
    )
    segs_prose_val = segmentos_por_marca(prose_text, valdecruz, marcas)
    assert len(segs_prose_val) == 1
    assert "Resulta una opción sólida y bien valorada." in segs_prose_val[0]
    assert "Clínica Alborada Visión" not in segs_prose_val[0]

    segs_prose_alb = segmentos_por_marca(prose_text, alborada, marcas)
    assert len(segs_prose_alb) == 1
    assert "seguimiento personalizado" in segs_prose_alb[0]
    assert "Conviene contrastar" not in segs_prose_alb[0]


def test_detect_2928_rows_and_100_percent_match_with_muestra() -> None:
    """Valida que detect() genera 2.928 filas y coincide al 100 % (133/133) con muestra_evaluada.csv."""
    marcas = load_marcas(REFERENCE_DIR)
    df_ej = load_ejecuciones(REFERENCE_DIR)
    df_muestra = load_muestra(REFERENCE_DIR)

    df_det = detect(df_ej, marcas)
    assert len(df_det) == 2928
    assert list(df_det.columns) == [
        "ejecucion_id",
        "marca",
        "aparece",
        "posicion",
        "peso_posicion",
        "fragmento",
    ]

    merged = df_muestra.merge(
        df_det,
        on=["ejecucion_id", "marca"],
        suffixes=("_muestra", "_pred"),
        how="inner",
    )
    assert len(merged) == 133

    discrepancias: list[str] = []
    for _, row in merged.iterrows():
        ap_m = int(row["aparece_muestra"])
        ap_p = int(row["aparece_pred"])

        pos_m = None if pd.isna(row["posicion_muestra"]) else int(row["posicion_muestra"])
        pos_p = None if pd.isna(row["posicion_pred"]) else int(row["posicion_pred"])

        peso_m = int(row["peso_posicion_muestra"])
        peso_p = int(row["peso_posicion_pred"])

        if (ap_m != ap_p) or (pos_m != pos_p) or (peso_m != peso_p):
            discrepancias.append(
                f"{row['ejecucion_id']} | {row['marca']}: "
                f"pred=({ap_p}, {pos_p}, {peso_p}) vs muestra=({ap_m}, {pos_m}, {peso_m})"
            )

    assert not discrepancias, "Discrepancias en detección:\n" + "\n".join(discrepancias)
