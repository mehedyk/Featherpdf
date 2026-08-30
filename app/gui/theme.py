"""
gui/theme.py
Very small theme system: a couple of palettes applied to ttk styles.
Page rendering dark-mode (inverted colors) is handled separately in
render/page_renderer.py -- this module is just the app CHROME (toolbars,
sidebars, menus), not the PDF page content itself.
"""
from tkinter import ttk

LIGHT = {
    "bg": "#f0f0f0",
    "fg": "#202020",
    "accent": "#4a90d9",
}

DARK = {
    "bg": "#2b2b2b",
    "fg": "#e0e0e0",
    "accent": "#4a90d9",
}


def apply_theme(root, palette_name="light"):
    palette = DARK if palette_name == "dark" else LIGHT
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(".", background=palette["bg"], foreground=palette["fg"])
    style.configure("TButton", background=palette["bg"], foreground=palette["fg"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    root.configure(bg=palette["bg"])
    return palette
