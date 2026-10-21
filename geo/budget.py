"""Cálculo de costes y validación de restricciones presupuestarias, dependencias y capacidad (F9)."""

from typing import Literal, Sequence
import pandas as pd

from geo.config import ACTION_LIBRARY, CLIENT_WEEKLY_HOURS_CAPACITY
from geo.schemas import Accion, FasePlan, FichaMarca, Hallazgo, Plan, Talla

_TALLA_SCORE: dict[Talla, int] = {"S": 1, "M": 2, "L": 3}

# Semanas de cada fase del plan. Nombre y objetivo salen del perfil de sector (`geo.sectors`).
_PHASE_WEEKS: dict[int, tuple[int, int]] = {0: (1, 4), 1: (5, 10), 2: (11, 36), 3: (12, 48)}


def cost_from_tier(
    rango: tuple[float, float],
    tier: Literal["bajo", "medio", "alto"] = "medio",
) -> float:
    """Calcula en código el coste en euros a partir del rango de la plantilla y del nivel elegido."""
    low, high = float(rango[0]), float(rango[1])
    if tier == "bajo":
        return round(low, 2)
    if tier == "alto":
        return round(high, 2)
    return round((low + high) / 2.0, 2)


def get_template_hours_map() -> dict[str, float]:
    """Devuelve un mapa (titulo -> horas_cliente_semana) a partir de ACTION_LIBRARY."""
    return {
        str(tpl["titulo"]): float(tpl.get("horas_cliente_semana", 2.0))  # type: ignore[arg-type]
        for tpl in ACTION_LIBRARY
    }


def action_roi_ratio(accion: Accion) -> float:
    """Calcula la relación impacto / esfuerzo de una acción (mayor = más prioritaria al ajustar presupuesto)."""
    imp = _TALLA_SCORE.get(accion.impacto, 2)
    esf = _TALLA_SCORE.get(accion.esfuerzo, 2)
    return imp / esf


def has_dependency_cycles(acciones: Sequence[Accion]) -> bool:
    """Detecta si existe algún ciclo en el grafo de dependencias de `acciones` mediante DFS."""
    valid_ids = {a.id for a in acciones}
    adj: dict[str, list[str]] = {
        a.id: [d for d in a.dependencias if d in valid_ids] for a in acciones
    }
    state: dict[str, int] = {aid: 0 for aid in valid_ids}  # 0=unvisited, 1=visiting, 2=visited

    def _dfs(node: str) -> bool:
        state[node] = 1
        for dep in adj.get(node, []):
            if state.get(dep, 0) == 1:
                return True
            if state.get(dep, 0) == 0 and _dfs(dep):
                return True
        state[node] = 2
        return False

    for aid in valid_ids:
        if state[aid] == 0 and _dfs(aid):
            return True
    return False


def enforce_dependency_schedule(acciones: list[Accion]) -> list[Accion]:
    """Garantiza que no haya ciclos y que toda acción comience después del fin de sus dependencias."""
    by_id: dict[str, Accion] = {a.id: a for a in acciones}
    for a in acciones:
        a.dependencias = [d for d in a.dependencias if d in by_id and d != a.id]

    # Si hubiera algún ciclo accidental, limpiar la arista de retroceso
    if has_dependency_cycles(acciones):
        order_idx = {a.id: idx for idx, a in enumerate(acciones)}
        for a in acciones:
            a.dependencias = [
                d for d in a.dependencias if order_idx[d] < order_idx[a.id]
            ]

    # Propagar semana_inicio >= max(fin de dependencias)
    for _ in range(len(acciones) + 1):
        changed = False
        for a in acciones:
            if not a.dependencias:
                continue
            min_start = max(
                by_id[dep].semana_inicio + by_id[dep].plazo_semanas
                for dep in a.dependencias
                if dep in by_id
            )
            if a.semana_inicio < min_start:
                a.semana_inicio = min(min_start, max(1, 52 - a.plazo_semanas))
                changed = True
        if not changed:
            break

    return acciones


