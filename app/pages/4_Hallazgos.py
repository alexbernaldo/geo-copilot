"""Página 4: Hallazgos priorizados con evidencias (Checkpoint 2) (F13)."""

from pathlib import Path
import sys
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import evidence_view, get_active_run, render_header_banner

st.set_page_config(page_title="4 · Hallazgos · GEO Copilot", page_icon="💡", layout="wide")
render_header_banner()

run = get_active_run()
ficha = run.load_ficha()
hallazgos = run.load_hallazgos()

st.title(f"4 · Hallazgos Priorizados con Evidencia Trazable (Checkpoint 2)")
st.markdown(
    "Cada hallazgo ha sido generado por reglas deterministas sobre las tablas `T1`–`T12`. "
    "Puedes revisar las ejecuciones originales que lo respaldan y activar o descartar cada hallazgo antes de construir el plan."
)

aprobados_map: dict[str, bool] = {}

for h in hallazgos:
    badge_imp = "🔴 Impacto Alto" if h.impacto == "alto" else ("🟠 Impacto Medio" if h.impacto == "medio" else "🟢 Impacto Bajo")
    badge_conf = f"Confianza {h.confianza.upper()}"
    with st.container(border=True):
        c_head, c_chk = st.columns([5, 1])
        with c_head:
            st.markdown(
                f"### `{h.id}` (Prioridad #{h.prioridad}) · {h.titulo}  \n"
                f"**Tipo:** `{h.tipo}` · **{badge_imp}** · **{badge_conf}**"
                + (f" · **Fase embudo:** `{h.fase_embudo}`" if h.fase_embudo else "")
                + (f" · **Motores:** `{', '.join(h.motores)}`" if h.motores else "")
            )
            st.write(h.descripcion)
        with c_chk:
            aprobados_map[h.id] = st.checkbox(
                "Incluir en Plan",
                value=bool(h.aprobado),
                key=f"chk_{h.id}",
            )

        ev_cols = st.columns(len(h.evidencias))
        all_eids: list[str] = []
        for ecol, ev in zip(ev_cols, h.evidencias):
            ecol.caption(
                f"📊 **`{ev.metrica}`**  \nValor: **{ev.valor}** · Muestra: **`n={ev.n}`** · Origen: `{ev.tabla}`"
            )
            for eid in ev.ejecucion_ids:
                if eid not in all_eids:
                    all_eids.append(eid)

        evidence_view(
            all_eids,
            marca_resaltada=ficha.marca,
            title=f"🔎 Ver respuestas de evidencia de {h.id}",
            max_items=4,
        )

if st.button(
    "✅ Confirmar Hallazgos Seleccionados (Checkpoint 2)",
    type="primary",
    use_container_width=True,
):
    for h in hallazgos:
        h.aprobado = bool(aprobados_map.get(h.id, True))
    run.save_hallazgos(hallazgos)
    run.approve_checkpoint(
        "checkpoint_2_hallazgos",
        note=f"{sum(1 for h in hallazgos if h.aprobado)}/{len(hallazgos)} hallazgos aprobados en Página 4.",
    )
    st.success("✅ Checkpoint 2 aprobado y guardado en `findings.json`.")
