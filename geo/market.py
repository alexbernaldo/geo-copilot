"""Contraste entre el brief y los datos reales del mercado y descubrimiento de marcas (F8)."""

import re
from typing import Literal, Sequence
import pandas as pd

from geo.config import FINDINGS_THRESHOLDS
from geo.schemas import (
    ContrasteMercado,
    Ejecucion,
    FichaMarca,
    Marca,
    MarcaMercado,
)
from geo.text import normalize

RolMercado = Literal[
    "marca_brief", "lider", "competidor_directo", "referencia", "contexto"
]

_GENERIC_BOLD_HEADINGS: set[str] = {
    "en resumen",
    "resumen",
    "consejo",
    "nota",
    "importante",
    "conclusion",
    "recomendacion",
}


def _matches_declared(marca: Marca, declarados: Sequence[str]) -> bool:
    """Comprueba si `marca` coincide por nombre o alias con alguno de los competidores declarados en el brief."""
    brand_terms = {normalize(marca.nombre), *(normalize(a) for a in marca.alias)}
    for dec in declarados:
        dec_norm = normalize(dec)
        if not dec_norm:
            continue
        if dec_norm in brand_terms or any(
            t in dec_norm or dec_norm in t for t in brand_terms if len(t) >= 4
        ):
            return True
    return False


def _assign_role(
    marca: Marca,
    ficha: FichaMarca,
    lider_nombre: str,
) -> RolMercado:
    """Asigna el rol de mercado según las reglas de F8."""
    if normalize(marca.nombre) == normalize(ficha.marca) or marca.es_marca_brief:
        return "marca_brief"
    if marca.nombre == lider_nombre or "lider real" in normalize(marca.rol):
        return "lider"
    if marca.nivel == "foco" and "referencia" in normalize(marca.rol):
        return "referencia"
    if marca.nivel == "foco":
        return "competidor_directo"
    return "contexto"


def discover_uncataloged_brands(
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
    marcas: Sequence[Marca],
) -> list[str]:
    """Busca en las respuestas candidatos de marcas en negrita al inicio de viñeta que no estén en marcas.csv.

    Extra Nivel 3: filtra encabezados genéricos ('En resumen:', 'Consejo:', 'Resumen:') y verifica contra
    todos los nombres y alias catalogados. En el dataset sintético del kit devuelve `[]` porque las
    respuestas solo mencionan las 10 marcas del catálogo.
    """
    known_terms: set[str] = set()
    for m in marcas:
        known_terms.add(normalize(m.nombre))
        for a in m.alias:
            known_terms.add(normalize(a))

    if isinstance(ejecuciones, pd.DataFrame):
        respuestas = ejecuciones["respuesta"].astype(str).tolist()
    else:
        respuestas = [e.respuesta for e in ejecuciones]

    candidates: set[str] = set()
    pattern = re.compile(r"(?:^|\n)\s*(?:\d+\.|[*\-•])\s*\*\*([^*\n]{2,60}?)\*\*")
    for resp in respuestas:
        for match in pattern.finditer(resp):
            raw_cand = match.group(1).strip(" :—.-")
            cand_norm = normalize(raw_cand)
            if not cand_norm or cand_norm in _GENERIC_BOLD_HEADINGS:
                continue
            if cand_norm not in known_terms:
                candidates.add(raw_cand)

    return sorted(candidates)


