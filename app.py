from typing import Dict, List, Tuple

import streamlit as st

from pdf_utils import (
    load_files,
    merge_pdfs,
    normalize_filename,
    parse_ranges,
    split_pdfs,
)


st.set_page_config(
    page_title="SAIPE PDF",
    page_icon="🤖",
    layout="centered")


def render_ranges_grid(
    files: List[Dict],
    sort_files: bool,
    key_prefix: str,
    header_third: str,
) -> Dict[str, List[Tuple[int, int]]]:
    st.caption("Ingresá páginas sueltas y/o rangos separados por coma. Ej: 1, 2, 20, 25, 45:57, 66:89")
    header_cols = st.columns([0.55, 0.15, 0.3])
    header_cols[0].markdown("**Archivo**")
    header_cols[1].markdown("**Páginas**")
    header_cols[2].markdown(header_third)

    selections: Dict[str, List[Tuple[int, int]]] = {}
    for idx, file in enumerate(sorted(files, key=lambda f: f["name"]) if sort_files else files):
        total_pages = file["pages"]
        col_name, col_pages, col_input = st.columns([0.55, 0.15, 0.3])
        col_name.write(file["name"])
        col_pages.write(f"{total_pages}")
        default_range = "1" if total_pages == 1 else f"1:{total_pages}"
        input_value = col_input.text_input(
            "Rangos",
            value=default_range,
            key=f"{key_prefix}_ranges_{idx}",
            label_visibility="collapsed",
            placeholder="1, 2, 5:7",
        )
        ranges, errors = parse_ranges(input_value, total_pages)
        selections[file["name"]] = ranges
        if errors:
            col_input.caption(f"Omitido(s) por formato inválido: {', '.join(errors)}")
        if not ranges:
            col_input.caption("Sin páginas válidas: se omitirá este archivo.")

    return selections


st.title("I 🤖 SAIPE PDF")
st.markdown("~~I ❤️ PDF~~  I 🤖 SAIPE PDF")
st.caption(
    "Herramienta simple para combinar o extraer páginas. Subí uno o varios PDFs y elegí el modo: "
    "podés consolidar primeras/últimas/todas las hojas o trabajar con rangos; también separar páginas sueltas "
    "en PDFs individuales o consolidarlas en un único archivo."
)


tab_merge, tab_split = st.tabs(["Consolidar", "Separar"])

with tab_merge:
    st.subheader("Consolidar PDFs")
    st.write(
        "Arrastrá los archivos PDF, elegí cómo consolidarlos y descargá el resultado. "
        "Podés unir todo el contenido, solo la última hoja, solo la primera hoja o seleccionar páginas por archivo con rangos "
        '(por defecto "Primera:Última"; ejemplo: `1, 2, 20, 25, 45:57, 66:89`).'
    )
    st.info(
        "- **Orden sugerido**: habilitá “Ordenar por nombre” si querés consolidar alfabéticamente.\n"
        "- **Rangos**: separá con comas, combinando páginas sueltas y tramos (ej: `1, 5:8, 10`).\n"
        "- **Salida**: descarga directa del PDF consolidado con el nombre que definas."
    )

    uploaded_files = st.file_uploader(
        "Archivos PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="Podés subir varios PDF a la vez.",
        key="merge_uploader",
    )

    files = load_files(uploaded_files) if uploaded_files else []

    with st.form("merge_form"):
        col_left, col_right = st.columns([2, 1])
        with col_left:
            mode = st.radio(
                "Modo de consolidación",
                options=[
                    ("all", "Todas las páginas"),
                    ("last", "Solo últimas páginas"),
                    ("first", "Solo primeras páginas"),
                    ("selected", "Elegir páginas por archivo"),
                ],
                format_func=lambda opt: opt[1],
                horizontal=True,
                index=0,
            )[0]
        with col_right:
            sort_files = st.checkbox("Ordenar por nombre", value=True)

        output_name = st.text_input("Nombre del PDF consolidado", value="consolidado.pdf")

        selections: Dict[str, List[Tuple[int, int]]] = {}
        if files and mode == "selected":
            st.markdown("### Selección de páginas por archivo")
            selections = render_ranges_grid(
                files=files,
                sort_files=sort_files,
                key_prefix="merge",
                header_third="**Rangos a consolidar**",
            )

        submitted = st.form_submit_button("Consolidar")

    if submitted:
        if not files:
            st.error("Subí al menos un PDF para consolidar.")
        else:
            files_to_merge = sorted(files, key=lambda f: f["name"]) if sort_files else files
            merged_pdf = merge_pdfs(files_to_merge, mode, selections)
            final_name = normalize_filename(output_name)

            st.success("PDF consolidado listo para descargar.")
            st.download_button(
                "Descargar PDF",
                data=merged_pdf.getvalue(),
                file_name=final_name,
                mime="application/pdf",
            )

with tab_split:
    st.subheader("Separar / Extraer PDFs")
    st.write(
        "Subí uno o varios PDFs para separar todas las hojas, extraer rangos o páginas sueltas. "
        "Podés optar por consolidar el resultado en un solo PDF o descargar los recortes individuales en un ZIP."
    )
    st.info(
        "- **Separar todas las hojas**: genera un archivo por página (se descarga en ZIP).\n"
        "- **Separar por rangos**: definí páginas/rangos por archivo con el mismo formato `1, 2, 5:9`.\n"
        "- **Consolidar extracciones**: marca la casilla para obtener un único PDF con todas las páginas extraídas."
    )

    split_uploads = st.file_uploader(
        "PDFs a separar",
        type=["pdf"],
        accept_multiple_files=True,
        help="Podés subir uno o varios PDF.",
        key="split_uploader",
    )
    split_files = load_files(split_uploads) if split_uploads else []

    with st.form("split_form"):
        mode_split = st.radio(
            "Modo de separación",
            options=[
                ("all", "Separar todas las hojas (una por PDF)"),
                ("ranges", "Separar por rangos/páginas por archivo"),
            ],
            format_func=lambda opt: opt[1],
            horizontal=True,
            index=0,
        )[0]
        sort_split = st.checkbox("Ordenar por nombre", value=True, key="split_sort")
        consolidate_split = st.checkbox("Consolidar extracciones en un solo PDF", value=False)
        output_name_split = st.text_input(
            "Nombre del resultado (PDF si consolidás, ZIP si no)",
            value="separados",
            help="Se agregará .pdf o .zip según corresponda.",
        )

        split_selections: Dict[str, List[Tuple[int, int]]] = {}
        if split_files and mode_split == "ranges":
            st.markdown("### Rangos por archivo")
            split_selections = render_ranges_grid(
                files=split_files,
                sort_files=sort_split,
                key_prefix="split",
                header_third="**Rangos a extraer**",
            )

        submitted_split = st.form_submit_button("Separar")

    if submitted_split:
        if not split_files:
            st.error("Subí al menos un PDF para separar.")
        else:
            files_to_use = sorted(split_files, key=lambda f: f["name"]) if sort_split else split_files
            kind, payload = split_pdfs(files_to_use, mode_split, split_selections, consolidate_split)
            if not payload:
                st.error("No se encontraron páginas válidas para separar.")
            else:
                ext = "pdf" if consolidate_split else "zip"
                final_name = normalize_filename(output_name_split, ext)
                st.success("Archivo listo para descargar.")
                st.download_button(
                    "Descargar resultado",
                    data=payload,
                    file_name=final_name,
                    mime="application/pdf" if ext == "pdf" else "application/zip",
                )
