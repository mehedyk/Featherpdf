"""
gui/dialogs/page_range_dialog.py
Generic "enter a page range" prompt used by extract-pages, delete-range,
and split-by-range operations. Validates against the doc's page count
via core.merge_split.parse_page_range_string.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from app.core.merge_split import parse_page_range_string


class PageRangeDialog(tk.Toplevel):
    def __init__(self, parent, page_count, title, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.geometry("360x160")
        self.page_count = page_count
        self.on_confirm = on_confirm

        tk.Label(
            self, text=f"Document has {page_count} pages.\n"
                       "Enter pages/ranges, e.g. 1-3,5,8-10",
            justify="left",
        ).pack(pady=(14, 6), padx=10)

        self.range_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.range_var, width=30)
        entry.pack(pady=6)
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._confirm())

        bottom = tk.Frame(self)
        bottom.pack(pady=10)
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(bottom, text="OK", command=self._confirm).pack(side="left", padx=6)

    def _confirm(self):
        try:
            indices = parse_page_range_string(self.range_var.get(), self.page_count)
        except ValueError as e:
            messagebox.showerror("Invalid range", str(e))
            return
        self.destroy()
        self.on_confirm(indices)
