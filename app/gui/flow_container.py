"""
gui/flow_container.py
A simple auto-wrapping ("flow layout") panel: lays child widgets out
left-to-right, wrapping to a new row whenever the current row would
exceed the container's available width, and recomputes on every resize.

This is what makes the toolbar "fit the window" instead of using a fixed
number of rows -- one row on a wide window, several rows on a narrow one,
and the panel's own height grows/shrinks to match however many rows that
takes. Nothing gets silently clipped off the edge the way a plain packed
row does once it runs out of horizontal space.
"""
import tkinter as tk


class FlowToolbar(tk.Frame):
    def __init__(self, parent, bg="#e8e8e8", item_pad=4, row_pad=4, group_gap=14):
        super().__init__(parent, bg=bg)
        self.bg = bg
        self.item_pad = item_pad
        self.row_pad = row_pad
        self.group_gap = group_gap
        self._items = []          # list of (widget, gap_before_this_item)
        self._last_width = None
        self.pack_propagate(False)   # height is set explicitly in _reflow, not derived from children
        self.bind("<Configure>", self._on_configure)

    def add_button(self, text, command, width=None, new_group=False):
        from tkinter import ttk
        btn = ttk.Button(self, text=text, width=width, command=command)
        return self.add_widget(btn, new_group=new_group)

    def add_widget(self, widget, new_group=False):
        gap = self.group_gap if (new_group and self._items) else self.item_pad
        self._items.append((widget, gap))
        self.after_idle(self._reflow)
        return widget

    def _on_configure(self, event):
        if event.width != self._last_width:
            self._last_width = event.width
            self._reflow()

    def _reflow(self):
        if not self._items:
            return
        available = self.winfo_width()
        if available <= 1:
            available = self.winfo_reqwidth() or 900

        x = self.item_pad
        y = self.row_pad
        row_height = 0
        first_in_row = True

        for widget, gap in self._items:
            widget.update_idletasks()
            w = widget.winfo_reqwidth()
            h = widget.winfo_reqheight()
            eff_gap = 0 if first_in_row else gap

            if not first_in_row and (x + eff_gap + w > available):
                x = self.item_pad
                y += row_height + self.row_pad
                row_height = 0
                first_in_row = True
                eff_gap = 0

            place_x = x + eff_gap
            widget.place(x=place_x, y=y, width=w, height=h)
            x = place_x + w
            row_height = max(row_height, h)
            first_in_row = False

        total_height = y + row_height + self.row_pad
        if self.winfo_reqheight() != total_height:
            self.configure(height=total_height)
