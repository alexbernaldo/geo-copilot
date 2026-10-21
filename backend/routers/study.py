"""Router `study` (stub de W0: devuelve 501 hasta que el agente A lo implemente)."""

from fastapi import APIRouter

from backend.routers import not_implemented

router = APIRouter()

@router.post("/projects/{id}/study/upload", summary='Sube CSV (varios); informe de validación por archivo')
def post_projects_id_study_upload() -> None:
    not_implemented()


@router.get("/projects/{id}/study/summary", summary='Resumen del estudio cargado o generado')
def get_projects_id_study_summary() -> None:
    not_implemented()


@router.post("/projects/{id}/study/brands/propose", summary='Propuesta de marcas (síncrono, timeout 90 s)')
def post_projects_id_study_brands_propose() -> None:
    not_implemented()


@router.put("/projects/{id}/study/brands", summary='Guarda las marcas editadas')
def put_projects_id_study_brands() -> None:
    not_implemented()


@router.get("/projects/{id}/study/brands", summary='Marcas del estudio')
def get_projects_id_study_brands() -> None:
    not_implemented()


@router.post("/projects/{id}/study/prompts/propose", summary='Propuesta de banco de prompts')
def post_projects_id_study_prompts_propose() -> None:
    not_implemented()


@router.put("/projects/{id}/study/prompts", summary='Guarda el banco editado')
def put_projects_id_study_prompts() -> None:
    not_implemented()


@router.get("/projects/{id}/study/prompts", summary='Banco de prompts del estudio')
def get_projects_id_study_prompts() -> None:
    not_implemented()


@router.get("/projects/{id}/study/prompts/instances", summary='Vista previa de la instanciación')
def get_projects_id_study_prompts_instances() -> None:
    not_implemented()


@router.put("/projects/{id}/study/config", summary='Tamaño, motores y repeticiones')
def put_projects_id_study_config() -> None:
    not_implemented()


@router.get("/projects/{id}/study/config", summary='Configuración del estudio')
def get_projects_id_study_config() -> None:
    not_implemented()
