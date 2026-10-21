"""Ensemble de juez por reglas + LLM y persistencia de evaluaciones (F4)."""

from pathlib import Path
from typing import Sequence
import pandas as pd

from geo.config import SOURCE_QUALITY_BY_TYPE
from geo.judge_llm import JUDGE_LAST_RUN, judge_llm
from geo.judge_rules import assign_source_for_brand, judge_rules
from geo.schemas import Ejecucion, Evaluacion, Marca, TipoFuente


def combine_rules_and_llm(
    df_rules: pd.DataFrame,
    df_llm: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
    catalogo: dict[str, tuple[TipoFuente, float]],
) -> pd.DataFrame:
    """Combina las evaluaciones del juez por reglas y del juez LLM en un único DataFrame ensemble.

    - Si reglas y LLM coinciden en `fuerza` -> `juez="ensemble"`, `confianza_juez=1.0`, `discrepancia=False`.
    - Si discrepan en `fuerza` -> prevalece el LLM, `juez="ensemble"`, `discrepancia=True`, `confianza_juez=0.6`.
    - `tipo_fuente` y `calidad_fuente` se determinan siempre por catálogo a partir de `dominio_fuente`.
    """
    marca_map: dict[str, Marca] = {m.nombre: m for m in marcas}
    if isinstance(ejecuciones, pd.DataFrame):
        fuentes_by_ej: dict[str, list[str]] = {
            str(r["ejecucion_id"]): list(r["fuentes"])
            for r in ejecuciones[["ejecucion_id", "fuentes"]].to_dict(orient="records")
        }
    else:
        fuentes_by_ej = {ej.ejecucion_id: list(ej.fuentes) for ej in ejecuciones}

    llm_lookup: dict[tuple[str, str], dict[str, object]] = {
        (str(r["ejecucion_id"]), str(r["marca"])): r
        for r in df_llm.to_dict(orient="records")
    }

    rows: list[dict[str, object]] = []
    for r_rule in df_rules.to_dict(orient="records"):
        key = (str(r_rule["ejecucion_id"]), str(r_rule["marca"]))
        r_llm = llm_lookup.get(key, r_rule)

        aparece = int(r_rule["aparece"])
        raw_pos = r_rule.get("posicion")
        posicion = None if pd.isna(raw_pos) else int(raw_pos)
        peso_posicion = int(r_rule["peso_posicion"])
        raw_frag = r_rule.get("fragmento")
        fragmento = None if pd.isna(raw_frag) else str(raw_frag)

        if aparece == 0:
            eval_obj = Evaluacion(
                ejecucion_id=key[0],
                marca=key[1],
                aparece=0,
                posicion=None,
                peso_posicion=0,
                tipo_mencion=None,
                fuerza=0,
                sentimiento=None,
                tipo_fuente=None,
                dominio_fuente=None,
                calidad_fuente=None,
                desconocimiento=False,
                fragmento=None,
                juez="ensemble",
                confianza_juez=1.0,
                discrepancia=False,
            )
            rows.append(eval_obj.model_dump())
            continue

        fuerza_rule = int(r_rule["fuerza"])
        fuerza_llm = int(r_llm["fuerza"])
        coinciden = fuerza_rule == fuerza_llm

        chosen = r_llm
        discrepancia = not coinciden
        confianza = 1.0 if coinciden else 0.6
        if coinciden and float(r_llm.get("confianza_juez", 1.0)) < 1.0:
            confianza = float(r_llm["confianza_juez"])

        desconocimiento = bool(chosen.get("desconocimiento", False))
        raw_dom = chosen.get("dominio_fuente")
        dom_fuente = None if (raw_dom is None or pd.isna(raw_dom)) else str(raw_dom).strip().lower()
        fuentes_ej = fuentes_by_ej.get(key[0], [])
        marca_obj = marca_map[key[1]]

        if desconocimiento or not fuentes_ej:
            tipo_fuente: TipoFuente = "Sin fuente"
            dom_fuente = None
            calidad_fuente = SOURCE_QUALITY_BY_TYPE["Sin fuente"]
        elif dom_fuente and dom_fuente in [f.lower() for f in fuentes_ej]:
            if dom_fuente == marca_obj.dominio.lower():
                tipo_fuente = "Web propia"
                calidad_fuente = SOURCE_QUALITY_BY_TYPE["Web propia"]
            elif dom_fuente in catalogo:
                tipo_fuente, calidad_fuente = catalogo[dom_fuente]
            else:
                tipo_fuente = "Sin fuente"
                calidad_fuente = SOURCE_QUALITY_BY_TYPE["Sin fuente"]
        else:
            tipo_fuente, dom_fuente, calidad_fuente = assign_source_for_brand(
                marca_obj,
                fuentes_ej,
                catalogo,
                fragmento=fragmento,
                desconocimiento=desconocimiento,
            )

        eval_obj = Evaluacion(
            ejecucion_id=key[0],
            marca=key[1],
            aparece=1,
            posicion=posicion,
            peso_posicion=peso_posicion,
            tipo_mencion=chosen["tipo_mencion"],  # type: ignore[arg-type]
            fuerza=fuerza_llm,
            sentimiento=chosen["sentimiento"],  # type: ignore[arg-type]
            tipo_fuente=tipo_fuente,
            dominio_fuente=dom_fuente,
            calidad_fuente=calidad_fuente,
            desconocimiento=desconocimiento,
            fragmento=fragmento,
            juez="ensemble",
            confianza_juez=confianza,
            discrepancia=discrepancia,
        )
        rows.append(eval_obj.model_dump())

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out["posicion"] = df_out["posicion"].astype(object).where(df_out["posicion"].notna(), None)
    return df_out


def judge_ensemble(
    df_detection: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
    catalogo: dict[str, tuple[TipoFuente, float]],
    *,
    provider: str | None = None,
    model: str | None = None,
    use_cache: bool = True,
    persist_path: Path | None = None,
    on_progress=None,
) -> pd.DataFrame:
    """Ejecuta el juez por reglas y el juez LLM, los combina en ensemble y opcionalmente persiste en Parquet."""
    df_rules = judge_rules(df_detection, ejecuciones, marcas, catalogo)
    df_llm = judge_llm(
        df_detection,
        ejecuciones,
        marcas,
        catalogo,
        provider=provider,
        model=model,
        use_cache=use_cache,
        on_progress=on_progress,
    )
    df_ens = combine_rules_and_llm(df_rules, df_llm, ejecuciones, marcas, catalogo)
    if persist_path is not None:
        persist_path.parent.mkdir(parents=True, exist_ok=True)
        df_ens.to_parquet(persist_path, index=False)
    return df_ens
