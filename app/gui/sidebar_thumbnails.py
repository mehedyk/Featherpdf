"""
gui/sidebar_thumbnails.py
Scrollable list of page thumbnails. Click to jump, right-click for a
context menu (delete / move up / move down / insert blank before-after).
Drag-and-drop reordering is intentionally left as up/down buttons + context
menu instead of full DnD, which is fiddly in plain Tkinter and error-prone;
this keeps reordering fully reliable.
"""
import tkinter as tk
from PIL import ImageTk
from app.render.page_renderer import render_page_to_pil

THUMB_ZOOM = 0.18


class ThumbnailSidebar(tk.Frame):
    def __init__(self, parent, thumb_cache, on_jump, on_delete_page, on_insert_blank, on_move_page):
        super().__init__(parent, bg="#d0d0d0")
        self.thumb_cache = thumb_cache
        self.on_jump = on_jump
        self.on_delete_page = on_delete_page
        self.on_insert_blank = on_insert_blank
        self.on_move_page = on_move_page

        self.canvas = tk.Canvas(self, bg="#d0d0d0", highlightthickness=0, width=140)
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg="#d0d0d0")
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")

        self._tk_images = []
        self._current_doc = None
        self._current_page = -1

    def refresh(self, pdf_doc, current_page):
        self._current_doc = pdf_doc
        self._current_page = current_page
        for w in self.inner.winfo_children():
            w.destroy()
        self._tk_images.clear()

        for i in range(pdf_doc.page_count):
            key = self.thumb_cache.make_key(id(pdf_doc), i, THUMB_ZOOM)
            pil_img = self.thumb_cache.get(key)
            if pil_img is None:
                page = pdf_doc.get_page(i)
                pil_img = render_page_to_pil(page, zoom=THUMB_ZOOM)
                self.thumb_cache.put(key, pil_img)
            tk_img = ImageTk.PhotoImage(pil_img)
            self._tk_images.append(tk_img)

            frame = tk.Frame(
                self.inner, bg="#4a90d9" if i == current_page else "#d0d0d0",
                bd=2, relief="solid" if i == current_page else "flat",
            )
            frame.pack(pady=4, padx=6, fill="x")
            lbl = tk.Label(frame, image=tk_img, bg="white")
            lbl.pack()
            num_lbl = tk.Label(frame, text=f"Page {i + 1}", bg=frame["bg"])
            num_lbl.pack()

            for widget in (frame, lbl, num_lbl):
                widget.bind("<Button-1>", lambda e, idx=i: self.on_jump(idx))
                widget.bind("<Button-3>", lambda e, idx=i: self._show_context_menu(e, idx))

    def _show_context_menu(self, event, index):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Delete Page", command=lambda: self.on_delete_page(index))
        menu.add_command(label="Insert Blank Before", command=lambda: self.on_insert_blank(index))
        menu.add_command(label="Insert Blank After", command=lambda: self.on_insert_blank(index + 1))
        menu.add_separator()
        menu.add_command(label="Move Up", command=lambda: self.on_move_page(index, max(0, index - 1)))
        menu.add_command(label="Move Down", command=lambda: self.on_move_page(index, index + 1))
        menu.tk_popup(event.x_root, event.y_root)
