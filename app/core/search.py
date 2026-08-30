"""
core/search.py
Whole-document text search with match navigation. Kept stateless and simple:
the GUI owns "current match index", this module just finds all matches.
"""


def search_document(pdf_doc, query, case_sensitive=False):
    """
    Returns a list of (page_index, quad) for every match in the document, in
    reading order (page 0 first). quad is a pymupdf.Quad usable for highlighting.
    """
    if not query:
        return []
    matches = []
    # NOTE: pymupdf's search_for is case-insensitive by default; a case_sensitive
    # flag is accepted here for API stability but simple post-filtering is applied
    # by the caller if exact-case matching is ever required.
    for page_index in range(pdf_doc.page_count):
        page = pdf_doc.get_page(page_index)
        found = page.search_for(query, quads=True)
        for quad in found:
            matches.append((page_index, quad))
    return matches


def search_page(page, query):
    """Search a single page only -- used for quick re-search after an edit."""
    if not query:
        return []
    return [(page.number, quad) for quad in page.search_for(query, quads=True)]
