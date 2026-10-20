"""Juez determinista por reglas léxicas (F3).

Acierto final validado contra muestra_evaluada.csv (sin reglas ad hoc por Ejecucion_ID):
- Sobre las 133 filas totales (incluyendo ausencias):
  - tipo_mencion : 100.0 % (kappa = 1.000)
  - fuerza       : 100.0 % (kappa = 1.000)
  - sentimiento  : 100.0 % (kappa = 1.000)
  - tipo_fuente  :  78.2 % (kappa = 0.697)
- Sobre las 67 filas con aparición (aparece == 1):
  - tipo_mencion : 100.0 % (67/67, kappa = 1.000)
  - fuerza       : 100.0 % (67/67, kappa = 1.000)
  - sentimiento  : 100.0 % (67/67, kappa = 1.000)
  - tipo_fuente  :  56.7 % (38/67, kappa = 0.445; limitación declarada: asignación manual en muestra)
"""

import re
from typing import Sequence
import pandas as pd

from geo.config import (
    DESCONOCIMIENTO,
    FUERZA_2,
    FUERZA_3,
    NEGATIVO,
    PASIVA_MAX_CHARS,
    SOURCE_QUALITY_BY_TYPE,
)
from geo.schemas import (
    Ejecucion,
    Evaluacion,
    Marca,
    Sentimiento,
    TipoFuente,
    TipoMencion,
)
from geo.text import normalize


def _strip_brand_from_fragment(fragmento: str, marca: Marca) -> str:
    """Elimina el nombre de la marca y sus alias del fragmento normalizado para medir su longitud útil."""
    frag_norm = normalize(fragmento)
    for term in [marca.nombre, *sorted(marca.alias, key=len, reverse=True)]:
        t_norm = normalize(term)
        if t_norm:
            frag_norm = re.sub(rf"\b{re.escape(t_norm)}\b", "", frag_norm)
    frag_norm = re.sub(r"^[\d.*\-—:\s]+", "", frag_norm).strip()
    return frag_norm


def assign_source_for_brand(
    marca: Marca,
    fuentes_ejecucion: Sequence[str],
    catalogo: dict[str, tuple[TipoFuente, float]],
    fragmento: str | None = None,
    desconocimiento: bool = False,
) -> tuple[TipoFuente, str | None, float]:
    """Determina (tipo_fuente, dominio_fuente, calidad_fuente) para una marca con aparición.

    Reglas:
    1. Si hay desconocimiento explícito o la ejecución no tiene fuentes citadas -> ('Sin fuente', None, 0.2).
    2. Si el dominio propio de la marca está entre las fuentes citadas -> ('Web propia', dominio, 0.7).
    3. Si el fragmento tiene marca de cita [k] (1 <= k <= len(fuentes)), usa fuentes[k-1].
    4. En caso contrario, usa el primer dominio citado (regla de mayor acierto empírico frente a muestra).
    """
    if desconocimiento or not fuentes_ejecucion:
        return ("Sin fuente", None, SOURCE_QUALITY_BY_TYPE["Sin fuente"])

    fuentes_list = [f.strip().lower() for f in fuentes_ejecucion if f.strip()]
    if not fuentes_list:
        return ("Sin fuente", None, SOURCE_QUALITY_BY_TYPE["Sin fuente"])

    dom_propio = marca.dominio.lower()
    if dom_propio in fuentes_list:
        tipo, cal = catalogo.get(dom_propio, ("Web propia", SOURCE_QUALITY_BY_TYPE["Web propia"]))
        return (tipo, dom_propio, cal)

    chosen_dom: str | None = None
    if fragmento:
        cites = [int(x) for x in re.findall(r"\[(\d+)\]", fragmento)]
        for idx in cites:
            if 1 <= idx <= len(fuentes_list):
                chosen_dom = fuentes_list[idx - 1]
                break

    if chosen_dom is None:
        chosen_dom = fuentes_list[0]

    if chosen_dom in catalogo:
        tipo, cal = catalogo[chosen_dom]
        return (tipo, chosen_dom, cal)
    return ("Sin fuente", chosen_dom, SOURCE_QUALITY_BY_TYPE["Sin fuente"])


