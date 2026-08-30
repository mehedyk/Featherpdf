"""
gui/dialogs/merge_dialog.py
Pick files, arrange order (up/down), confirm -> returns ordered path list.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from app.utils.file_dialogs import ask_open_pdf


class MergeDialog(tk.Toplevel):
    def __init__(self, parent, on_confirm):
        super().__init__(parent)
        self.title("Merge PDFs")
        self.geometry("420x360")
        self.on_confirm = on_confirm
        self.paths = []

        tk.Label(self, text="Add PDFs, then arrange the order:").pack(pady=(10, 4))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10)
        self.listbox = tk.Listbox(list_frame, selectmode="single")
        sb = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        btn_row = tk.Frame(self)
        btn_row.pack(fill="x", padx=10, pady=6)
        ttk.Button(btn_row, text="Add Files...", command=self._add_files).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Remove", command=self._remove_selected).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Move Up", command=lambda: self._move(-1)).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Move Down", command=lambda: self._move(1)).pack(side="left", padx=2)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=10)
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bottom, text="Merge", command=self._confirm).pack(side="right", padx=4)

    def _add_files(self):
        new_paths = ask_open_pdf(multiple=True)
        for p in new_paths:
            self.paths.append(p)
            self.listbox.insert("end", p)

    def _remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.listbox.delete(idx)
        del self.paths[idx]

    def _move(self, direction):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.paths):
            self.paths[idx], self.paths[new_idx] = self.paths[new_idx], self.paths[idx]
            text = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(new_idx, text)
            self.listbox.selection_set(new_idx)

    def _confirm(self):
        if len(self.paths) < 2:
            messagebox.showwarning("Merge PDFs", "Add at least two PDF files to merge.")
            return
        self.destroy()
        self.on_confirm(self.paths)
