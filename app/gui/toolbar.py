"""
gui/toolbar.py
The main toolbar: file ops, page navigation, zoom/fit controls, rotate,
file tools, and read-aloud controls. Built on FlowToolbar so it always
wraps to fit the current window width -- fewer rows when the window is
wide, more when it's narrow -- instead of a fixed row count that can
either waste space or clip buttons off the edge.
"""
import tkinter as tk
from tkinter import ttk
from app.state.tab_state import FIT_NONE, FIT_WIDTH, FIT_PAGE, FIT_SCREEN
from app.gui.flow_container import FlowToolbar


class Toolbar(FlowToolbar):
    def __init__(self, parent, actions: dict):
        super().__init__(parent, bg="#e8e8e8")
        self.actions = actions
        self._build()

    def _btn(self, text, action_name, width=None, new_group=False):
        return self.add_button(
            text, self.actions.get(action_name, lambda: None), width=width, new_group=new_group,
        )

    def _build(self):
        self._btn("Open", "open_file")
        self._btn("Save", "save_file")
        self._btn("Save As", "save_as")

        self._btn("|<", "first_page", width=3, new_group=True)
        self._btn("<", "prev_page", width=3)

        entry_frame = tk.Frame(self, bg=self.bg)
        self.page_entry_var = tk.StringVar(value="1")
        page_entry = ttk.Entry(entry_frame, textvariable=self.page_entry_var, width=5)
        page_entry.pack(side="left")
        page_entry.bind("<Return>", lambda e: self.actions.get("goto_page_entry", lambda v: None)(
            self.page_entry_var.get()))
        self.page_count_label = tk.Label(entry_frame, text="/ 0", bg=self.bg)
        self.page_count_label.pack(side="left", padx=(4, 0))
        self.add_widget(entry_frame)

        self._btn(">", "next_page", width=3)
        self._btn(">|", "last_page", width=3)

        self._btn("-", "zoom_out", width=3, new_group=True)
        self.zoom_label = tk.Label(self, text="100%", bg=self.bg, width=6)
        self.add_widget(self.zoom_label)
        self._btn("+", "zoom_in", width=3)
        self._btn("100%", "zoom_reset", width=5)

        fit_var = tk.StringVar(value=FIT_SCREEN)
        self.fit_combo = ttk.Combobox(
            self, textvariable=fit_var, state="readonly", width=12,
            values=["Fit Width", "Fit Page", "Fit Screen", "Manual Zoom"],
        )
        self.fit_combo.set("Fit Screen")
        self.fit_combo.bind("<<ComboboxSelected>>", self._on_fit_selected)
        self.add_widget(self.fit_combo)

        self._btn("Rotate ⟲", "rotate_left", new_group=True)
        self._btn("Rotate ⟳", "rotate_right")
        self._btn("Delete Page", "delete_page")
        self._btn("Undo", "undo")
        self._btn("Redo", "redo")

        self._btn("Merge", "merge_dialog", new_group=True)
        self._btn("Img → PDF", "convert_dialog")
        self._btn("Compress", "compress_dialog")
        self._btn("Print", "print_document")
        self._btn("Dark Mode", "toggle_dark_mode")

        self._btn("🔊 Read Selection", "read_selection", new_group=True)
        self._btn("🔊 Read Page", "read_page")
        self._btn("⏹ Stop", "stop_reading")
        self._btn("Slower", "tts_slower")
        self.tts_speed_label = tk.Label(self, text="1.0x", bg=self.bg, width=4)
        self.add_widget(self.tts_speed_label)
        self._btn("Faster", "tts_faster")
        self._btn("Copy", "copy_selection")

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

    def update_tts_speed_label(self, mult):
        self.tts_speed_label.configure(text=f"{mult:.2g}x")
