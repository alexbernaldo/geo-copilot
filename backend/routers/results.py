"""Router `results`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, status

from backend.api_models import (
    ContrasteMercado,
    ExecutionDetail,
    ExecutionPage,
    FindingPatch,
    Hallazgo,
    LabelsPayload,
    PlanResponse,
    Progress,
    Proposal,
    Quality,
    SimulateRequest,
    SimulateResult,
)
from backend.deps import get_runner, get_store
from backend.services import results
from backend.services.runner import JobRunner
from backend.services.store import ProjectStore

router = APIRouter()


@router.get("/projects/{id}/market", response_model=ContrasteMercado, summary="Competencia (ContrasteMercado)")
def get_projects_id_market(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_market(store, id)


@router.put("/projects/{id}/market", response_model=ContrasteMercado, summary="Guarda la competencia")
def put_projects_id_market(
    id: str,
    body: dict[str, Any],
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.put_market(store, id, body)


@router.get("/projects/{id}/findings", response_model=list[Hallazgo], summary="Hallazgos")
def get_projects_id_findings(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_findings(store, id)


@router.patch("/projects/{id}/findings/{hid}", response_model=Hallazgo, summary="Aprobar, descartar o editar título")
def patch_projects_id_findings_hid(
    id: str,
    hid: str,
    body: FindingPatch,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.patch_finding(store, id, hid, body.model_dump(exclude_unset=True))


@router.get("/projects/{id}/plan", response_model=PlanResponse, summary="Plan")
def get_projects_id_plan(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_plan(store, id)


@router.put("/projects/{id}/plan", response_model=PlanResponse, summary="Guarda el plan; devuelve el plan revalidado con avisos")
def put_projects_id_plan(
    id: str,
    body: dict[str, Any],
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.put_plan(store, id, body)


@router.post("/projects/{id}/plan/simulate", response_model=SimulateResult, summary="Simulador de escenarios")
def post_projects_id_plan_simulate(
    id: str,
    body: SimulateRequest,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.simulate_plan(store, id, body.model_dump())


@router.get("/projects/{id}/diagnosis", summary="Indicadores y gráficos agregados")
def get_projects_id_diagnosis(
    id: str,
    ambito: str = Query("espontanea", pattern="^(espontanea|asistida)$"),
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_diagnosis(store, id, ambito)


@router.get("/projects/{id}/tables/{tid}", summary="Tabla T1-T12 en JSON")
def get_projects_id_tables_tid(
    id: str,
    tid: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_table(store, id, tid)


@router.get("/projects/{id}/executions", response_model=ExecutionPage, summary="Ejecuciones paginadas con filtros")
def get_projects_id_executions(
    id: str,
    motor: str | None = None,
    familia: str | None = None,
    intencion: str | None = None,
    ambito: str | None = None,
    marca: str | None = None,
    solo_con_marca: bool = False,
    fuente_tipo: str | None = None,
    fuera_de_territorio: bool | None = None,
    q: str | None = None,
    orden: str = "-fecha",
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(25, ge=1, le=100),
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.list_executions(
        store,
        id,
        motor=motor,
        familia=familia,
        intencion=intencion,
        ambito=ambito,
        marca=marca,
        solo_con_marca=solo_con_marca,
        fuente_tipo=fuente_tipo,
        fuera_de_territorio=fuera_de_territorio,
        q=q,
        orden=orden,
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.get("/projects/{id}/executions/{eid}", response_model=ExecutionDetail, summary="Detalle con evaluación por marca")
def get_projects_id_executions_eid(
    id: str,
    eid: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_execution(store, id, eid)


@router.get("/projects/{id}/proposal", response_model=Proposal, summary="Propuesta con etiquetas de origen")
def get_projects_id_proposal(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_proposal(store, id)


@router.post(
    "/projects/{id}/proposal/regenerate",
    response_model=Progress,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Rehace redacción y revisión",
)
def post_projects_id_proposal_regenerate(
    id: str,
    body: dict[str, Any] | None = None,
    runner: JobRunner = Depends(get_runner),
) -> Any:
    seccion = body.get("seccion") if body else None
    confirmo = bool(body.get("confirmo_coste", False)) if body else False
    return runner.launch(id, "regenerate", seccion=seccion, confirmo_coste=confirmo)


@router.get("/projects/{id}/quality", response_model=Quality, summary="Validación del juez, discrepancias y aprobaciones")
def get_projects_id_quality(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    return results.get_quality(store, id)


@router.post("/projects/{id}/quality/labels", response_model=Quality, summary="Etiquetas humanas de la muestra")
def post_projects_id_quality_labels(
    id: str,
    body: LabelsPayload,
    store: ProjectStore = Depends(get_store),
) -> Any:
    etiquetas = [e.model_dump() for e in body.etiquetas]
    return results.add_labels(store, id, etiquetas)


@router.patch("/projects/{id}/quality/discrepancies/{eid}/{marca}", response_model=Quality, summary="Resuelve una discrepancia")
def patch_projects_id_quality_discrepancies_eid_marca(
    id: str,
    eid: str,
    marca: str,
    body: dict[str, Any],
    store: ProjectStore = Depends(get_store),
) -> Any:
    valor = body.get("valor", body)
    return results.resolve_discrepancy(store, id, eid, marca, valor)