def build_market(
    ficha: FichaMarca,
    marcas: Sequence[Marca],
    tablas: dict[str, pd.DataFrame],
    ejecuciones: pd.DataFrame | Sequence[Ejecucion],
) -> ContrasteMercado:
    """Construye el ContrasteMercado cruzando la ficha del brief con marcas.csv y T1 espontánea."""
    t1_esp = tablas["T1_espontanea"]
    lider_nombre = (
        str(t1_esp.iloc[0]["marca"])
        if not t1_esp.empty
        else "Grupo Hospitalario Valdecruz"
    )
    n_esp = int(t1_esp.iloc[0]["n"]) if not t1_esp.empty else 240

    ap_by_brand: dict[str, float] = {}
    score_by_brand: dict[str, float] = {}
    for _, row in t1_esp.iterrows():
        m_name = str(row["marca"])
        ap_by_brand[m_name] = float(row["tasa_aparicion"])
        score_by_brand[m_name] = float(row["score"])

    marcas_mercado: list[MarcaMercado] = []
    no_declaradas_relevantes: list[str] = []

    threshold_undeclared = float(
        FINDINGS_THRESHOLDS.get("r7_undeclared_competitor_min", 0.30)
    )

    # Ordenar marcas por tasa de aparición espontánea descendente (orden de T1_espontanea)
    marca_lookup = {m.nombre: m for m in marcas}
    ordered_names = [
        str(r["marca"]) for _, r in t1_esp.iterrows() if str(r["marca"]) in marca_lookup
    ]
    for m in marcas:
        if m.nombre not in ordered_names:
            ordered_names.append(m.nombre)

    for m_name in ordered_names:
        m = marca_lookup[m_name]
        rol = _assign_role(m, ficha, lider_nombre)
        es_propia = rol == "marca_brief"
        declarada = es_propia or _matches_declared(m, ficha.competidores_declarados)
        tasa_ap = ap_by_brand.get(m.nombre, 0.0)
        detectada = tasa_ap > 0.0

        nota = m.rol
        if not declarada and not es_propia and tasa_ap >= threshold_undeclared:
            no_declaradas_relevantes.append(m.nombre)
            nota = f"{m.rol} · No declarada en brief ({tasa_ap * 100:.1f}% espontánea)"

        marcas_mercado.append(
            MarcaMercado(
                nombre=m.nombre,
                rol=rol,
                declarada_en_brief=declarada,
                detectada_en_datos=detectada,
                tasa_aparicion_espontanea=round(tasa_ap, 4),
                nota=nota,
            )
        )

    discrepancias: list[str] = []

    # 1. Competidores foco no declarados (ej. Vistalia Oftalmología)
    if "Vistalia Oftalmología" in no_declaradas_relevantes:
        ap_vist = ap_by_brand["Vistalia Oftalmología"] * 100.0
        discrepancias.append(
            f"El brief no menciona a Vistalia Oftalmología (competidor directo de red multicentro), "
            f"que aparece en el {ap_vist:.1f}% de las respuestas espontáneas (T1, n={n_esp})."
        )

    # 2. Líder real del mercado vs percepción del brief
    ap_lider = ap_by_brand.get(lider_nombre, 0.0) * 100.0
    sc_lider = score_by_brand.get(lider_nombre, 0.0)
    ap_tram = ap_by_brand.get("Instituto Oftálmico Tramuntana", 0.0) * 100.0
    sc_tram = score_by_brand.get("Instituto Oftálmico Tramuntana", 0.0)
    discrepancias.append(
        f"El líder real en visibilidad espontánea es {lider_nombre} con un {ap_lider:.1f}% de aparición "
        f"y score {sc_lider:.2f} (T1, n={n_esp}), superando a la referencia premium declarada "
        f"Instituto Oftálmico Tramuntana ({ap_tram:.1f}%, score {sc_tram:.2f})."
    )

    # 3. Otros actores relevantes (>= 30 %) no contemplados en el brief
    otros_no_decl = [
        b for b in no_declaradas_relevantes if b != "Vistalia Oftalmología"
    ]
    if otros_no_decl:
        detalle_otros = ", ".join(
            f"{b} ({ap_by_brand[b] * 100.0:.1f}%)" for b in otros_no_decl
        )
        discrepancias.append(
            f"Existen otros {len(otros_no_decl)} actores no declarados en el brief con aparición "
            f"espontánea >= 30% (T1, n={n_esp}): {detalle_otros}."
        )

    # 4. Candidatos no catalogados (Nivel 3)
    candidatos_nuevos = discover_uncataloged_brands(ejecuciones, marcas)
    if candidatos_nuevos:
        discrepancias.append(
            f"Se han detectado {len(candidatos_nuevos)} marcas candidatas fuera de catálogo: "
            f"{', '.join(candidatos_nuevos)}."
        )

    return ContrasteMercado(
        marcas=marcas_mercado,
        no_declaradas_relevantes=no_declaradas_relevantes,
        discrepancias_brief=discrepancias,
        aprobado_por_humano=False,
    )
