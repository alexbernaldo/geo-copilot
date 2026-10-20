"""Página 6 · Propuesta final en Modo Cliente y Modo Prospecto, sello del revisor y exportación .docx/.md (F13)."""

from pathlib import Path
import sys
import tempfile
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, render_header_banner
from geo.export import export_docx, export_md
from geo.loader import load_marcas
from geo.writer import write_prospect

st.set_page_config(page_title="6 · Propuesta | GEO Copilot", page_icon="📄", layout="wide")
render_header_banner()

run = get_active_run()
if not (run.run_dir / "propuesta.json").exists():
    run.run_all(auto_approve=True, force=False)

propuesta_cliente = run.load_propuesta()
tablas = run.load_tablas()
marcas_catalogo = load_marcas()

st.title("6 · Propuesta Estratégica y Comercial")
st.caption(
    "Previsualización íntegra de la propuesta ejecutiva con sello del agente revisor (verificación determinista de cifras y cumplimiento normativo sanitario) y descarga en `.docx` y `.md`."
)

tab_cliente, tab_prospecto = st.tabs(
    [
        f"🏥 Modo Cliente ({propuesta_cliente.marca} · 10 secciones)",
        "🎯 Modo Prospecto (Captación en frío sin brief previo)",
    ]
)

with tab_cliente:
    rev = propuesta_cliente.revision
    total_cifras = rev.cifras_verificadas + rev.cifras_no_trazables

    # Sello del revisor
    st.subheader("🛡️ Sello del Agente Revisor (F10)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estado de revisión", "APROBADO ✅" if rev.aprobado else "REVISIÓN ⚠️")
    c2.metric("Cifras trazables verificadas", f"{rev.cifras_verificadas}/{total_cifras}")
    c3.metric("Cifras no trazables", str(rev.cifras_no_trazables))
    c4.metric("Incidencias normativas", str(len(rev.incidencias)))

    if rev.aprobado and rev.cifras_no_trazables == 0 and len(rev.incidencias) == 0:
        st.success(
            f"**Sello Verificador GEO:** `{rev.cifras_verificadas}/{total_cifras}` cifras trazables verificadas contra las tablas deterministas y `0` incidencias normativas sanitarias."
        )
    else:
        for inc in rev.incidencias:
            st.warning(f"**[{inc.severidad.upper()} · {inc.tipo}]** {inc.detalle} (`{inc.ubicacion}`)")

    # Botones de descarga .docx y .md
    md_path = run.run_dir / f"propuesta_{propuesta_cliente.modo}.md"
    docx_path = run.run_dir / f"propuesta_{propuesta_cliente.modo}.docx"
    if not md_path.exists():
        export_md(propuesta_cliente, md_path)
    if not docx_path.exists():
        export_docx(propuesta_cliente, docx_path)

    col_dl1, col_dl2, col_regen = st.columns([1, 1, 1])
    with col_dl1:
        st.download_button(
            "📥 Descargar Propuesta Cliente (.docx)",
            data=docx_path.read_bytes(),
            file_name=f"Propuesta_GEO_{propuesta_cliente.marca.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            "📥 Descargar Propuesta Cliente (.md)",
            data=md_path.read_text(encoding="utf-8"),
            file_name=f"Propuesta_GEO_{propuesta_cliente.marca.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_regen:
        if st.button("🔄 Regenerar propuesta desde Plan actual", use_container_width=True):
            run.run_all(auto_approve=True, force=True)
            st.rerun()

    st.divider()
    st.subheader("📖 Vista previa de las 10 secciones")
    sec_names = list(propuesta_cliente.secciones.keys())
    vista_modo = st.radio(
        "Modo de lectura:",
        options=["Sección por sección (desplegables)", "Documento completo continuo"],
        horizontal=True,
    )

    if vista_modo == "Sección por sección (desplegables)":
        for idx, (sec_title, sec_body) in enumerate(propuesta_cliente.secciones.items()):
            with st.expander(f"**{sec_title}**", expanded=(idx < 2)):
                st.markdown(sec_body)
    else:
        full_md = export_md(propuesta_cliente)
        st.markdown(full_md)

with tab_prospecto:
    st.subheader("🎯 Generador de Propuesta en Modo Prospecto (sin brief previo)")
    st.caption(
        "Construye al instante una auditoría ejecutiva de captación para cualquier clínica competidora del catálogo a partir de las 624 ejecuciones del estudio sintético."
    )

    prospect_candidates = [
        m.nombre for m in marcas_catalogo if m.nombre != propuesta_cliente.marca
    ]
    default_idx = (
        prospect_candidates.index("Vistalia Oftalmología")
        if "Vistalia Oftalmología" in prospect_candidates
        else 0
    )

    marca_prosp = st.selectbox(
        "Selecciona la clínica prospecto objetivo:",
        options=prospect_candidates,
        index=default_idx,
    )

    propuesta_prosp = write_prospect(
        marca=marca_prosp,
        tablas=tablas,
        marcas_catalogo=marcas_catalogo,
        run_id=f"{run.run_id}_prospect",
        provider=run.provider,
    )

    rev_p = propuesta_prosp.revision
    tot_p = rev_p.cifras_verificadas + rev_p.cifras_no_trazables
    st.info(
        f"🛡️ **Sello Revisor (Prospecto {marca_prosp}):** `{rev_p.cifras_verificadas}/{tot_p}` cifras trazables · `{len(rev_p.incidencias)}` incidencias normativas · Ficha generada desde `marcas.csv` (sin brief interno)."
    )

    col_p1, col_p2 = st.columns([1.3, 1.0])
    with col_p1:
        for sec_t, sec_b in propuesta_prosp.secciones.items():
            if "Correo comercial" in sec_t:
                continue
            st.markdown(f"### {sec_t}")
            st.markdown(sec_b)

    with col_p2:
        st.markdown("### ✉️ Correo comercial listo para enviar (120–180 palabras)")
        correo_txt = propuesta_prosp.secciones.get("4. Correo comercial", "")
        n_words = len(correo_txt.split())
        st.caption(f"Longitud verificada: **{n_words} palabras** (rango objetivo: 120–180 palabras).")
        st.code(correo_txt, language="markdown")

        md_prosp_str = export_md(propuesta_prosp)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            export_docx(propuesta_prosp, Path(tmp_docx.name))
            docx_prosp_bytes = Path(tmp_docx.name).read_bytes()

        st.download_button(
            f"📥 Descargar Dossier Prospecto — {marca_prosp} (.docx)",
            data=docx_prosp_bytes,
            file_name=f"Propuesta_Prospecto_{marca_prosp.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )
        st.download_button(
            f"📥 Descargar Dossier Prospecto — {marca_prosp} (.md)",
            data=md_prosp_str,
            file_name=f"Propuesta_Prospecto_{marca_prosp.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
