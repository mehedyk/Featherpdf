"""
gui/tab_manager.py
Wraps a ttk.Notebook: each tab holds one ViewerCanvas bound to one TabState.
Opening/closing tabs happens here; MainWindow asks this object for the
"active" ViewerCanvas/TabState rather than tracking it separately.
"""
import tkinter as tk
from tkinter import ttk
from app.gui.viewer_canvas import ViewerCanvas


class TabManager(tk.Frame):
    def __init__(self, parent, page_cache, on_tab_changed, on_page_changed, on_dirty, tts=None):
        super().__init__(parent)
        self.page_cache = page_cache
        self.on_tab_changed = on_tab_changed
        self.on_page_changed = on_page_changed
        self.on_dirty = on_dirty
        self.tts = tts

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._canvases = {}   # tab_state.id -> ViewerCanvas
        self._frame_to_id = {}

    def open_tab(self, tab_state):
        canvas = ViewerCanvas(
            self.notebook, tab_state, self.page_cache, tts=self.tts,
            on_page_changed=self.on_page_changed, on_dirty=self.on_dirty,
        )
        self.notebook.add(canvas, text=tab_state.display_name)
        self._canvases[tab_state.id] = canvas
        self._frame_to_id[str(canvas)] = tab_state.id
        self.notebook.select(canvas)
        return canvas

    def close_tab(self, tab_state_id):
        canvas = self._canvases.pop(tab_state_id, None)
        if canvas:
            self.notebook.forget(canvas)
            canvas.destroy()

    def get_canvas(self, tab_state_id):
        return self._canvases.get(tab_state_id)

    def get_active_canvas(self):
        try:
            current = self.notebook.select()
            if not current:
                return None
            tab_id = self._frame_to_id.get(current)
            return self._canvases.get(tab_id)
        except tk.TclError:
            return None

    def rename_tab(self, tab_state):
        canvas = self._canvases.get(tab_state.id)
        if canvas:
            self.notebook.tab(canvas, text=tab_state.display_name)

    def _on_tab_changed(self, _event):
        current = self.notebook.select()
        tab_id = self._frame_to_id.get(current)
        if tab_id is not None:
            self.on_tab_changed(tab_id)
