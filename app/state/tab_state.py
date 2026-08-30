"""
state/tab_state.py
Everything about ONE open document tab: which PDFDocument, current page,
zoom, fit mode, selection, undo history. GUI widgets read/write here instead
of holding their own copies, so toolbar/canvas/sidebar always agree.
"""
from app.core.history import History

FIT_NONE = "none"       # manual zoom
FIT_WIDTH = "width"
FIT_PAGE = "page"
FIT_SCREEN = "screen"


class TabState:
    _next_id = 1

    def __init__(self, pdf_doc, title):
        self.id = TabState._next_id
        TabState._next_id += 1

        self.pdf_doc = pdf_doc
        self.title = title
        self.current_page = 0
        self.zoom = 1.0
        self.fit_mode = FIT_SCREEN
        self.dark_mode = False
        self.history = History(pdf_doc)
        self.search_query = ""
        self.search_matches = []      # list of (page_index, quad)
        self.search_index = -1
        self.selected_pages = set()   # for multi-select in thumbnail panel
        self.selected_words = []      # list of pymupdf word-tuples, current text selection
        self.selected_text = ""       # joined text of selected_words, kept in sync

    @property
    def display_name(self):
        star = "*" if self.pdf_doc.dirty else ""
        return f"{self.title}{star}"
