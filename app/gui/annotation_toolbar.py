"""
gui/annotation_toolbar.py
Tool + color selection for the ViewerCanvas's click-drag annotation mode.
Built on FlowToolbar so it wraps gracefully on narrow windows too.
"""
import tkinter as tk
from tkinter import ttk
from app.core import annotations as ann
from app.gui.flow_container import FlowToolbar

COLORS = {
    "Yellow": ann.COLOR_YELLOW,
    "Green": ann.COLOR_GREEN,
    "Red": ann.COLOR_RED,
    "Blue": ann.COLOR_BLUE,
}


class AnnotationToolbar(FlowToolbar):
    def __init__(self, parent, on_tool_change, on_color_change):
        super().__init__(parent, bg="#f0f0f0")
        self.on_tool_change = on_tool_change
        self.on_color_change = on_color_change
        self.tool_var = tk.StringVar(value="select")
        self._build()

    def _build(self):
        label = tk.Label(self, text="Tool:", bg=self.bg)
        self.add_widget(label)

        tools = [
            ("Select / Copy", "select"), ("Highlight", "highlight"), ("Underline", "underline"),
            ("Strikeout", "strikeout"), ("Sticky Note", "note"), ("Freehand", "ink"),
        ]
        for tlabel, value in tools:
            rb = ttk.Radiobutton(
                self, text=tlabel, value=value, variable=self.tool_var,
                command=self._on_tool_selected,
            )
            self.add_widget(rb)

        color_label = tk.Label(self, text="Color:", bg=self.bg)
        self.add_widget(color_label, new_group=True)

        self.color_var = tk.StringVar(value="Yellow")
        color_combo = ttk.Combobox(
            self, textvariable=self.color_var, state="readonly", width=8,
            values=list(COLORS.keys()),
        )
        color_combo.bind("<<ComboboxSelected>>", self._on_color_selected)
        self.add_widget(color_combo)

    def _on_tool_selected(self):
        tool = self.tool_var.get()
        self.on_tool_change(None if tool == "select" else tool)

    def _on_color_selected(self, _event):
        self.on_color_change(COLORS[self.color_var.get()])
