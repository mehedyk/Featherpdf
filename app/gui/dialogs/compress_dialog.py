"""
gui/dialogs/compress_dialog.py
DPI threshold + JPEG quality controls, with a live-ish size estimate.
"""
import tkinter as tk
from tkinter import ttk


class CompressDialog(tk.Toplevel):
    def __init__(self, parent, on_confirm, on_estimate, default_dpi=220, default_quality=82):
        super().__init__(parent)
        self.title("Compress PDF")
        self.geometry("380x260")
        self.on_confirm = on_confirm
        self.on_estimate = on_estimate

        tk.Label(
            self, text="Images above the DPI threshold will be downsampled.\n"
                       "Lower threshold = smaller file, more aggressive.",
            justify="left", wraplength=340,
        ).pack(pady=(10, 6), padx=10)

        dpi_frame = tk.Frame(self)
        dpi_frame.pack(fill="x", padx=10, pady=6)
        tk.Label(dpi_frame, text="Max DPI:").pack(side="left")
        self.dpi_var = tk.IntVar(value=default_dpi)
        ttk.Scale(dpi_frame, from_=100, to=400, variable=self.dpi_var, orient="horizontal",
                  command=lambda v: self.dpi_label.configure(text=str(int(float(v))))
                  ).pack(side="left", fill="x", expand=True, padx=6)
        self.dpi_label = tk.Label(dpi_frame, text=str(default_dpi), width=4)
        self.dpi_label.pack(side="left")

        q_frame = tk.Frame(self)
        q_frame.pack(fill="x", padx=10, pady=6)
        tk.Label(q_frame, text="JPEG Quality:").pack(side="left")
        self.quality_var = tk.IntVar(value=default_quality)
        ttk.Scale(q_frame, from_=50, to=95, variable=self.quality_var, orient="horizontal",
                  command=lambda v: self.quality_label.configure(text=str(int(float(v))))
                  ).pack(side="left", fill="x", expand=True, padx=6)
        self.quality_label = tk.Label(q_frame, text=str(default_quality), width=4)
        self.quality_label.pack(side="left")

        self.estimate_label = tk.Label(self, text="Click 'Estimate' to preview size reduction.")
        self.estimate_label.pack(pady=8)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=10)
        ttk.Button(bottom, text="Estimate", command=self._estimate).pack(side="left")
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bottom, text="Compress", command=self._confirm).pack(side="right", padx=4)

    def _estimate(self):
        current, estimated = self.on_estimate(self.dpi_var.get())
        pct = 100 * (1 - estimated / current) if current else 0
        self.estimate_label.configure(
            text=f"{current/1024:.0f} KB -> ~{estimated/1024:.0f} KB  (~{pct:.0f}% smaller)"
        )

    def _confirm(self):
        self.destroy()
        self.on_confirm(self.dpi_var.get(), self.quality_var.get())
