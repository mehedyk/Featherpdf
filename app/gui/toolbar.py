"""
gui/toolbar.py
The main horizontal toolbar: file ops, page navigation, zoom/fit controls,
rotate, and a slot for annotation tools (see annotation_toolbar.py, shown
as a second row when the Annotate tab is active).
"""
import tkinter as tk
from tkinter import ttk
from app.state.tab_state import FIT_NONE, FIT_WIDTH, FIT_PAGE, FIT_SCREEN


class Toolbar(tk.Frame):
    def __init__(self, parent, actions: dict):
        """actions: dict mapping action names to callables, e.g. actions['open']()"""
        super().__init__(parent, bg="#e8e8e8", bd=1, relief="raised")
        self.actions = actions
        self._build()

    def _btn(self, parent, text, action_name, width=None):
        return ttk.Button(
            parent, text=text, width=width,
            command=self.actions.get(action_name, lambda: None),
        )

    def _build(self):
        pad = {"padx": 2, "pady": 3}

        # Three stacked rows -- with this many buttons, even two rows can
        # exceed a normal window width and clip the trailing group. Splitting
        # into three keeps every row comfortably under ~1100px.
        row1 = tk.Frame(self, bg="#e8e8e8")
        row1.pack(side="top", fill="x")
        row2 = tk.Frame(self, bg="#e8e8e8")
        row2.pack(side="top", fill="x")
        row3 = tk.Frame(self, bg="#e8e8e8")
        row3.pack(side="top", fill="x")

        # --- Row 1: file, navigation, zoom ---
        file_grp = tk.Frame(row1, bg="#e8e8e8")
        file_grp.pack(side="left", padx=(4, 8))
        self._btn(file_grp, "Open", "open_file").pack(side="left", **pad)
        self._btn(file_grp, "Save", "save_file").pack(side="left", **pad)
        self._btn(file_grp, "Save As", "save_as").pack(side="left", **pad)

        ttk.Separator(row1, orient="vertical").pack(side="left", fill="y", padx=4, pady=4)

        nav_grp = tk.Frame(row1, bg="#e8e8e8")
        nav_grp.pack(side="left", padx=8)
        self._btn(nav_grp, "|<", "first_page", width=3).pack(side="left", **pad)
        self._btn(nav_grp, "<", "prev_page", width=3).pack(side="left", **pad)
        self.page_entry_var = tk.StringVar(value="1")
        page_entry = ttk.Entry(nav_grp, textvariable=self.page_entry_var, width=5)
        page_entry.pack(side="left", **pad)
        page_entry.bind("<Return>", lambda e: self.actions.get("goto_page_entry", lambda v: None)(
            self.page_entry_var.get()))
        self.page_count_label = tk.Label(nav_grp, text="/ 0", bg="#e8e8e8")
        self.page_count_label.pack(side="left", **pad)
        self._btn(nav_grp, ">", "next_page", width=3).pack(side="left", **pad)
        self._btn(nav_grp, ">|", "last_page", width=3).pack(side="left", **pad)

        ttk.Separator(row1, orient="vertical").pack(side="left", fill="y", padx=4, pady=4)

        zoom_grp = tk.Frame(row1, bg="#e8e8e8")
        zoom_grp.pack(side="left", padx=8)
        self._btn(zoom_grp, "-", "zoom_out", width=3).pack(side="left", **pad)
        self.zoom_label = tk.Label(zoom_grp, text="100%", bg="#e8e8e8", width=6)
        self.zoom_label.pack(side="left", **pad)
        self._btn(zoom_grp, "+", "zoom_in", width=3).pack(side="left", **pad)
        self._btn(zoom_grp, "100%", "zoom_reset", width=5).pack(side="left", **pad)

        fit_var = tk.StringVar(value=FIT_SCREEN)
        self.fit_combo = ttk.Combobox(
            zoom_grp, textvariable=fit_var, state="readonly", width=12,
            values=["Fit Width", "Fit Page", "Fit Screen", "Manual Zoom"],
        )
        self.fit_combo.set("Fit Screen")
        self.fit_combo.pack(side="left", **pad)
        self.fit_combo.bind("<<ComboboxSelected>>", self._on_fit_selected)

        # --- Row 2: edit, file tools, read aloud ---
        edit_grp = tk.Frame(row2, bg="#e8e8e8")
        edit_grp.pack(side="left", padx=(4, 8))
        self._btn(edit_grp, "Rotate ⟲", "rotate_left").pack(side="left", **pad)
        self._btn(edit_grp, "Rotate ⟳", "rotate_right").pack(side="left", **pad)
        self._btn(edit_grp, "Delete Page", "delete_page").pack(side="left", **pad)
        self._btn(edit_grp, "Undo", "undo").pack(side="left", **pad)
        self._btn(edit_grp, "Redo", "redo").pack(side="left", **pad)

        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=4, pady=4)

        tools_grp = tk.Frame(row2, bg="#e8e8e8")
        tools_grp.pack(side="left", padx=8)
        self._btn(tools_grp, "Merge", "merge_dialog").pack(side="left", **pad)
        self._btn(tools_grp, "Img → PDF", "convert_dialog").pack(side="left", **pad)
        self._btn(tools_grp, "Compress", "compress_dialog").pack(side="left", **pad)

        # --- Row 3: remaining tools + read aloud / copy ---
        tools_grp2 = tk.Frame(row3, bg="#e8e8e8")
        tools_grp2.pack(side="left", padx=(4, 8))
        self._btn(tools_grp2, "Print", "print_document").pack(side="left", **pad)
        self._btn(tools_grp2, "Dark Mode", "toggle_dark_mode").pack(side="left", **pad)

        ttk.Separator(row3, orient="vertical").pack(side="left", fill="y", padx=4, pady=4)

        read_grp = tk.Frame(row3, bg="#e8e8e8")
        read_grp.pack(side="left", padx=8)
        self._btn(read_grp, "🔊 Read Selection", "read_selection").pack(side="left", **pad)
        self._btn(read_grp, "🔊 Read Page", "read_page").pack(side="left", **pad)
        self._btn(read_grp, "⏹ Stop", "stop_reading").pack(side="left", **pad)
        ttk.Separator(row3, orient="vertical").pack(side="left", fill="y", padx=4, pady=4)
        self._btn(read_grp, "Copy", "copy_selection").pack(side="left", **pad)

    def _on_fit_selected(self, _event):
        mapping = {
            "Fit Width": FIT_WIDTH, "Fit Page": FIT_PAGE,
            "Fit Screen": FIT_SCREEN, "Manual Zoom": FIT_NONE,
        }
        mode = mapping[self.fit_combo.get()]
        self.actions.get("set_fit_mode", lambda m: None)(mode)

    def update_page_info(self, current_index, total):
        self.page_entry_var.set(str(current_index + 1))
        self.page_count_label.configure(text=f"/ {total}")

    def update_zoom_label(self, zoom):
        self.zoom_label.configure(text=f"{int(zoom * 100)}%")
