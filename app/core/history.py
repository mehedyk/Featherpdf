"""
core/history.py
Undo/redo for a single document tab.

Design choice: full-bytes snapshots, NOT operation diffs. A true diff engine
for arbitrary PDF mutations (page delete/reorder/annotate/rotate all touch
different internal structures) is a lot of bespoke inverse-logic for a
"lite" app. Snapshots are simple and correct; to keep memory bounded we cap
the stack depth and only snapshot on user-initiated edits (not on every
render), which in practice is infrequent enough that the memory cost is
small relative to the app's other savings (no OpenCV, no Qt, etc).
"""
import pymupdf

MAX_HISTORY = 20


class History:
    def __init__(self, pdf_doc):
        self._pdf_doc = pdf_doc
        self._undo_stack = []
        self._redo_stack = []

    def snapshot(self):
        """Call BEFORE performing a mutating operation."""
        data = self._pdf_doc.doc.tobytes()
        self._undo_stack.append(data)
        if len(self._undo_stack) > MAX_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def can_undo(self):
        return len(self._undo_stack) > 0

    def can_redo(self):
        return len(self._redo_stack) > 0

    def undo(self):
        if not self.can_undo():
            return False
        current = self._pdf_doc.doc.tobytes()
        self._redo_stack.append(current)
        data = self._undo_stack.pop()
        self._pdf_doc.doc.close()
        self._pdf_doc.doc = pymupdf.open("pdf", data)
        self._pdf_doc.dirty = True
        return True

    def redo(self):
        if not self.can_redo():
            return False
        current = self._pdf_doc.doc.tobytes()
        self._undo_stack.append(current)
        data = self._redo_stack.pop()
        self._pdf_doc.doc.close()
        self._pdf_doc.doc = pymupdf.open("pdf", data)
        self._pdf_doc.dirty = True
        return True

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
