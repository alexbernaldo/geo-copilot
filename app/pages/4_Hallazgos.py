"""Página 4: hallazgos priorizados con evidencias (punto de control 2)."""
from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import (
    checkpoint_summary,
    evidence_view,
    finding_header,
    get_active_run,
    page_header,
    panel,
)

run = get_active_run()
ficha = run.load_ficha()
hallazgos = run.load_hallazgos()

n_prob = sum(1 for h in hallazgos if not str(h.descripcion).upper().startswith("FORTALEZA"))
n_fort = len(hallazgos) - n_prob

page_header(
    "Hallazgos",
    f"{len(hallazgos)} hallazgos: {n_prob} problemas y {n_fort} fortaleza{'s' if n_fort != 1 else ''}. "
    "Revisa la evidencia de cada uno y decide cuáles entran en el plan.",
    checkpoint=2,
    step=4,
)

aprobados_map: dict[str, bool] = {}

with st.sidebar:
    hipotesis = getattr(ficha, "hipotesis_cliente", []) or []
    if hipotesis:
        st.markdown("**Hipótesis del cliente**")
        for hip in hipotesis:
            st.caption(f"«{hip}»")

for h in hallazgos:
    desc = str(h.descripcion)
    es_fortaleza = desc.upper().startswith("FORTALEZA:")
    if es_fortaleza:
        desc = desc.split(":", 1)[-1].strip() if ":" in desc else desc
        tipo = "Fortaleza"
    else:
        tipo = "Problema"
    ev_principal = h.evidencias[0] if h.evidencias else None
    if h.fase_embudo and len(h.evidencias) > 1:
        for ev in h.evidencias:
            if str(ev.metrica).lower().endswith(h.fase_embudo.lower()) or h.fase_embudo.lower() in str(ev.metrica).lower():
                ev_principal = ev
                break
    cifra = f"{ev_principal.valor}" if ev_principal else "-"
    origin = f"{ev_principal.tabla} · n = {ev_principal.n}" if ev_principal else "-"
    n = ev_principal.n if ev_principal else 0
    motores = ", ".join(h.motores) if h.motores else "Todos"
    fase = h.fase_embudo or "-"
    impacto_txt = h.impacto.capitalize() if hasattr(h, "impacto") else "Alto"
    confianza_txt = h.confianza.capitalize() if hasattr(h, "confianza") else "Alta"
    categoria = h.tipo.replace("_", " ").title() if hasattr(h, "tipo") else "Geografía"

    with st.container(border=True, key=f"finding_{h.id}"):
        finding_header(
            fid=h.id,
            tipo=tipo,
            categoria=categoria,
            titulo=h.titulo,
            cifra=cifra,
            origin=origin,
            n=n,
            fase=fase,
            motores=motores,
            impacto=impacto_txt,
            confianza=confianza_txt,
            descripcion=desc,
        )
        all_eids: list[str] = []
        for ev in h.evidencias:
            for eid in ev.ejecucion_ids:
                if eid not in all_eids:
                    all_eids.append(eid)
        evidence_view(all_eids, marca_resaltada=ficha.marca, title=f"Ver respuestas de evidencia de {h.id}", max_items=4)
        aprobados_map[h.id] = st.toggle("Incluir en el plan", value=bool(h.aprobado), key=f"chk_{h.id}")
    st.write("")

n_incl = sum(1 for h in hallazgos if aprobados_map.get(h.id, h.aprobado))
with panel():
    checkpoint_summary(
        "Punto de control 2: hallazgos",
        f"{n_incl} de {len(hallazgos)} hallazgos incluidos en el plan.",
        bool(run.state.get("checkpoints", {}).get("checkpoint_2_hallazgos")),
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        def _incluir_todos() -> None:
            for hh in hallazgos:
                st.session_state[f"chk_{hh.id}"] = True

        st.button("Incluir todos", icon=":material/done_all:", use_container_width=True, on_click=_incluir_todos)
    with col_b:
        if st.button("Confirmar hallazgos seleccionados", type="primary", icon=":material/task_alt:", use_container_width=True):
            for h in hallazgos:
                h.aprobado = bool(aprobados_map.get(h.id, True))
            run.save_hallazgos(hallazgos)
            run.approve_checkpoint(
                "checkpoint_2_hallazgos",
                note=f"{sum(1 for h in hallazgos if h.aprobado)}/{len(hallazgos)} hallazgos aprobados en Página 4.",
            )
            st.toast("Punto de control 2 aprobado.", icon=":material/check_circle:")
            st.rerun()
