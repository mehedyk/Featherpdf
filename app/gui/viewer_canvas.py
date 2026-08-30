"""
gui/viewer_canvas.py
The scrollable canvas that draws the current page and handles zoom/pan/
scroll, real word-level text selection (+ copy, + read-aloud), and
click-drag annotation placement (highlight/underline/strikeout/note/ink).
One ViewerCanvas per open tab.
"""
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk
import pymupdf

from app.render.page_renderer import render_page_to_pil, invert_for_dark_mode, compute_zoom_for_fit
from app.state.tab_state import FIT_NONE, FIT_WIDTH, FIT_PAGE, FIT_SCREEN
from app.core import annotations as ann
from app.core import text_extraction as tex


class ViewerCanvas(tk.Frame):
    def __init__(self, parent, tab_state, page_cache, tts=None, on_page_changed=None, on_dirty=None):
        super().__init__(parent, bg="#606060")
        self.tab_state = tab_state
        self.page_cache = page_cache
        self.tts = tts
        self.on_page_changed = on_page_changed
        self.on_dirty = on_dirty

        # None = plain text-selection mode (the default). Otherwise one of:
        # 'highlight', 'underline', 'strikeout', 'note', 'ink'
        self.annotation_tool = None
        self.annotation_color = ann.COLOR_YELLOW
        self._drag_start = None
        self._current_tk_image = None
        self._current_pil_size = (0, 0)
        self._ink_points = []
        self._page_words_cache = {}   # (doc_id, page_index) -> words list, cleared on edits

        self.canvas = tk.Canvas(self, bg="#606060", highlightthickness=0, cursor="xterm")
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
        self.canvas.bind("<Button-4>", self._on_mousewheel)        # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)        # Linux scroll down
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Control-c>", lambda e: self.copy_selection_to_clipboard())

        self._image_item = None
        self.render_current_page()

    # ---- rendering ----
    def render_current_page(self, force=False):
        ts = self.tab_state
        doc = ts.pdf_doc
        if doc.page_count == 0:
            self.canvas.delete("all")
            return

        ts.current_page = max(0, min(ts.current_page, doc.page_count - 1))
        page = doc.get_page(ts.current_page)

        if ts.fit_mode != FIT_NONE:
            vp_w = max(self.canvas.winfo_width(), 200)
            vp_h = max(self.canvas.winfo_height(), 200)
            page_rect = page.rect
            mode = {FIT_WIDTH: "width", FIT_PAGE: "page", FIT_SCREEN: "screen"}[ts.fit_mode]
            ts.zoom = compute_zoom_for_fit(page_rect.width, page_rect.height, vp_w, vp_h, mode)

        cache_key = self.page_cache.make_key(id(doc), ts.current_page, ts.zoom)
        pil_img = None if force else self.page_cache.get(cache_key)
        if pil_img is None:
            pil_img = render_page_to_pil(page, zoom=ts.zoom)
            if ts.dark_mode:
                pil_img = invert_for_dark_mode(pil_img)
            self.page_cache.put(cache_key, pil_img)

        self._current_pil_size = pil_img.size
        self._current_tk_image = ImageTk.PhotoImage(pil_img)

        self.canvas.delete("all")
        self._image_item = self.canvas.create_image(0, 0, anchor="nw", image=self._current_tk_image)
        self.canvas.configure(scrollregion=(0, 0, pil_img.width, pil_img.height))

        self._draw_search_highlights()
        self._draw_selection_overlay()

        if self.on_page_changed:
            self.on_page_changed(ts.current_page, doc.page_count)

    def _draw_search_highlights(self):
        ts = self.tab_state
        if not ts.search_matches:
            return
        zoom = ts.zoom
        for i, (page_idx, quad) in enumerate(ts.search_matches):
            if page_idx != ts.current_page:
                continue
            rect = quad.rect
            x0, y0, x1, y1 = rect.x0 * zoom, rect.y0 * zoom, rect.x1 * zoom, rect.y1 * zoom
            color = "#ff8800" if i == ts.search_index else "#ffe066"
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags="search_hit")

    def _draw_selection_overlay(self):
        """Redraws the persisted (post-drag) text selection, if any, on the current page."""
        ts = self.tab_state
        if not ts.selected_words:
            return
        zoom = ts.zoom
        for w in ts.selected_words:
            x0, y0, x1, y1 = w[0] * zoom, w[1] * zoom, w[2] * zoom, w[3] * zoom
            self.canvas.create_rectangle(
                x0, y0, x1, y1, fill="#4a90d9", outline="", stipple="gray50", tags="selection"
            )

    # ---- word lookup (cached per page, invalidated on edits) ----
    def _get_words_for_current_page(self):
        ts = self.tab_state
        key = (id(ts.pdf_doc), ts.current_page)
        words = self._page_words_cache.get(key)
        if words is None:
            page = ts.pdf_doc.get_page(ts.current_page)
            words = tex.get_words(page)
            self._page_words_cache[key] = words
        return words

    def _invalidate_words_cache(self):
        self._page_words_cache.clear()

    # ---- navigation ----
    def goto_page(self, index):
        self.tab_state.current_page = index
        self.render_current_page()

    def next_page(self):
        self.goto_page(self.tab_state.current_page + 1)

    def prev_page(self):
        self.goto_page(self.tab_state.current_page - 1)

    # ---- zoom ----
    def set_zoom(self, zoom, fit_mode=FIT_NONE):
        self.tab_state.zoom = max(0.1, min(zoom, 5.0))
        self.tab_state.fit_mode = fit_mode
        self.render_current_page()

    def zoom_in(self):
        self.set_zoom(self.tab_state.zoom * 1.1, fit_mode=FIT_NONE)

    def zoom_out(self):
        self.set_zoom(self.tab_state.zoom / 1.1, fit_mode=FIT_NONE)

    def zoom_reset(self):
        self.set_zoom(1.0, fit_mode=FIT_NONE)

    def set_fit_mode(self, mode):
        self.tab_state.fit_mode = mode
        self.render_current_page()

    # ---- events ----
    def _on_resize(self, _event):
        if self.tab_state.fit_mode != FIT_NONE:
            self.render_current_page()

    def _on_mousewheel(self, event):
        delta = event.delta if event.delta else (120 if event.num == 4 else -120)
        self.canvas.yview_scroll(-1 if delta > 0 else 1, "units")

    def _on_ctrl_mousewheel(self, event):
        delta = event.delta if event.delta else (120 if event.num == 4 else -120)
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _canvas_to_pdf(self, cx, cy):
        zoom = self.tab_state.zoom
        return cx / zoom, cy / zoom

    def _on_mouse_down(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        self._drag_start = (cx, cy)
        if self.annotation_tool == "ink":
            self._ink_points = [self._canvas_to_pdf(cx, cy)]
        elif self.annotation_tool is None:
            # starting a new text selection clears the old one
            self.tab_state.selected_words = []
            self.tab_state.selected_text = ""
            self.canvas.delete("selection")

    def _on_mouse_drag(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        if not self._drag_start:
            return

        if self.annotation_tool == "ink":
            self._ink_points.append(self._canvas_to_pdf(cx, cy))
            self.canvas.create_line(
                self._drag_start[0], self._drag_start[1], cx, cy,
                fill="#e02020", width=2, tags="ink_preview"
            )
            self._drag_start = (cx, cy)

        elif self.annotation_tool is None:
            # live text-selection preview
            self.canvas.delete("selection")
            px0, py0 = self._canvas_to_pdf(*self._drag_start)
            px1, py1 = self._canvas_to_pdf(cx, cy)
            rect = (min(px0, px1), min(py0, py1), max(px0, px1), max(py0, py1))
            words = self._get_words_for_current_page()
            hit_words = tex.words_in_rect(words, rect)
            zoom = self.tab_state.zoom
            for w in hit_words:
                x0, y0, x1, y1 = w[0] * zoom, w[1] * zoom, w[2] * zoom, w[3] * zoom
                self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill="#4a90d9", outline="", stipple="gray50", tags="selection"
                )

        else:
            # highlight / underline / strikeout / note: rectangle drag preview
            self.canvas.delete("drag_preview")
            x0, y0 = self._drag_start
            self.canvas.create_rectangle(x0, y0, cx, cy, outline="#e0a020", width=2, tags="drag_preview")

    def _on_mouse_up(self, event):
        if not self._drag_start:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        page = self.tab_state.pdf_doc.get_page(self.tab_state.current_page)

        if self.annotation_tool == "ink":
            if len(self._ink_points) > 1:
                self.tab_state.history.snapshot()
                ann.add_ink(page, [self._ink_points], color=self.annotation_color)
                self._notify_dirty()
            self._ink_points = []

        elif self.annotation_tool is None:
            # finalize the text selection (already drawn live in _on_mouse_drag)
            px0, py0 = self._canvas_to_pdf(*self._drag_start)
            px1, py1 = self._canvas_to_pdf(cx, cy)
            rect = (min(px0, px1), min(py0, py1), max(px0, px1), max(py0, py1))
            words = self._get_words_for_current_page()
            hit_words = tex.words_in_rect(words, rect)
            self.tab_state.selected_words = hit_words
            self.tab_state.selected_text = tex.words_to_text(hit_words)

        else:
            px0, py0 = self._canvas_to_pdf(*self._drag_start)
            px1, py1 = self._canvas_to_pdf(cx, cy)
            rect = (min(px0, px1), min(py0, py1), max(px0, px1), max(py0, py1))

            if self.annotation_tool == "note":
                self.tab_state.history.snapshot()
                ann.add_note(page, pymupdf.Point(px0, py0), "Note")
                self._notify_dirty()
            else:
                # snap to real text: use exact word quads under the drag if any exist,
                # otherwise fall back to the dragged rectangle (e.g. marking a diagram)
                words = self._get_words_for_current_page()
                hit_words = tex.words_in_rect(words, rect)
                if hit_words:
                    quads = [tex.word_rect(w).quad for w in hit_words]
                else:
                    r = pymupdf.Rect(*rect)
                    quads = [r.quad] if r.width > 2 and r.height > 2 else []

                if quads:
                    self.tab_state.history.snapshot()
                    for quad in quads:
                        if self.annotation_tool == "highlight":
                            ann.highlight_text(page, quad, color=self.annotation_color)
                        elif self.annotation_tool == "underline":
                            ann.underline_text(page, quad, color=self.annotation_color)
                        elif self.annotation_tool == "strikeout":
                            ann.strikeout_text(page, quad, color=self.annotation_color)
                    self._notify_dirty()

        self.canvas.delete("drag_preview")
        self.canvas.delete("ink_preview")
        self._drag_start = None
        self.render_current_page(force=True)

    def _on_right_click(self, event):
        menu = tk.Menu(self, tearoff=0)
        has_selection = bool(self.tab_state.selected_text)
        menu.add_command(
            label="Copy", command=self.copy_selection_to_clipboard,
            state="normal" if has_selection else "disabled",
        )
        menu.add_command(
            label="Highlight Selection", command=lambda: self._annotate_current_selection("highlight"),
            state="normal" if has_selection else "disabled",
        )
        menu.add_command(
            label="Underline Selection", command=lambda: self._annotate_current_selection("underline"),
            state="normal" if has_selection else "disabled",
        )
        menu.add_command(
            label="Strikeout Selection", command=lambda: self._annotate_current_selection("strikeout"),
            state="normal" if has_selection else "disabled",
        )
        menu.add_separator()
        menu.add_command(
            label="Read Selection Aloud", command=self.read_selection_aloud,
            state="normal" if (has_selection and self.tts) else "disabled",
        )
        menu.add_command(
            label="Read Page Aloud", command=self.read_page_aloud,
            state="normal" if self.tts else "disabled",
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _annotate_current_selection(self, tool):
        if not self.tab_state.selected_words:
            return
        page = self.tab_state.pdf_doc.get_page(self.tab_state.current_page)
        self.tab_state.history.snapshot()
        for w in self.tab_state.selected_words:
            quad = tex.word_rect(w).quad
            if tool == "highlight":
                ann.highlight_text(page, quad, color=self.annotation_color)
            elif tool == "underline":
                ann.underline_text(page, quad, color=self.annotation_color)
            elif tool == "strikeout":
                ann.strikeout_text(page, quad, color=self.annotation_color)
        self._notify_dirty()
        self.render_current_page(force=True)

    # ---- copy / read aloud ----
    def copy_selection_to_clipboard(self):
        text = self.tab_state.selected_text
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)

    def read_selection_aloud(self):
        if not self.tts:
            return
        text = self.tab_state.selected_text
        if not text:
            messagebox.showinfo("Read Aloud", "Select some text first.")
            return
        if not self.tts.speak(text):
            messagebox.showwarning(
                "Read Aloud",
                "No text-to-speech engine was found on this system. "
                "Install pyttsx3's platform requirement (e.g. espeak on Linux) and try again.",
            )

    def read_page_aloud(self):
        if not self.tts:
            return
        page = self.tab_state.pdf_doc.get_page(self.tab_state.current_page)
        text = tex.get_page_text(page)
        if not self.tts.speak(text):
            messagebox.showwarning(
                "Read Aloud",
                "No text-to-speech engine was found on this system, or this page has no "
                "extractable text (e.g. it's a scanned image without OCR).",
            )

    def stop_reading(self):
        if self.tts:
            self.tts.stop()

    def _notify_dirty(self):
        self.tab_state.pdf_doc.dirty = True
        self.page_cache.invalidate_document(id(self.tab_state.pdf_doc))
        self._invalidate_words_cache()
        if self.on_dirty:
            self.on_dirty()
