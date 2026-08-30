"""
utils/file_dialogs.py
Thin wrappers over tkinter's native file dialogs so GUI modules don't
import tkinter.filedialog directly everywhere.
"""
from tkinter import filedialog

PDF_FILETYPES = [("PDF files", "*.pdf"), ("All files", "*.*")]
IMAGE_FILETYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
    ("All files", "*.*"),
]


def ask_open_pdf(multiple=False):
    if multiple:
        return list(filedialog.askopenfilenames(title="Open PDF", filetypes=PDF_FILETYPES))
    path = filedialog.askopenfilename(title="Open PDF", filetypes=PDF_FILETYPES)
    return path or None


def ask_open_images():
    return list(filedialog.askopenfilenames(title="Select images", filetypes=IMAGE_FILETYPES))


def ask_save_pdf(initial_name="document.pdf"):
    path = filedialog.asksaveasfilename(
        title="Save PDF",
        defaultextension=".pdf",
        initialfile=initial_name,
        filetypes=PDF_FILETYPES,
    )
    return path or None


def ask_save_folder():
    path = filedialog.askdirectory(title="Choose output folder")
    return path or None
