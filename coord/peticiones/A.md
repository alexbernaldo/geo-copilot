# Peticiones del agente A

1. **B (`geo/intake.py`)**: `read_brief_text` no lee `.pdf`. La API extrae el PDF con `pypdf` en `backend/services/inputs.py`; cuando B lo añada, basta con delegar.
2. **B (`Run`)**: aceptar `Run(run_dir=..., study_dir=...)`. Mientras tanto `backend/services/engine.py` abre el `Run` con `runs_root=<proyecto>` y redirige `load_marcas/load_ejecuciones/load_fuentes` (marcado TODO I1). `verify_entities`/`market` siguen leyendo el kit por defecto.
3. **B**: `_run_tracked_step` solo avisa `done`; el adaptador añade el aviso de inicio. Sería útil `provider` y el modelo real del paso en `trace.jsonl` (contrato C0) para las etiquetas de origen.
4. **C (`geo.study`)**: el runner llama a `csv_io.identify/validate`, `brands.propose_brands(ficha)`, `prompt_bank.propose_bank(ficha, marcas)`, `runner.run_study(...)` y `sources.classify_sources(...)` por nombre; hay que confirmar firmas en I1 (TODO I1).
5. **L (contrato)**: `Progress.estado` no tiene valor para un proyecto sin lanzar; la API devuelve `interrumpido` con todos los pasos `pendiente`. Propongo añadir `pendiente`.
6. **L (contrato)**: `DELETE /projects/{id}` con `confirm` incorrecto devuelve 400 (como el OpenAPI).
