"""Detección de aparición y posición de marcas en las respuestas."""

from typing import Sequence
import pandas as pd

from geo.config import peso_por_posicion
from geo.schemas import Ejecucion, Marca
from geo.text import find_first_offset, segmentos_por_marca


def detect_in_response(
    respuesta: str,
    marcas_sector: Sequence[Marca],
) -> dict[str, tuple[int, int | None, int, str | None]]:
    """Calcula (aparece, posicion, peso_posicion, fragmento) para todas las marcas del sector en una respuesta.

    La posición se asigna según el orden del primer offset de aparición entre todas las marcas del sector
    presentes en la respuesta (validado al 100 % contra muestra_evaluada.csv).
    """
    marca_list = list(marcas_sector)
    offsets: dict[str, int] = {}
    for m in marca_list:
        off = find_first_offset(respuesta, m)
        if off is not None:
            offsets[m.nombre] = off

    ordered_present = sorted(offsets.keys(), key=lambda nombre: offsets[nombre])
    pos_by_brand: dict[str, int] = {
        nombre: idx + 1 for idx, nombre in enumerate(ordered_present)
    }

    result: dict[str, tuple[int, int | None, int, str | None]] = {}
    for m in marca_list:
        if m.nombre in pos_by_brand:
            pos = pos_by_brand[m.nombre]
            peso = peso_por_posicion(pos)
            segs = segmentos_por_marca(respuesta, m, todas_las_marcas=marca_list)
            frag = " \n".join(segs) if segs else None
            result[m.nombre] = (1, pos, peso, frag)
        else:
            result[m.nombre] = (0, None, 0, None)
    return result


def detect(
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
) -> pd.DataFrame:
    """Detecta aparición, posición, peso_posicion y fragmento para cada marca a evaluar por ejecución.

    Devuelve un DataFrame con columnas:
    ['ejecucion_id', 'marca', 'aparece', 'posicion', 'peso_posicion', 'fragmento']
    """
    marca_list = list(marcas)
    rows: list[dict[str, object]] = []

    if isinstance(ejecuciones, pd.DataFrame):
        iterable = ejecuciones[["ejecucion_id", "respuesta", "marcas_a_evaluar"]].to_dict(
            orient="records"
        )
    else:
        iterable = [
            {
                "ejecucion_id": ej.ejecucion_id,
                "respuesta": ej.respuesta,
                "marcas_a_evaluar": ej.marcas_a_evaluar,
            }
            for ej in ejecuciones
        ]

    for item in iterable:
        ej_id = str(item["ejecucion_id"])
        respuesta = str(item["respuesta"])
        marcas_eval: list[str] = list(item["marcas_a_evaluar"])  # type: ignore[arg-type]

        det_map = detect_in_response(respuesta, marca_list)
        for nombre_marca in marcas_eval:
            if nombre_marca in det_map:
                aparece, posicion, peso_pos, fragmento = det_map[nombre_marca]
            else:
                aparece, posicion, peso_pos, fragmento = (0, None, 0, None)

            rows.append(
                {
                    "ejecucion_id": ej_id,
                    "marca": nombre_marca,
                    "aparece": aparece,
                    "posicion": posicion,
                    "peso_posicion": peso_pos,
                    "fragmento": fragmento,
                }
            )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["aparece"] = df["aparece"].astype(int)
        df["peso_posicion"] = df["peso_posicion"].astype(int)
        df["posicion"] = df["posicion"].astype(object).where(df["posicion"].notna(), None)
    return df
