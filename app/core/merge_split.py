"""
core/merge_split.py
Higher-level operations that combine multiple PDFDocuments or split one apart.
Everything here is in-memory until the caller calls .save() on the result.
"""
import pymupdf
from app.core.document import PDFDocument


def merge_pdfs(paths):
    """Merge a list of PDF file paths, in order, into a single new PDFDocument."""
    merged = PDFDocument()
    for p in paths:
        src = pymupdf.open(p)
        merged.doc.insert_pdf(src)
        src.close()
    merged.dirty = True
    return merged


def split_every_n_pages(pdf_doc: PDFDocument, n: int):
    """Split into a list of new PDFDocuments, each with up to n consecutive pages."""
    results = []
    total = pdf_doc.page_count
    for start in range(0, total, n):
        end = min(start + n - 1, total - 1)
        chunk = pymupdf.open()
        chunk.insert_pdf(pdf_doc.doc, from_page=start, to_page=end)
        wrapper = PDFDocument()
        wrapper.doc.close()
        wrapper.doc = chunk
        results.append(wrapper)
    return results


def split_by_ranges(pdf_doc: PDFDocument, ranges):
    """ranges: list of (start, end) 0-indexed inclusive tuples -> list of new PDFDocuments."""
    results = []
    for start, end in ranges:
        chunk = pymupdf.open()
        chunk.insert_pdf(pdf_doc.doc, from_page=start, to_page=end)
        wrapper = PDFDocument()
        wrapper.doc.close()
        wrapper.doc = chunk
        results.append(wrapper)
    return results


def parse_page_range_string(range_str, page_count):
    """
    Parse a user-typed range like '1-3,5,8-10' (1-indexed, inclusive)
    into a sorted list of 0-indexed page numbers. Raises ValueError on bad input.
    """
    indices = set()
    range_str = range_str.strip()
    if not range_str:
        raise ValueError("Empty page range.")
    for part in range_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            if a < 1 or b > page_count or a > b:
                raise ValueError(f"Range {part} out of bounds (document has {page_count} pages).")
            indices.update(range(a - 1, b))
        else:
            p = int(part)
            if p < 1 or p > page_count:
                raise ValueError(f"Page {p} out of bounds (document has {page_count} pages).")
            indices.add(p - 1)
    return sorted(indices)