def compute_weekly_client_hours(
    acciones: Sequence[Accion],
    hours_by_action_id: dict[str, float] | None = None,
) -> dict[int, float]:
    """Calcula las horas semanales requeridas del equipo del cliente entre las semanas 1 y 52."""
    weekly: dict[int, float] = {w: 0.0 for w in range(1, 53)}
    for a in acciones:
        hrs = (
            hours_by_action_id.get(a.id, 2.0)
            if hours_by_action_id is not None
            else (2.5 if a.responsable.startswith("cliente_") else 1.5)
        )
        start_w = max(1, int(a.semana_inicio))
        end_w = min(52, start_w + max(1, int(a.plazo_semanas)) - 1)
        for w in range(start_w, end_w + 1):
            weekly[w] = round(weekly[w] + hrs, 2)
    return weekly


def enforce_client_capacity(
    acciones: list[Accion],
    hours_by_action_id: dict[str, float] | None = None,
    max_weekly_hours: float = CLIENT_WEEKLY_HOURS_CAPACITY,
) -> tuple[list[Accion], dict[int, float]]:
    """Desplaza `semana_inicio` si en alguna semana se supera la capacidad del equipo del cliente."""
    scheduled = enforce_dependency_schedule(acciones)
    weekly: dict[int, float] = {w: 0.0 for w in range(1, 53)}
    by_id = {a.id: a for a in scheduled}

    for a in scheduled:
        hrs = (
            hours_by_action_id.get(a.id, 2.0)
            if hours_by_action_id is not None
            else (2.5 if a.responsable.startswith("cliente_") else 1.5)
        )
        dep_end = (
            max(
                by_id[d].semana_inicio + by_id[d].plazo_semanas
                for d in a.dependencias
                if d in by_id
            )
            if a.dependencias
            else a.semana_inicio
        )
        cand_start = max(1, a.semana_inicio, dep_end)
        dur = max(1, a.plazo_semanas)

        while cand_start + dur - 1 < 52:
            weeks_span = range(cand_start, min(53, cand_start + dur))
            if all(weekly[w] + hrs <= max_weekly_hours for w in weeks_span):
                break
            cand_start += 1

        a.semana_inicio = cand_start
        for w in range(cand_start, min(53, cand_start + dur)):
            weekly[w] = round(weekly[w] + hrs, 2)

    scheduled = enforce_dependency_schedule(scheduled)
    final_weekly = compute_weekly_client_hours(scheduled, hours_by_action_id)
    return scheduled, final_weekly


def build_fases_from_acciones(
    acciones: Sequence[Accion], ficha: FichaMarca | None = None
) -> list[FasePlan]:
    """Reconstruye las 4 fases del plan (0, 1, 2, 3) con los IDs de las acciones activas."""
    from geo.sectors import action_context, phase_defs, select_profile

    ctx = action_context(ficha) if ficha is not None else {}
    defs = phase_defs(select_profile(ficha), ctx, _PHASE_WEEKS)
    fases: list[FasePlan] = []
    for num in (0, 1, 2, 3):
        nombre, semanas, objetivo = defs[num]
        act_ids = [a.id for a in acciones if a.fase_plan == num]
        fases.append(
            FasePlan(
                numero=num,  # type: ignore[arg-type]
                nombre=nombre,
                semanas=semanas,
                objetivo=objetivo,
                acciones=act_ids,
            )
        )
    return fases


