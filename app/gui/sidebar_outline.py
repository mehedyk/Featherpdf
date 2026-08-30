"""
gui/sidebar_outline.py
Displays the PDF's table of contents / bookmarks (if any) as a tree;
clicking an entry jumps to that page.
"""
import tkinter as tk
from tkinter import ttk


class OutlineSidebar(tk.Frame):
    def __init__(self, parent, on_jump):
        super().__init__(parent, bg="#d0d0d0")
        self.on_jump = on_jump

        self.tree = ttk.Treeview(self, show="tree")
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._page_by_item = {}

    def refresh(self, pdf_doc):
        self.tree.delete(*self.tree.get_children())
        self._page_by_item.clear()

        toc = pdf_doc.get_toc()
        if not toc:
            item = self.tree.insert("", "end", text="(No bookmarks in this PDF)")
            return

        # stack keeps track of the last inserted item at each level
        last_at_level = {0: ""}
        for level, title, page_num in toc:
            parent = last_at_level.get(level - 1, "")
            item = self.tree.insert(parent, "end", text=title, open=True)
            last_at_level[level] = item
            self._page_by_item[item] = max(0, page_num - 1)

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel and sel[0] in self._page_by_item:
            self.on_jump(self._page_by_item[sel[0]])
