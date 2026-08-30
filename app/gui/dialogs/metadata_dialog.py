"""
gui/dialogs/metadata_dialog.py
Edit title/author/subject/keywords, and optionally save an encrypted copy.
"""
import tkinter as tk
from tkinter import ttk
from app.core.metadata import STANDARD_FIELDS


class MetadataDialog(tk.Toplevel):
    def __init__(self, parent, current_meta, on_save_metadata, on_save_encrypted):
        super().__init__(parent)
        self.title("Document Properties")
        self.geometry("380x340")
        self.on_save_metadata = on_save_metadata
        self.on_save_encrypted = on_save_encrypted
        self.vars = {}

        form = tk.Frame(self)
        form.pack(fill="x", padx=10, pady=10)
        for i, field in enumerate(STANDARD_FIELDS):
            tk.Label(form, text=field.capitalize() + ":").grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=current_meta.get(field, ""))
            self.vars[field] = var
            ttk.Entry(form, textvariable=var, width=30).grid(row=i, column=1, pady=3, padx=6)

        ttk.Button(self, text="Save Metadata", command=self._save_meta).pack(pady=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=6)

        pw_frame = tk.LabelFrame(self, text="Password Protect (Save As encrypted copy)")
        pw_frame.pack(fill="x", padx=10, pady=6)
        tk.Label(pw_frame, text="Password:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.pw_var = tk.StringVar()
        ttk.Entry(pw_frame, textvariable=self.pw_var, show="*", width=20).grid(row=0, column=1, padx=6)
        ttk.Button(pw_frame, text="Save Encrypted Copy...", command=self._save_encrypted).grid(
            row=1, column=0, columnspan=2, pady=6)

    def _save_meta(self):
        fields = {k: v.get() for k, v in self.vars.items()}
        self.on_save_metadata(fields)

    def _save_encrypted(self):
        pw = self.pw_var.get()
        if pw:
            self.on_save_encrypted(pw)
