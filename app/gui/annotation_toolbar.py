"""
gui/annotation_toolbar.py
Tool + color selection for the ViewerCanvas's click-drag annotation mode.
"""
import tkinter as tk
from tkinter import ttk
from app.core import annotations as ann

COLORS = {
    "Yellow": ann.COLOR_YELLOW,
    "Green": ann.COLOR_GREEN,
    "Red": ann.COLOR_RED,
    "Blue": ann.COLOR_BLUE,
}


class AnnotationToolbar(tk.Frame):
    def __init__(self, parent, on_tool_change, on_color_change):
        super().__init__(parent, bg="#f0f0f0", bd=1, relief="sunken")
        self.on_tool_change = on_tool_change
        self.on_color_change = on_color_change
        self.tool_var = tk.StringVar(value="select")
        self._build()

    def _build(self):
        pad = {"padx": 3, "pady": 3}
        tools = [
            ("Select / Copy", "select"), ("Highlight", "highlight"), ("Underline", "underline"),
            ("Strikeout", "strikeout"), ("Sticky Note", "note"), ("Freehand", "ink"),
        ]
        tk.Label(self, text="Tool:", bg="#f0f0f0").pack(side="left", **pad)
        for label, value in tools:
            ttk.Radiobutton(
                self, text=label, value=value, variable=self.tool_var,
                command=self._on_tool_selected,
            ).pack(side="left", **pad)

        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=6)
        tk.Label(self, text="Color:", bg="#f0f0f0").pack(side="left", **pad)
        self.color_var = tk.StringVar(value="Yellow")
        color_combo = ttk.Combobox(
            self, textvariable=self.color_var, state="readonly", width=8,
            values=list(COLORS.keys()),
        )
        color_combo.pack(side="left", **pad)
        color_combo.bind("<<ComboboxSelected>>", self._on_color_selected)

    def _on_tool_selected(self):
        tool = self.tool_var.get()
        self.on_tool_change(None if tool == "select" else tool)

    def _on_color_selected(self, _event):
        self.on_color_change(COLORS[self.color_var.get()])
