"""Juez basado en LLM con validación de esquemas y garantías por código (F4)."""

import json
from typing import Optional, Sequence
import pandas as pd
from pydantic import BaseModel, Field

from geo.config import PROMPTS_DIR, SOURCE_QUALITY_BY_TYPE
from geo.judge_rules import assign_source_for_brand, judge_brand_mention
from geo.llm import complete_json, estimate_cost
from geo.schemas import (
    Ejecucion,
    Evaluacion,
    Marca,
    Sentimiento,
    TipoFuente,
    TipoMencion,
)
from geo.text import normalize

# Las 3 ejecuciones usadas como few-shot en judge_v1.md (se excluyen al validar el juez LLM/ensemble)
FEW_SHOT_EJECUCION_IDS: set[str] = {"EJ-0502", "EJ-0565", "EJ-0624"}


class JuicioMarca(BaseModel):
    """Juicio individual de una marca que aparece en una ejecución."""

    marca: str
    tipo_mencion: TipoMencion
    fuerza: int = Field(ge=-1, le=3)
    sentimiento: Sentimiento
    desconocimiento: bool = False
    dominio_fuente: Optional[str] = None
    cita_textual: str = ""


class JuicioEjecucion(BaseModel):
    """Lista de juicios de todas las marcas detectadas en una ejecución."""

    juicios: list[JuicioMarca]


def _load_judge_prompt() -> str:
    """Lee el prompt de sistema versionado judge_v1.md."""
    path = PROMPTS_DIR / "judge_v1.md"
    return path.read_text(encoding="utf-8")


def estimate_judge_llm_workload(
    df_detection: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
) -> dict[str, float | int]:
    """Calcula cuántas llamadas LLM requerirá evaluar df_detection y estima tokens y coste."""
    present_ej_ids = set(
        df_detection.loc[df_detection["aparece"] == 1, "ejecucion_id"].astype(str).unique()
    )
    n_calls = len(present_ej_ids)
    # Estimación media conservadora: ~850 tokens de entrada (system + respuesta) y ~180 de salida por ejecución
    tok_in = n_calls * 850
    tok_out = n_calls * 180
    cost = estimate_cost(n_calls, tok_in, tok_out)
    return {
        "n_calls": n_calls,
        "tokens_in_est": tok_in,
        "tokens_out_est": tok_out,
        "cost_est_eur": round(cost, 4),
    }


