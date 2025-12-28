import io
import zipfile
from typing import Dict, List, Tuple

import streamlit as st
from PyPDF2 import PdfReader, PdfWriter


def load_files(uploaded_files: List) -> List[Dict]:
    """Return basic info and raw bytes for each uploaded PDF."""
    files: List[Dict] = []
    for uploaded in uploaded_files:
        data = uploaded.read()
        if not data:
            st.warning(f"{uploaded.name} está vacío, se omite.")
            continue
        try:
            reader = PdfReader(io.BytesIO(data))
            files.append({"name": uploaded.name, "data": data, "pages": len(reader.pages)})
        except Exception as exc:
            st.error(f"No se pudo leer {uploaded.name}: {exc}")
    return files


def parse_ranges(text: str, total_pages: int) -> Tuple[List[Tuple[int, int]], List[str]]:
    """Parse comma-separated pages/ranges into (start, end) tuples (1-indexed, inclusive)."""
    ranges: List[Tuple[int, int]] = []
    errors: List[str] = []
    tokens = [t.strip() for t in text.split(",") if t.strip()]
    for token in tokens:
        if ":" in token:
            parts = token.split(":")
            if len(parts) != 2:
                errors.append(token)
                continue
            try:
                start, end = int(parts[0]), int(parts[1])
            except ValueError:
                errors.append(token)
                continue
        else:
            try:
                start = end = int(token)
            except ValueError:
                errors.append(token)
                continue

        if start > end:
            start, end = end, start

        start = max(1, start)
        end = min(total_pages, end)
        if start > total_pages:
            continue

        ranges.append((start, end))

    return ranges, errors


def ranges_to_label(ranges: List[Tuple[int, int]]) -> str:
    """Return a human label from a list of ranges [(1,1),(2,5)] -> '1, 2-5'."""
    labels = []
    for start, end in ranges:
        labels.append(str(start) if start == end else f"{start}-{end}")
    return ", ".join(labels)


def normalize_filename(name: str, extension: str = "pdf") -> str:
    cleaned = name.strip() or f"resultado.{extension}"
    ext = f".{extension}"
    return cleaned if cleaned.lower().endswith(ext) else f"{cleaned}{ext}"


def merge_pdfs(files: List[Dict], mode: str, selections: Dict[str, List[Tuple[int, int]]]) -> io.BytesIO:
    """Merge pages following the selected mode."""
    writer = PdfWriter()
    for file in files:
        reader = PdfReader(io.BytesIO(file["data"]))
        total_pages = len(reader.pages)
        label_text = None

        if mode == "all":
            page_indexes = range(total_pages)
            label_text = "1" if total_pages == 1 else f"1-{total_pages}"
        elif mode == "last":
            page_indexes = [total_pages - 1]
            label_text = str(total_pages)
        elif mode == "first":
            page_indexes = [0]
            label_text = "1"
        else:
            selection = selections.get(file["name"], [])
            if not selection:
                continue
            page_indexes = []
            for start, end in selection:
                page_indexes.extend(range(start - 1, end))
            label_text = ranges_to_label(selection)

        start_page = len(writer.pages)
        added = 0
        for page_index in page_indexes:
            writer.add_page(reader.pages[page_index])
            added += 1

        if added:
            title = file["name"] if not label_text else f"{file['name']} - páginas {label_text}"
            writer.add_outline_item(title=title, page_number=start_page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def split_pdfs(
    files: List[Dict],
    mode: str,
    selections: Dict[str, List[Tuple[int, int]]],
    consolidate: bool,
) -> Tuple[str | None, bytes | None]:
    """Split PDFs into individual ranges; return ("pdf" or "zip", data)."""
    consolidated_writer = PdfWriter() if consolidate else None
    parts: List[Tuple[str, bytes]] = []

    for file in files:
        reader = PdfReader(io.BytesIO(file["data"]))
        total_pages = len(reader.pages)
        if mode == "all":
            ranges = [(i, i) for i in range(1, total_pages + 1)]
        else:
            ranges = selections.get(file["name"], [])
            if not ranges:
                continue

        base_name = file["name"].rsplit(".", 1)[0]
        parent_outline = None

        for start, end in ranges:
            writer = PdfWriter()
            range_start_page = len(consolidated_writer.pages) if consolidated_writer else 0
            for idx in range(start - 1, end):
                writer.add_page(reader.pages[idx])
                if consolidated_writer:
                    consolidated_writer.add_page(reader.pages[idx])

            label = f"{start}" if start == end else f"{start}-{end}"

            if consolidate:
                if consolidated_writer and writer.get_num_pages() > 0:
                    if parent_outline is None:
                        parent_outline = consolidated_writer.add_outline_item(
                            title=file["name"], page_number=range_start_page
                        )
                    consolidated_writer.add_outline_item(
                        title=f"{file['name']} - páginas {label}",
                        page_number=range_start_page,
                        parent=parent_outline,
                    )
            else:
                if writer.get_num_pages() > 0:
                    writer.add_outline_item(title=f"{file['name']} - páginas {label}", page_number=0)
                    filename = f"{base_name}_p{label}.pdf"
                    buf = io.BytesIO()
                    writer.write(buf)
                    buf.seek(0)
                    parts.append((filename, buf.getvalue()))

    if consolidate:
        if consolidated_writer and len(consolidated_writer.pages) == 0:
            return None, None
        buf = io.BytesIO()
        consolidated_writer.write(buf)
        buf.seek(0)
        return "pdf", buf.getvalue()

    if not parts:
        return None, None

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, data in parts:
            zf.writestr(filename, data)
    zip_buf.seek(0)
    return "zip", zip_buf.getvalue()
