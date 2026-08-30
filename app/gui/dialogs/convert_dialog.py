"""
gui/dialogs/convert_dialog.py
Pick images, choose scan effect mode and page-size behavior, confirm.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from app.utils.file_dialogs import ask_open_images
from app.core.scan_effect import MODE_COLOR, MODE_GRAY, MODE_BW


class ConvertDialog(tk.Toplevel):
    def __init__(self, parent, on_confirm):
        super().__init__(parent)
        self.title("Images to PDF")
        self.geometry("420x400")
        self.on_confirm = on_confirm
        self.paths = []

        tk.Label(self, text="Add images (in the order they should appear):").pack(pady=(10, 4))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10)
        self.listbox = tk.Listbox(list_frame, selectmode="single")
        sb = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        btn_row = tk.Frame(self)
        btn_row.pack(fill="x", padx=10, pady=6)
        ttk.Button(btn_row, text="Add Images...", command=self._add_files).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Remove", command=self._remove_selected).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Move Up", command=lambda: self._move(-1)).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Move Down", command=lambda: self._move(1)).pack(side="left", padx=2)

        opts = tk.LabelFrame(self, text="Document Style")
        opts.pack(fill="x", padx=10, pady=6)
        self.effect_var = tk.StringVar(value="none")
        ttk.Radiobutton(opts, text="No effect (keep as photographed)", value="none",
                         variable=self.effect_var).pack(anchor="w", padx=6, pady=2)
        ttk.Radiobutton(opts, text="Color document (contrast + sharpen)", value=MODE_COLOR,
                         variable=self.effect_var).pack(anchor="w", padx=6, pady=2)
        ttk.Radiobutton(opts, text="Grayscale document", value=MODE_GRAY,
                         variable=self.effect_var).pack(anchor="w", padx=6, pady=2)
        ttk.Radiobutton(opts, text="Black & white scan (CamScanner-style)", value=MODE_BW,
                         variable=self.effect_var).pack(anchor="w", padx=6, pady=2)

        size_frame = tk.LabelFrame(self, text="Page Size")
        size_frame.pack(fill="x", padx=10, pady=6)
        self.size_var = tk.StringVar(value="fit")
        ttk.Radiobutton(size_frame, text="Match each image's aspect ratio", value="fit",
                         variable=self.size_var).pack(anchor="w", padx=6, pady=2)
        ttk.Radiobutton(size_frame, text="Fixed A4, image centered", value="a4",
                         variable=self.size_var).pack(anchor="w", padx=6, pady=2)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=10)
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bottom, text="Convert", command=self._confirm).pack(side="right", padx=4)

    def _add_files(self):
        new_paths = ask_open_images()
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
        if not self.paths:
            messagebox.showwarning("Images to PDF", "Add at least one image.")
            return
        scan_mode = None if self.effect_var.get() == "none" else self.effect_var.get()
        self.destroy()
        self.on_confirm(self.paths, scan_mode, self.size_var.get())
