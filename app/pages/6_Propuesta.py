"""Página 6: propuesta final en modo cliente y modo prospecto, sello del revisor y exportación .docx/.md."""

from pathlib import Path
import sys
import tempfile
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui_shared import get_active_run, kpi_strip, page_header, panel, render_seal, section
from geo.export import export_docx, export_md
from geo.loader import load_marcas
from geo.writer import write_prospect

run = get_active_run()
if not (run.run_dir / "propuesta.json").exists():
    run.run_all(auto_approve=True, force=False)

propuesta_cliente = run.load_propuesta()
tablas = run.load_tablas()
marcas_catalogo = load_marcas()

page_header(
    "Propuesta",
    "Vista previa íntegra de la propuesta ejecutiva, con el sello del agente revisor y descarga en .docx y .md.",
    step=6,
)

tab_cliente, tab_prospecto = st.tabs(
    [f"Modo cliente · {propuesta_cliente.marca}", "Modo prospecto · captación en frío"]
)

with tab_cliente:
    rev = propuesta_cliente.revision
    total_cifras = rev.cifras_verificadas + rev.cifras_no_trazables
    limpio = rev.aprobado and rev.cifras_no_trazables == 0 and len(rev.incidencias) == 0

    render_seal(
        f"{rev.cifras_verificadas}/{total_cifras} cifras trazables · {len(rev.incidencias)} incidencias normativas",
        "Lista para enviar" if rev.aprobado else "Requiere revisión",
        ok=rev.aprobado,
    )
    if not limpio:
        for inc in rev.incidencias:
            st.warning(f"**{inc.severidad.upper()} · {inc.tipo}.** {inc.detalle} (`{inc.ubicacion}`)", icon=":material/warning:")

    md_path = run.run_dir / f"propuesta_{propuesta_cliente.modo}.md"
    docx_path = run.run_dir / f"propuesta_{propuesta_cliente.modo}.docx"
    if not md_path.exists():
        export_md(propuesta_cliente, md_path)
    if not docx_path.exists():
        export_docx(propuesta_cliente, docx_path)

    nombre_archivo = propuesta_cliente.marca.replace(" ", "_")
    col_dl1, col_dl2, col_regen = st.columns(3)
    with col_dl1:
        st.download_button(
            "Descargar .docx",
            data=docx_path.read_bytes(),
            file_name=f"Propuesta_GEO_{nombre_archivo}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            icon=":material/download:",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            "Descargar .md",
            data=md_path.read_text(encoding="utf-8"),
            file_name=f"Propuesta_GEO_{nombre_archivo}.md",
            mime="text/markdown",
            icon=":material/download:",
            use_container_width=True,
        )
    with col_regen:
        if st.button("Regenerar desde el plan actual", icon=":material/refresh:", use_container_width=True):
            run.run_all(auto_approve=True, force=True)
            st.rerun()

    section("Lectura de la propuesta", f"{len(propuesta_cliente.secciones)} secciones")
    vista_modo = st.segmented_control(
        "Modo de lectura",
        options=["Por secciones", "Documento continuo"],
        default="Por secciones",
        selection_mode="single",
        key="vista_propuesta",
    )

    if vista_modo != "Documento continuo":
        for idx, (sec_title, sec_body) in enumerate(propuesta_cliente.secciones.items()):
            with st.expander(sec_title, expanded=(idx < 2)):
                st.markdown(sec_body)
    else:
        with panel():
            st.markdown(export_md(propuesta_cliente))

with tab_prospecto:
    section(
        "Propuesta para un prospecto",
        "Sin brief previo",
        "Auditoría ejecutiva de captación para cualquier clínica del catálogo, construida con las 624 ejecuciones del estudio sintético.",
    )

    prospect_candidates = [m.nombre for m in marcas_catalogo if m.nombre != propuesta_cliente.marca]
    default_idx = (
        prospect_candidates.index("Vistalia Oftalmología") if "Vistalia Oftalmología" in prospect_candidates else 0
    )
    marca_prosp = st.selectbox("Clínica prospecto", options=prospect_candidates, index=default_idx)

    propuesta_prosp = write_prospect(
        marca=marca_prosp,
        tablas=tablas,
        marcas_catalogo=marcas_catalogo,
        run_id=f"{run.run_id}_prospect",
        provider=run.provider,
    )

    rev_p = propuesta_prosp.revision
    tot_p = rev_p.cifras_verificadas + rev_p.cifras_no_trazables
    render_seal(
        f"{rev_p.cifras_verificadas}/{tot_p} cifras trazables · {len(rev_p.incidencias)} incidencias normativas",
        "Ficha generada desde marcas.csv",
        ok=rev_p.aprobado,
    )

    col_p1, col_p2 = st.columns([1.3, 1.0], gap="large")
    with col_p1:
        for sec_t, sec_b in propuesta_prosp.secciones.items():
            if "Correo comercial" in sec_t:
                continue
            st.markdown(f"### {sec_t}")
            st.markdown(sec_b)

    with col_p2:
        with panel("Correo comercial", "120 a 180 palabras"):
            correo_txt = propuesta_prosp.secciones.get("4. Correo comercial", "")
            n_words = len(correo_txt.split())
            st.caption(f"Longitud verificada: {n_words} palabras.")
            st.code(correo_txt, language="markdown", wrap_lines=True)

            md_prosp_str = export_md(propuesta_prosp)
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
                export_docx(propuesta_prosp, Path(tmp_docx.name))
                docx_prosp_bytes = Path(tmp_docx.name).read_bytes()

            nombre_prosp = marca_prosp.replace(" ", "_")
            st.download_button(
                "Descargar dossier .docx",
                data=docx_prosp_bytes,
                file_name=f"Propuesta_Prospecto_{nombre_prosp}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                icon=":material/download:",
                use_container_width=True,
            )
            st.download_button(
                "Descargar dossier .md",
                data=md_prosp_str,
                file_name=f"Propuesta_Prospecto_{nombre_prosp}.md",
                mime="text/markdown",
                icon=":material/download:",
                use_container_width=True,
            )
