"""Router `results` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.get("/projects/{id}/market", summary='Competencia (ContrasteMercado)')
def get_projects_id_market() -> None:
    not_implemented()


@router.put("/projects/{id}/market", summary='Guarda la competencia')
def put_projects_id_market() -> None:
    not_implemented()


@router.get("/projects/{id}/findings", summary='Hallazgos')
def get_projects_id_findings() -> None:
    not_implemented()


@router.patch("/projects/{id}/findings/{hid}", summary='Aprobar, descartar o editar título')
def patch_projects_id_findings_hid() -> None:
    not_implemented()


@router.get("/projects/{id}/plan", summary='Plan')
def get_projects_id_plan() -> None:
    not_implemented()


@router.put("/projects/{id}/plan", summary='Guarda el plan; devuelve el plan revalidado con avisos')
def put_projects_id_plan() -> None:
    not_implemented()


@router.post("/projects/{id}/plan/simulate", summary='Simulador de escenarios')
def post_projects_id_plan_simulate() -> None:
    not_implemented()


@router.get("/projects/{id}/diagnosis", summary='Indicadores y gráficos agregados')
def get_projects_id_diagnosis() -> None:
    not_implemented()


@router.get("/projects/{id}/tables/{tid}", summary='Tabla T1-T12 en JSON')
def get_projects_id_tables_tid() -> None:
    not_implemented()


@router.get("/projects/{id}/executions", summary='Ejecuciones paginadas con filtros')
def get_projects_id_executions() -> None:
    not_implemented()


@router.get("/projects/{id}/executions/{eid}", summary='Detalle con evaluación por marca')
def get_projects_id_executions_eid() -> None:
    not_implemented()


@router.get("/projects/{id}/proposal", summary='Propuesta con etiquetas de origen')
def get_projects_id_proposal() -> None:
    not_implemented()


@router.post("/projects/{id}/proposal/regenerate", summary='Rehace redacción y revisión')
def post_projects_id_proposal_regenerate() -> None:
    not_implemented()


@router.get("/projects/{id}/quality", summary='Validación del juez, discrepancias y aprobaciones')
def get_projects_id_quality() -> None:
    not_implemented()


@router.post("/projects/{id}/quality/labels", summary='Etiquetas humanas de la muestra')
def post_projects_id_quality_labels() -> None:
    not_implemented()


@router.patch("/projects/{id}/quality/discrepancies/{eid}/{marca}", summary='Resuelve una discrepancia')
def patch_projects_id_quality_discrepancies_eid_marca() -> None:
    not_implemented()