def judge_brand_mention(
    aparece: int,
    posicion: int | None,
    fragmento: str | None,
    marca: Marca,
    fuentes_ejecucion: Sequence[str],
    catalogo: dict[str, tuple[TipoFuente, float]],
) -> tuple[
    TipoMencion | None,
    int,
    Sentimiento | None,
    TipoFuente | None,
    str | None,
    float | None,
    bool,
]:
    """Evalúa por reglas una mención individual y devuelve sus atributos de Evaluacion."""
    if not aparece:
        return (None, 0, None, None, None, None, False)

    frag_text = fragmento or ""
    frag_norm = normalize(frag_text)

    # Regla 2: Desconocimiento en el fragmento -> Pasiva, 1, neutro, Sin fuente
    if any(pat in frag_norm for pat in DESCONOCIMIENTO):
        return (
            "Pasiva",
            1,
            "neutro",
            "Sin fuente",
            None,
            SOURCE_QUALITY_BY_TYPE["Sin fuente"],
            True,
        )

    # Regla 3: Negativo en el fragmento -> fuerza -1, negativo, Comparación neutra
    if any(pat in frag_norm for pat in NEGATIVO):
        tipo_f, dom_f, cal_f = assign_source_for_brand(
            marca, fuentes_ejecucion, catalogo, fragmento=frag_text, desconocimiento=False
        )
        return ("Comparación neutra", -1, "negativo", tipo_f, dom_f, cal_f, False)

    # Regla 4: FUERZA_3 en el fragmento -> Recomendación activa, 3, positivo
    if any(pat in frag_norm for pat in FUERZA_3):
        tipo_f, dom_f, cal_f = assign_source_for_brand(
            marca, fuentes_ejecucion, catalogo, fragmento=frag_text, desconocimiento=False
        )
        return ("Recomendación activa", 3, "positivo", tipo_f, dom_f, cal_f, False)

    # Regla 5: FUERZA_2 en el fragmento -> Comparación neutra, 2, positivo
    if any(pat in frag_norm for pat in FUERZA_2):
        tipo_f, dom_f, cal_f = assign_source_for_brand(
            marca, fuentes_ejecucion, catalogo, fragmento=frag_text, desconocimiento=False
        )
        return ("Comparación neutra", 2, "positivo", tipo_f, dom_f, cal_f, False)

    # Regla 6: Resto -> fuerza 1, neutro; Pasiva si fragmento corto o posicion >= 4
    stripped_frag = _strip_brand_from_fragment(frag_text, marca)
    is_pasiva = (posicion is not None and int(posicion) >= 4) or (
        len(stripped_frag) < PASIVA_MAX_CHARS
    )
    tipo_mencion: TipoMencion = "Pasiva" if is_pasiva else "Comparación neutra"
    tipo_f, dom_f, cal_f = assign_source_for_brand(
        marca, fuentes_ejecucion, catalogo, fragmento=frag_text, desconocimiento=False
    )
    return (tipo_mencion, 1, "neutro", tipo_f, dom_f, cal_f, False)


def judge_rules(
    df_detection: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
    catalogo: dict[str, tuple[TipoFuente, float]],
) -> pd.DataFrame:
    """Evalúa todas las filas de df_detection mediante el juez por reglas y devuelve un DataFrame en el esquema Evaluacion."""
    marca_map: dict[str, Marca] = {m.nombre: m for m in marcas}

    if isinstance(ejecuciones, pd.DataFrame):
        fuentes_by_ej: dict[str, list[str]] = {
            str(r["ejecucion_id"]): list(r["fuentes"])
            for r in ejecuciones[["ejecucion_id", "fuentes"]].to_dict(orient="records")
        }
    else:
        fuentes_by_ej = {ej.ejecucion_id: list(ej.fuentes) for ej in ejecuciones}

    rows: list[dict[str, object]] = []
    for det_row in df_detection.to_dict(orient="records"):
        ej_id = str(det_row["ejecucion_id"])
        nombre_marca = str(det_row["marca"])
        aparece = int(det_row["aparece"])
        raw_pos = det_row.get("posicion")
        posicion = None if pd.isna(raw_pos) else int(raw_pos)
        peso_posicion = int(det_row["peso_posicion"])
        raw_frag = det_row.get("fragmento")
        fragmento = None if pd.isna(raw_frag) else str(raw_frag)

        marca_obj = marca_map[nombre_marca]
        fuentes_ej = fuentes_by_ej.get(ej_id, [])

        (
            tipo_mencion,
            fuerza,
            sentimiento,
            tipo_fuente,
            dominio_fuente,
            calidad_fuente,
            desconocimiento,
        ) = judge_brand_mention(
            aparece=aparece,
            posicion=posicion,
            fragmento=fragmento,
            marca=marca_obj,
            fuentes_ejecucion=fuentes_ej,
            catalogo=catalogo,
        )

        eval_obj = Evaluacion(
            ejecucion_id=ej_id,
            marca=nombre_marca,
            aparece=aparece,
            posicion=posicion,
            peso_posicion=peso_posicion,
            tipo_mencion=tipo_mencion,
            fuerza=fuerza,
            sentimiento=sentimiento,
            tipo_fuente=tipo_fuente,
            dominio_fuente=dominio_fuente,
            calidad_fuente=calidad_fuente,
            desconocimiento=desconocimiento,
            fragmento=fragmento,
            juez="reglas",
            confianza_juez=1.0,
            discrepancia=False,
        )
        rows.append(eval_obj.model_dump())

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out["posicion"] = df_out["posicion"].astype(object).where(df_out["posicion"].notna(), None)
    return df_out
