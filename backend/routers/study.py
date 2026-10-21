"""Router `study`."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile

from backend.deps import get_store
from backend.errors import not_found, unprocessable
from backend.services import estimates, inputs, study_files as sf
from backend.services.store import ProjectStore

router = APIRouter()


@router.post("/projects/{id}/study/upload", summary="Sube CSV (varios); informe de validación por archivo")
async def post_projects_id_study_upload(
    id: str,
    archivos: list[UploadFile] = File(...),
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    files = []
    for a in archivos:
        data = await a.read()
        files.append((a.filename or "archivo.csv", data))
    res = inputs.upload_csvs(store, id, files)
    inputs.refresh_readiness(store, id)
    return res


@router.get("/projects/{id}/study/summary", summary="Resumen del estudio cargado o generado")
def get_projects_id_study_summary(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    if not all(sf.study_file(study, k).exists() for k in sf.REQUIRED):
        raise not_found("El resumen del estudio")
    return sf.study_summary(study)


@router.post("/projects/{id}/study/brands/propose", summary="Propuesta de marcas (síncrono, timeout 90 s)")
def post_projects_id_study_brands_propose(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    ficha = inputs.current_ficha(store, id)
    brief_text = inputs.read_brief(store, id)
    
    # Intenta usar geo.study.brands si está disponible
    try:
        from geo.study import brands as study_brands
        prop = study_brands.propose_brands(ficha, study_dir=study, brief_text=brief_text, write=True)
        marcas = [m.model_dump() for m in prop.marcas]
    except Exception:
        # En modo de referencia o fallback
        if inputs.is_reference(store, id) or (study / sf.KIT_MARKER).exists():
            marcas = sf.read_brands(study)
        else:
            marca_nom = ficha.marca if ficha else "Marca del proyecto"
            marcas = [
                {"nombre": marca_nom, "nivel": "foco", "rol": "marca_brief", "dominio": "example.com", "alias": [], "motivo": "Marca del brief", "fuente_url": "https://example.com"}
            ]
            sf.write_brands(study, marcas)
    return {"marcas": marcas}


@router.put("/projects/{id}/study/brands", summary="Guarda las marcas editadas")
def put_projects_id_study_brands(
    id: str,
    body: dict[str, Any],
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    marcas = body.get("marcas", [])
    ficha = inputs.current_ficha(store, id)
    marca_nom = ficha.marca if ficha else None
    decl = list(ficha.competidores_declarados or []) if ficha else []
    probs = sf.validate_brands(marcas, marca_nom, decl)
    if probs:
        raise unprocessable("marcas_invalidas", "; ".join(probs), {"errores": probs})
    study = store.study_dir(id)
    sf.write_brands(study, marcas)
    return {"marcas": marcas}


@router.get("/projects/{id}/study/brands", summary="Marcas del estudio")
def get_projects_id_study_brands(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    return {"marcas": sf.read_brands(study)}


@router.post("/projects/{id}/study/prompts/propose", summary="Propuesta de banco de prompts")
def post_projects_id_study_prompts_propose(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    ficha = inputs.current_ficha(store, id)
    brief_text = inputs.read_brief(store, id)
    marcas = sf.read_brands(study)
    
    try:
        from geo.study import prompt_bank
        prop = prompt_bank.propose_bank(ficha, marcas, study_dir=study, brief_text=brief_text, write=True)
        prompts = [p.model_dump() for p in prop.prompts]
    except Exception:
        if inputs.is_reference(store, id) or (study / sf.KIT_MARKER).exists():
            prompts = sf.read_prompts(study)
        else:
            prompts = sf.read_prompts(study)
    return {"prompts": prompts}


@router.put("/projects/{id}/study/prompts", summary="Guarda el banco editado")
def put_projects_id_study_prompts(
    id: str,
    body: dict[str, Any],
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    prompts = body.get("prompts", [])
    study = store.study_dir(id)
    marcas_objs = sf.read_brands(study)
    marcas_names = [m["nombre"] for m in marcas_objs]
    probs = sf.validate_prompts(prompts, marcas_names)
    if probs:
        raise unprocessable("prompts_invalidos", "; ".join(probs), {"errores": probs})
    ficha = inputs.current_ficha(store, id)
    sector = ficha.sector if ficha else ""
    sf.write_prompts(study, prompts, sector=sector)
    return {"prompts": prompts}


@router.get("/projects/{id}/study/prompts", summary="Banco de prompts del estudio")
def get_projects_id_study_prompts(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    return {"prompts": sf.read_prompts(study)}


@router.get("/projects/{id}/study/prompts/instances", summary="Vista previa de la instanciación")
def get_projects_id_study_prompts_instances(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    instances = estimates.study_instances(store, id)
    return {"instancias": instances}


@router.put("/projects/{id}/study/config", summary="Tamaño, motores y repeticiones")
def put_projects_id_study_config(
    id: str,
    body: dict[str, Any],
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    sf.write_config(study, body)
    inputs.refresh_readiness(store, id)
    return sf.read_config(study)


@router.get("/projects/{id}/study/config", summary="Configuración del estudio")
def get_projects_id_study_config(
    id: str,
    store: ProjectStore = Depends(get_store),
) -> Any:
    store.require(id)
    study = store.study_dir(id)
    return sf.read_config(study)
