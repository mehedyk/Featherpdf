"""
gui/dialogs/goto_page_dialog.py
One-field "jump to page" prompt. Thin wrapper over simpledialog so the
caller doesn't need to import tkinter.simpledialog directly.
"""
from tkinter import simpledialog


def ask_page_number(parent, page_count, current_page_1indexed):
    return simpledialog.askinteger(
        "Go to Page",
        f"Page number (1-{page_count}):",
        parent=parent,
        minvalue=1,
        maxvalue=page_count,
        initialvalue=current_page_1indexed,
    )