def validate_and_adjust_plan(
    plan: Plan,
    ficha: FichaMarca,
    hallazgos: Sequence[Hallazgo],
    *,
    hours_by_action_id: dict[str, float] | None = None,
) -> Plan:
    """Valida y ajusta un Plan según las reglas de negocio de F9 (hallazgos, presupuesto, capacidad y ciclos)."""
    valid_h_ids = {h.id for h in hallazgos if h.aprobado}
    if not valid_h_ids:
        valid_h_ids = {h.id for h in hallazgos}

    # 1. Filtrar acciones sin hallazgo válido
    valid_acciones: list[Accion] = []
    for a in plan.acciones:
        rels = [hid for hid in a.hallazgos_relacionados if hid in valid_h_ids]
        if rels:
            a.hallazgos_relacionados = rels
            valid_acciones.append(a)

    # 2. Ajustar presupuesto si supera presupuesto_max_eur
    max_budget = ficha.presupuesto_max_eur or 27000.0
    min_budget = ficha.presupuesto_min_eur or 18000.0

    # Ordenar candidatas a recorte de menor a mayor ratio impacto/esfuerzo (protegiendo medición trimestral)
    while sum(a.coste_estimado_eur for a in valid_acciones) > max_budget and len(valid_acciones) > 6:
        # Contar cuántas acciones cubren cada hallazgo para no dejar ningún hallazgo huérfano si es posible
        h_counts: dict[str, int] = {}
        for a in valid_acciones:
            for hid in a.hallazgos_relacionados:
                h_counts[hid] = h_counts.get(hid, 0) + 1

        removable = [
            a
            for a in valid_acciones
            if a.palanca != "medicion"
            and all(h_counts.get(hid, 0) > 1 for hid in a.hallazgos_relacionados)
        ]
        if not removable:
            removable = [a for a in valid_acciones if a.palanca != "medicion"]
        if not removable:
            break

        removable.sort(
            key=lambda x: (action_roi_ratio(x), -x.coste_estimado_eur)
        )
        to_remove = removable[0]
        valid_acciones = [a for a in valid_acciones if a.id != to_remove.id]

    # Si tras recortar acciones aún supera max_budget, ajustar proporcionalmente al tope
    total_raw = sum(a.coste_estimado_eur for a in valid_acciones)
    if total_raw > max_budget and total_raw > 0:
        factor = max_budget / total_raw
        for a in valid_acciones:
            a.coste_estimado_eur = round(a.coste_estimado_eur * factor, 2)

    # 3. Renumerar IDs o mantener consistencia de dependencias, aplicar capacidad y calendario
    valid_acciones, _ = enforce_client_capacity(
        valid_acciones,
        hours_by_action_id=hours_by_action_id,
        max_weekly_hours=CLIENT_WEEKLY_HOURS_CAPACITY,
    )

    coste_total = round(sum(a.coste_estimado_eur for a in valid_acciones), 2)
    supuestos = list(plan.supuestos)
    if coste_total < min_budget:
        aviso_min = (
            f"Nota presupuestaria: el coste estimado ({coste_total:,.0f} €) queda por debajo "
            f"del rango mínimo orientativo del brief ({min_budget:,.0f} €)."
        )
        if aviso_min not in supuestos:
            supuestos.append(aviso_min)

    fases = build_fases_from_acciones(valid_acciones, ficha)

    return Plan(
        objetivos=plan.objetivos,
        fases=fases,
        acciones=valid_acciones,
        coste_total_eur=coste_total,
        medicion=plan.medicion,
        riesgos=plan.riesgos,
        supuestos=supuestos,
    )


def effort_impact_matrix(plan: Plan) -> pd.DataFrame:
    """Genera un DataFrame para la matriz Esfuerzo vs Impacto de la página 5 de la UI."""
    rows = []
    for a in plan.acciones:
        rows.append(
            {
                "id": a.id,
                "titulo": a.titulo,
                "palanca": a.palanca,
                "fase_plan": a.fase_plan,
                "esfuerzo": a.esfuerzo,
                "impacto": a.impacto,
                "esfuerzo_num": _TALLA_SCORE[a.esfuerzo],
                "impacto_num": _TALLA_SCORE[a.impacto],
                "coste_estimado_eur": a.coste_estimado_eur,
                "responsable": a.responsable,
                "hallazgos": ", ".join(a.hallazgos_relacionados),
            }
        )
    return pd.DataFrame(rows)