def judge_llm(
    df_detection: pd.DataFrame,
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
    catalogo: dict[str, tuple[TipoFuente, float]],
    *,
    provider: str | None = None,
    model: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Evalúa las menciones mediante el juez LLM (1 llamada por ejecución con marcas detectadas).

    Aplica las validaciones de código de F4:
    - Las marcas deben ser exactamente las detectadas por F2 (las que sobran se descartan, las que faltan se rellenan con reglas).
    - `cita_textual` debe existir en la respuesta (substring normalizado); si no existe, baja `confianza_juez` a 0.75.
    - `dominio_fuente` debe estar entre las fuentes citadas; si no, `None`.
    - `tipo_fuente` y `calidad_fuente` se asignan siempre desde el catálogo.
    """
    system_prompt = _load_judge_prompt()
    marca_map: dict[str, Marca] = {m.nombre: m for m in marcas}

    if isinstance(ejecuciones, pd.DataFrame):
        ej_Lookup: dict[str, dict[str, object]] = {
            str(r["ejecucion_id"]): {
                "respuesta": str(r["respuesta"]),
                "fuentes": list(r["fuentes"]),
            }
            for r in ejecuciones[["ejecucion_id", "respuesta", "fuentes"]].to_dict(
                orient="records"
            )
        }
    else:
        ej_Lookup = {
            ej.ejecucion_id: {
                "respuesta": ej.respuesta,
                "fuentes": list(ej.fuentes),
            }
            for ej in ejecuciones
        }

    # Agrupar filas detectadas por ejecución para hacer a lo sumo 1 llamada por ejecución
    rows_by_ej: dict[str, list[dict[str, object]]] = {}
    for det_row in df_detection.to_dict(orient="records"):
        ej_id = str(det_row["ejecucion_id"])
        rows_by_ej.setdefault(ej_id, []).append(det_row)

    out_rows: list[dict[str, object]] = []

    for ej_id, det_rows in rows_by_ej.items():
        ej_info = ej_Lookup[ej_id]
        respuesta = str(ej_info["respuesta"])
        fuentes_ej: list[str] = [str(f).strip().lower() for f in ej_info["fuentes"]]  # type: ignore[union-attr]
        resp_norm = normalize(respuesta)

        present_rows = [r for r in det_rows if int(r["aparece"]) == 1]
        juicios_map: dict[str, JuicioMarca] = {}

        if present_rows:
            payload_datos = {
                "ejecucion_id": ej_id,
                "marcas_detectadas": [
                    {
                        "marca": str(r["marca"]),
                        "posicion": int(r["posicion"]) if pd.notna(r.get("posicion")) else 1,
                        "dominio_propio": marca_map[str(r["marca"])].dominio,
                        "fragmento_detectado": str(r.get("fragmento") or ""),
                    }
                    for r in present_rows
                ],
                "fuentes_citadas": fuentes_ej,
                "respuesta": respuesta,
            }
            user_prompt = (
                "Evalúa las marcas detectadas en la siguiente ejecución y responde en JSON:\n"
                f"<datos>\n{json.dumps(payload_datos, ensure_ascii=False, indent=2)}\n</datos>"
            )

            def _mock_builder() -> JuicioEjecucion:
                mock_items: list[JuicioMarca] = []
                for r in present_rows:
                    m_name = str(r["marca"])
                    pos = int(r["posicion"]) if pd.notna(r.get("posicion")) else 1
                    frag = None if pd.isna(r.get("fragmento")) else str(r["fragmento"])
                    t_m, f_val, sent, _, dom_f, _, desc = judge_brand_mention(
                        1, pos, frag, marca_map[m_name], fuentes_ej, catalogo
                    )
                    cita = (frag or respuesta)[:200]
                    mock_items.append(
                        JuicioMarca(
                            marca=m_name,
                            tipo_mencion=t_m or "Comparación neutra",
                            fuerza=f_val if f_val != 0 else 1,
                            sentimiento=sent or "neutro",
                            desconocimiento=desc,
                            dominio_fuente=dom_f,
                            cita_textual=cita,
                        )
                    )
                return JuicioEjecucion(juicios=mock_items)

            juicio_ej = complete_json(
                system=system_prompt,
                user=user_prompt,
                schema=JuicioEjecucion,
                model=model,
                temperature=0.0,
                cache_key=f"judge_v1|{ej_id}|{[str(r['marca']) for r in present_rows]}",
                prompt_version="judge_v1",
                mock_builder=_mock_builder,
                provider=provider,
                use_cache=use_cache,
            )
            # Solo conservar las marcas que F2 detectó realmente
            valid_names = {str(r["marca"]) for r in present_rows}
            for j in juicio_ej.juicios:
                if j.marca in valid_names:
                    juicios_map[j.marca] = j

        # Construir filas Evaluacion para todas las marcas de esta ejecución
        for det_row in det_rows:
            nombre_marca = str(det_row["marca"])
            aparece = int(det_row["aparece"])
            raw_pos = det_row.get("posicion")
            posicion = None if pd.isna(raw_pos) else int(raw_pos)
            peso_posicion = int(det_row["peso_posicion"])
            raw_frag = det_row.get("fragmento")
            fragmento = None if pd.isna(raw_frag) else str(raw_frag)
            marca_obj = marca_map[nombre_marca]

            if aparece == 0:
                eval_obj = Evaluacion(
                    ejecucion_id=ej_id,
                    marca=nombre_marca,
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
                    juez="llm",
                    confianza_juez=1.0,
                    discrepancia=False,
                )
                out_rows.append(eval_obj.model_dump())
                continue

            if nombre_marca in juicios_map:
                jm = juicios_map[nombre_marca]
                fuerza = jm.fuerza if jm.fuerza != 0 else 1
                tipo_mencion: TipoMencion = jm.tipo_mencion
                sentimiento: Sentimiento = jm.sentimiento
                desconocimiento = bool(jm.desconocimiento)

                # Validar que cita_textual exista como substring normalizado en la respuesta
                cita_norm = normalize(jm.cita_textual)
                confianza = 1.0 if (cita_norm and cita_norm in resp_norm) else 0.75

                # Validar que dominio_fuente esté entre las fuentes citadas
                dom_cand = (jm.dominio_fuente or "").strip().lower() or None
                if dom_cand not in fuentes_ej or desconocimiento:
                    dom_cand = None

                if desconocimiento or not fuentes_ej:
                    tipo_fuente: TipoFuente = "Sin fuente"
                    dominio_fuente: str | None = None
                    calidad_fuente: float = SOURCE_QUALITY_BY_TYPE["Sin fuente"]
                elif dom_cand is not None:
                    dominio_fuente = dom_cand
                    if dom_cand == marca_obj.dominio.lower():
                        tipo_fuente = "Web propia"
                        calidad_fuente = SOURCE_QUALITY_BY_TYPE["Web propia"]
                    elif dom_cand in catalogo:
                        tipo_fuente, calidad_fuente = catalogo[dom_cand]
                    else:
                        tipo_fuente = "Sin fuente"
                        calidad_fuente = SOURCE_QUALITY_BY_TYPE["Sin fuente"]
                else:
                    tipo_fuente, dominio_fuente, calidad_fuente = assign_source_for_brand(
                        marca_obj,
                        fuentes_ej,
                        catalogo,
                        fragmento=fragmento,
                        desconocimiento=desconocimiento,
                    )

                eval_obj = Evaluacion(
                    ejecucion_id=ej_id,
                    marca=nombre_marca,
                    aparece=1,
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
                    juez="llm",
                    confianza_juez=confianza,
                    discrepancia=False,
                )
            else:
                # Si el LLM omitió una marca detectada por F2, rellenar con el juez de reglas
                (
                    t_m,
                    f_val,
                    sent_r,
                    t_f,
                    dom_f,
                    cal_f,
                    desc_r,
                ) = judge_brand_mention(
                    1, posicion, fragmento, marca_obj, fuentes_ej, catalogo
                )
                eval_obj = Evaluacion(
                    ejecucion_id=ej_id,
                    marca=nombre_marca,
                    aparece=1,
                    posicion=posicion,
                    peso_posicion=peso_posicion,
                    tipo_mencion=t_m,
                    fuerza=f_val,
                    sentimiento=sent_r,
                    tipo_fuente=t_f,
                    dominio_fuente=dom_f,
                    calidad_fuente=cal_f,
                    desconocimiento=desc_r,
                    fragmento=fragmento,
                    juez="reglas",
                    confianza_juez=0.8,
                    discrepancia=False,
                )

            out_rows.append(eval_obj.model_dump())

    df_out = pd.DataFrame(out_rows)
    if not df_out.empty:
        df_out["posicion"] = df_out["posicion"].astype(object).where(df_out["posicion"].notna(), None)
    return df_out
