"""
core/document.py
Wraps a pymupdf.Document with the extra bookkeeping the app needs
(dirty flag, file path, password state). No GUI code here.
"""
import pymupdf


class PDFDocument:
    """A single open PDF, independent of any tab/window."""

    def __init__(self, path=None):
        self.path = path
        self.doc = pymupdf.open(path) if path else pymupdf.open()
        self.dirty = False
        self.password_protected = self.doc.needs_pass if path else False

    # ---- basic info ----
    @property
    def page_count(self):
        return self.doc.page_count

    def get_page(self, index):
        return self.doc[index]

    def get_toc(self):
        """Table of contents / bookmarks: list of [level, title, page]."""
        return self.doc.get_toc()

    def get_metadata(self):
        return dict(self.doc.metadata or {})

    def set_metadata(self, meta: dict):
        self.doc.set_metadata(meta)
        self.dirty = True

    def authenticate(self, password):
        ok = self.doc.authenticate(password)
        if ok:
            self.password_protected = False
        return ok

    # ---- page mutation ----
    def delete_page(self, index):
        self.doc.delete_page(index)
        self.dirty = True

    def delete_pages(self, indices):
        # delete highest index first so earlier indices stay valid
        for i in sorted(indices, reverse=True):
            self.doc.delete_page(i)
        self.dirty = True

    def insert_blank_page(self, index, width=595, height=842):
        self.doc.insert_page(index, width=width, height=height)
        self.dirty = True

    def move_page(self, from_index, to_index):
        self.doc.move_page(from_index, to_index)
        self.dirty = True

    def rotate_page(self, index, degrees):
        """Permanent rotation, saved with the file (not just display)."""
        page = self.doc[index]
        page.set_rotation((page.rotation + degrees) % 360)
        self.dirty = True

    def insert_pdf(self, other_doc, start_at=None):
        """Insert all pages of another PDFDocument/Document at start_at (append if None)."""
        src = other_doc.doc if isinstance(other_doc, PDFDocument) else other_doc
        if start_at is None:
            self.doc.insert_pdf(src)
        else:
            self.doc.insert_pdf(src, start_at=start_at)
        self.dirty = True

    def extract_pages(self, indices):
        """Return a NEW PDFDocument containing only the given pages (order preserved)."""
        new_doc = pymupdf.open()
        for i in indices:
            new_doc.insert_pdf(self.doc, from_page=i, to_page=i)
        wrapper = PDFDocument()
        wrapper.doc.close()
        wrapper.doc = new_doc
        return wrapper

    # ---- save ----
    def save(self, path=None, garbage=4, deflate=True):
        target = path or self.path
        if not target:
            raise ValueError("No path given for save().")
        # incremental save only works when saving to the same file that was
        # opened without structural changes; for safety we always do a full save
        self.doc.save(target, garbage=garbage, deflate=deflate)
        self.path = target
        self.dirty = False

    def close(self):
        self.doc.close()
