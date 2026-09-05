"""
gui/main_window.py
Root window. Owns the menu bar, toolbar, sidebar notebook (thumbnails /
outline / search), and the tab manager. This is the "conductor" module --
it doesn't implement PDF logic itself, it calls into core/ and updates
state/, then asks the relevant GUI piece to refresh.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from app.core.document import PDFDocument
from app.core.merge_split import merge_pdfs, parse_page_range_string
from app.core.convert import images_to_pdf
from app.core.auto_crop import OpenCVNotAvailable
from app.core.compress import compress_pdf, estimate_size_reduction
from app.core.metadata import get_display_metadata, update_metadata, save_with_password
from app.core.tts import TextToSpeech, TTS_AVAILABLE

from app.render.page_cache import LRUImageCache
from app.render.thumbnail_cache import ThumbnailCache

from app.state.app_state import AppState
from app.state.tab_state import TabState, FIT_NONE, FIT_WIDTH, FIT_PAGE, FIT_SCREEN

from app.gui.toolbar import Toolbar
from app.gui.annotation_toolbar import AnnotationToolbar
from app.gui.tab_manager import TabManager
from app.gui.sidebar_thumbnails import ThumbnailSidebar
from app.gui.sidebar_outline import OutlineSidebar
from app.gui.sidebar_search import SearchSidebar
from app.gui.theme import apply_theme

from app.gui.dialogs.merge_dialog import MergeDialog
from app.gui.dialogs.convert_dialog import ConvertDialog
from app.gui.dialogs.compress_dialog import CompressDialog
from app.gui.dialogs.metadata_dialog import MetadataDialog
from app.gui.dialogs.page_range_dialog import PageRangeDialog
from app.gui.dialogs.goto_page_dialog import ask_page_number

from app.utils.file_dialogs import ask_open_pdf, ask_save_pdf
from app.utils.shortcuts import bind_all_shortcuts
from app.utils.printing import print_pdf
from app.utils.logger import get_logger

log = get_logger()


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FeatherPDF")
        self.geometry("1200x800")

        self.app_state = AppState()
        self.page_cache = LRUImageCache(max_items=12)
        self.thumb_cache = ThumbnailCache(max_items=80)
        self.tts = TextToSpeech()

        apply_theme(self, self.app_state.settings.get("theme", "light"))

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        bind_all_shortcuts(self, self._shortcut_handlers())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Document Properties...", command=self.open_metadata_dialog)
        file_menu.add_command(label="Print...", command=self.print_document, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_active_tab, accelerator="Ctrl+W")
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete Page", command=self.delete_current_page)
        edit_menu.add_command(label="Delete Page Range...", command=self.delete_page_range)
        edit_menu.add_command(label="Insert Blank Page", command=self.insert_blank_page)
        edit_menu.add_command(label="Rotate Left", command=lambda: self.rotate_page(-90))
        edit_menu.add_command(label="Rotate Right", command=lambda: self.rotate_page(90))
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy Selected Text", command=self.copy_selection, accelerator="Ctrl+C")
        edit_menu.add_command(label="Read Selection Aloud", command=self.read_selection_aloud)
        edit_menu.add_command(label="Read Page Aloud", command=self.read_page_aloud)
        edit_menu.add_command(label="Stop Reading", command=self.stop_reading)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Actual Size", command=self.zoom_reset, accelerator="Ctrl+0")
        view_menu.add_command(label="Fit Width", command=lambda: self.set_fit_mode(FIT_WIDTH))
        view_menu.add_command(label="Fit Page", command=lambda: self.set_fit_mode(FIT_PAGE))
        view_menu.add_command(label="Fit Screen", command=lambda: self.set_fit_mode(FIT_SCREEN))
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Dark Mode (page)", command=self.toggle_dark_mode)
        view_menu.add_command(label="Toggle Full Screen", command=self.toggle_fullscreen, accelerator="F11")
        menubar.add_cascade(label="View", menu=view_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Merge PDFs...", command=self.open_merge_dialog, accelerator="Ctrl+M")
        tools_menu.add_command(label="Images to PDF...", command=self.open_convert_dialog)
        tools_menu.add_command(label="Compress PDF...", command=self.open_compress_dialog)
        tools_menu.add_command(label="Extract Pages...", command=self.extract_pages_dialog)
        tools_menu.add_command(label="Split Every N Pages...", command=self.split_every_n_dialog)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.configure(menu=menubar)

    def _build_toolbar(self):
        actions = {
            "open_file": self.open_file,
            "save_file": self.save_file,
            "save_as": self.save_as,
            "first_page": lambda: self.goto_page(0),
            "prev_page": self.prev_page,
            "next_page": self.next_page,
            "last_page": lambda: self.goto_page(self._active_tab_state().pdf_doc.page_count - 1)
            if self._active_tab_state() else None,
            "goto_page_entry": self._goto_page_from_entry,
            "zoom_in": self.zoom_in,
            "zoom_out": self.zoom_out,
            "zoom_reset": self.zoom_reset,
            "set_fit_mode": self.set_fit_mode,
            "rotate_left": lambda: self.rotate_page(-90),
            "rotate_right": lambda: self.rotate_page(90),
            "delete_page": self.delete_current_page,
            "undo": self.undo,
            "redo": self.redo,
            "merge_dialog": self.open_merge_dialog,
            "convert_dialog": self.open_convert_dialog,
            "compress_dialog": self.open_compress_dialog,
            "print_document": self.print_document,
            "toggle_dark_mode": self.toggle_dark_mode,
            "read_selection": self.read_selection_aloud,
            "read_page": self.read_page_aloud,
            "stop_reading": self.stop_reading,
            "copy_selection": self.copy_selection,
        }
        self.toolbar = Toolbar(self, actions)
        self.toolbar.pack(side="top", fill="x")

        self.annotation_toolbar = AnnotationToolbar(
            self, on_tool_change=self._set_annotation_tool, on_color_change=self._set_annotation_color,
        )
        self.annotation_toolbar.pack(side="top", fill="x")

    def _build_body(self):
        self.body = tk.PanedWindow(self, orient="horizontal", sashrelief="raised")
        self.body.pack(fill="both", expand=True)

        # left: sidebar with its own mini-notebook (thumbnails / outline / search)
        self.sidebar_notebook = ttk.Notebook(self.body)
        self.thumb_sidebar = ThumbnailSidebar(
            self.sidebar_notebook, self.thumb_cache,
            on_jump=self.goto_page,
            on_delete_page=self.delete_page_at,
            on_insert_blank=self.insert_blank_page_at,
            on_move_page=self.move_page,
        )
        self.outline_sidebar = OutlineSidebar(self.sidebar_notebook, on_jump=self.goto_page)
        self.search_sidebar = SearchSidebar(
            self.sidebar_notebook, get_active_tab=self._active_tab_state, on_navigate=self.goto_page,
        )
        self.sidebar_notebook.add(self.thumb_sidebar, text="Pages")
        self.sidebar_notebook.add(self.outline_sidebar, text="Bookmarks")
        self.sidebar_notebook.add(self.search_sidebar, text="Search")
        self.body.add(self.sidebar_notebook, width=220)

        # right: the tab manager (one ViewerCanvas per open PDF)
        self.tab_manager = TabManager(
            self.body, self.page_cache,
            on_tab_changed=self._on_tab_changed,
            on_page_changed=self._on_page_changed,
            on_dirty=self._on_doc_dirty,
            tts=self.tts,
        )
        self.body.add(self.tab_manager)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        bar = tk.Label(self, textvariable=self.status_var, anchor="w", bd=1, relief="sunken")
        bar.pack(side="bottom", fill="x")

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _active_tab_state(self):
        return self.app_state.get_active_tab()

    def _active_canvas(self):
        return self.tab_manager.get_active_canvas()

    def _set_status(self, text):
        self.status_var.set(text)

    def _refresh_sidebars(self):
        tab = self._active_tab_state()
        if not tab:
            return
        self.thumb_sidebar.refresh(tab.pdf_doc, tab.current_page)
        self.outline_sidebar.refresh(tab.pdf_doc)

    def _on_tab_changed(self, tab_id):
        self.app_state.active_tab_id = tab_id
        self._refresh_sidebars()
        tab = self._active_tab_state()
        if tab:
            self.toolbar.update_page_info(tab.current_page, tab.pdf_doc.page_count)
            self.toolbar.update_zoom_label(tab.zoom)

    def _on_page_changed(self, current_index, total):
        self.toolbar.update_page_info(current_index, total)
        tab = self._active_tab_state()
        if tab:
            self.toolbar.update_zoom_label(tab.zoom)
            self.thumb_sidebar.refresh(tab.pdf_doc, tab.current_page)

    def _on_doc_dirty(self):
        tab = self._active_tab_state()
        if tab:
            self.tab_manager.rename_tab(tab)
            self.thumb_sidebar.refresh(tab.pdf_doc, tab.current_page)

    def _set_annotation_tool(self, tool):
        canvas = self._active_canvas()
        if canvas:
            canvas.annotation_tool = tool

    def _set_annotation_color(self, color):
        canvas = self._active_canvas()
        if canvas:
            canvas.annotation_color = color

    # ------------------------------------------------------------------
    # file operations
    # ------------------------------------------------------------------
    def open_file(self):
        paths = ask_open_pdf(multiple=True)
        if not paths:
            return
        for path in paths:
            self._open_path_in_new_tab(path)

    def _open_path_in_new_tab(self, path):
        try:
            pdf_doc = PDFDocument(path)
            if pdf_doc.password_protected:
                pw = simpledialog.askstring("Password Required", f"Enter password for {os.path.basename(path)}:", show="*")
                if pw is None or not pdf_doc.authenticate(pw):
                    messagebox.showerror("Open PDF", "Incorrect password or cancelled.")
                    return
        except Exception as e:
            messagebox.showerror("Open PDF", f"Could not open file:\n{e}")
            log.exception("Failed to open %s", path)
            return

        tab = TabState(pdf_doc, os.path.basename(path))
        self.app_state.add_tab(tab)
        self.tab_manager.open_tab(tab)
        self.app_state.add_recent_file(path)
        self._refresh_sidebars()
        self._set_status(f"Opened {path}")

    def save_file(self):
        tab = self._active_tab_state()
        if not tab:
            return
        if not tab.pdf_doc.path:
            self.save_as()
            return
        try:
            tab.pdf_doc.save()
            self.tab_manager.rename_tab(tab)
            self._set_status(f"Saved {tab.pdf_doc.path}")
        except Exception as e:
            messagebox.showerror("Save", f"Could not save file:\n{e}")

    def save_as(self):
        tab = self._active_tab_state()
        if not tab:
            return
        path = ask_save_pdf(initial_name=tab.title or "document.pdf")
        if not path:
            return
        try:
            tab.pdf_doc.save(path)
            tab.title = os.path.basename(path)
            self.tab_manager.rename_tab(tab)
            self._set_status(f"Saved {path}")
        except Exception as e:
            messagebox.showerror("Save As", f"Could not save file:\n{e}")

    def close_active_tab(self):
        tab = self._active_tab_state()
        if not tab:
            return
        if tab.pdf_doc.dirty:
            if not messagebox.askyesno("Close Tab", "This document has unsaved changes. Close anyway?"):
                return
        self.page_cache.invalidate_document(id(tab.pdf_doc))
        self.thumb_cache.invalidate_document(id(tab.pdf_doc))
        tab.pdf_doc.close()
        self.tab_manager.close_tab(tab.id)
        self.app_state.close_tab(tab.id)
        self._refresh_sidebars()

    def print_document(self):
        tab = self._active_tab_state()
        if not tab:
            return
        if tab.pdf_doc.dirty or not tab.pdf_doc.path:
            messagebox.showinfo("Print", "Please save the document before printing.")
            return
        print_pdf(tab.pdf_doc.path)
        self._set_status("Sent to printer.")

    # ------------------------------------------------------------------
    # navigation / zoom
    # ------------------------------------------------------------------
    def goto_page(self, index):
        canvas = self._active_canvas()
        if canvas:
            canvas.goto_page(index)

    def next_page(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.next_page()

    def prev_page(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.prev_page()

    def _goto_page_from_entry(self, value):
        tab = self._active_tab_state()
        if not tab:
            return
        try:
            page_num = int(value) - 1
        except ValueError:
            return
        if 0 <= page_num < tab.pdf_doc.page_count:
            self.goto_page(page_num)

    def goto_page_prompt(self):
        tab = self._active_tab_state()
        if not tab:
            return
        result = ask_page_number(self, tab.pdf_doc.page_count, tab.current_page + 1)
        if result:
            self.goto_page(result - 1)

    def zoom_in(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.zoom_in()
            self.toolbar.update_zoom_label(canvas.tab_state.zoom)

    def zoom_out(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.zoom_out()
            self.toolbar.update_zoom_label(canvas.tab_state.zoom)

    def zoom_reset(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.zoom_reset()
            self.toolbar.update_zoom_label(canvas.tab_state.zoom)

    def set_fit_mode(self, mode):
        canvas = self._active_canvas()
        if canvas:
            canvas.set_fit_mode(mode)
            self.toolbar.update_zoom_label(canvas.tab_state.zoom)

    def toggle_dark_mode(self):
        tab = self._active_tab_state()
        canvas = self._active_canvas()
        if tab and canvas:
            tab.dark_mode = not tab.dark_mode
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)

    def toggle_fullscreen(self):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

    # ------------------------------------------------------------------
    # text selection / copy / read aloud
    # ------------------------------------------------------------------
    def copy_selection(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.copy_selection_to_clipboard()
            self._set_status("Copied selection to clipboard.")

    def read_selection_aloud(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.read_selection_aloud()
            self._set_status("Reading selection...")

    def read_page_aloud(self):
        canvas = self._active_canvas()
        if canvas:
            canvas.read_page_aloud()
            self._set_status("Reading page...")

    def stop_reading(self):
        self.tts.stop()
        self._set_status("Stopped reading.")

    # ------------------------------------------------------------------
    # page editing
    # ------------------------------------------------------------------
    def _with_active(self, fn):
        tab = self._active_tab_state()
        canvas = self._active_canvas()
        if not tab or not canvas:
            return
        fn(tab, canvas)

    def delete_current_page(self):
        def op(tab, canvas):
            if tab.pdf_doc.page_count <= 1:
                messagebox.showinfo("Delete Page", "Can't delete the only page in the document.")
                return
            tab.history.snapshot()
            tab.pdf_doc.delete_page(tab.current_page)
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()
        self._with_active(op)

    def delete_page_at(self, index):
        def op(tab, canvas):
            if tab.pdf_doc.page_count <= 1:
                messagebox.showinfo("Delete Page", "Can't delete the only page in the document.")
                return
            tab.history.snapshot()
            tab.pdf_doc.delete_page(index)
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()
        self._with_active(op)

    def delete_page_range(self):
        tab = self._active_tab_state()
        if not tab:
            return
        def confirm(indices):
            tab.history.snapshot()
            tab.pdf_doc.delete_pages(indices)
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            self._active_canvas().render_current_page(force=True)
            self._refresh_sidebars()
        PageRangeDialog(self, tab.pdf_doc.page_count, "Delete Page Range", confirm)

    def insert_blank_page(self):
        def op(tab, canvas):
            tab.history.snapshot()
            tab.pdf_doc.insert_blank_page(tab.current_page + 1)
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()
        self._with_active(op)

    def insert_blank_page_at(self, index):
        def op(tab, canvas):
            tab.history.snapshot()
            tab.pdf_doc.insert_blank_page(index)
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()
        self._with_active(op)

    def move_page(self, from_index, to_index):
        def op(tab, canvas):
            tab.history.snapshot()
            tab.pdf_doc.move_page(from_index, to_index)
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()
        self._with_active(op)

    def rotate_page(self, degrees):
        def op(tab, canvas):
            tab.history.snapshot()
            tab.pdf_doc.rotate_page(tab.current_page, degrees)
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
        self._with_active(op)

    def undo(self):
        tab = self._active_tab_state()
        canvas = self._active_canvas()
        if tab and tab.history.undo():
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()

    def redo(self):
        tab = self._active_tab_state()
        canvas = self._active_canvas()
        if tab and tab.history.redo():
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            canvas.render_current_page(force=True)
            self._refresh_sidebars()

    # ------------------------------------------------------------------
    # tools: merge / convert / compress / extract / split
    # ------------------------------------------------------------------
    def open_merge_dialog(self):
        def confirm(paths):
            try:
                merged = merge_pdfs(paths)
            except Exception as e:
                messagebox.showerror("Merge PDFs", f"Merge failed:\n{e}")
                return
            tab = TabState(merged, "Merged.pdf")
            self.app_state.add_tab(tab)
            self.tab_manager.open_tab(tab)
            self._refresh_sidebars()
            self._set_status(f"Merged {len(paths)} files.")
        MergeDialog(self, confirm)

    def open_convert_dialog(self):
        def confirm(paths, scan_mode, page_size, auto_crop):
            try:
                result = images_to_pdf(
                    paths, scan_mode=scan_mode, page_size=page_size, auto_crop=auto_crop,
                )
            except OpenCVNotAvailable as e:
                messagebox.showwarning("Auto-Crop Unavailable", str(e))
                return
            except Exception as e:
                messagebox.showerror("Images to PDF", f"Conversion failed:\n{e}")
                return
            tab = TabState(result, "Converted.pdf")
            self.app_state.add_tab(tab)
            self.tab_manager.open_tab(tab)
            self._refresh_sidebars()
            crop_note = " (auto-crop applied)" if auto_crop else ""
            self._set_status(f"Converted {len(paths)} images to PDF{crop_note}.")
        ConvertDialog(self, confirm)

    def open_compress_dialog(self):
        tab = self._active_tab_state()
        if not tab:
            messagebox.showinfo("Compress PDF", "Open a PDF first.")
            return

        def estimate(dpi):
            return estimate_size_reduction(tab.pdf_doc, max_dpi=dpi)

        def confirm(dpi, quality):
            tab.history.snapshot()
            touched, skipped = compress_pdf(tab.pdf_doc, max_dpi=dpi, jpeg_quality=quality)
            self.page_cache.invalidate_document(id(tab.pdf_doc))
            self.thumb_cache.invalidate_document(id(tab.pdf_doc))
            self._active_canvas().render_current_page(force=True)
            self._set_status(f"Compressed: {touched} images downsampled, {skipped} left as-is.")

        CompressDialog(
            self, on_confirm=confirm, on_estimate=estimate,
            default_dpi=self.app_state.settings.get("compress_max_dpi", 220),
            default_quality=self.app_state.settings.get("compress_jpeg_quality", 82),
        )

    def extract_pages_dialog(self):
        tab = self._active_tab_state()
        if not tab:
            return
        def confirm(indices):
            extracted = tab.pdf_doc.extract_pages(indices)
            new_tab = TabState(extracted, "Extracted.pdf")
            self.app_state.add_tab(new_tab)
            self.tab_manager.open_tab(new_tab)
            self._refresh_sidebars()
        PageRangeDialog(self, tab.pdf_doc.page_count, "Extract Pages", confirm)

    def split_every_n_dialog(self):
        tab = self._active_tab_state()
        if not tab:
            return
        n = simpledialog.askinteger("Split Every N Pages", "Pages per file:", minvalue=1,
                                        maxvalue=tab.pdf_doc.page_count)
        if not n:
            return
        from app.core.merge_split import split_every_n_pages
        parts = split_every_n_pages(tab.pdf_doc, n)
        for i, part in enumerate(parts, start=1):
            new_tab = TabState(part, f"Split_part{i}.pdf")
            self.app_state.add_tab(new_tab)
            self.tab_manager.open_tab(new_tab)
        self._set_status(f"Split into {len(parts)} files.")

    def open_metadata_dialog(self):
        tab = self._active_tab_state()
        if not tab:
            return
        meta = get_display_metadata(tab.pdf_doc)

        def save_meta(fields):
            update_metadata(tab.pdf_doc, fields)
            self._set_status("Metadata updated (save the file to persist).")

        def save_encrypted(password):
            path = ask_save_pdf(initial_name="protected_" + (tab.title or "document.pdf"))
            if not path:
                return
            save_with_password(tab.pdf_doc, path, password)
            messagebox.showinfo("Password Protect", f"Encrypted copy saved to:\n{path}")

        MetadataDialog(self, meta, save_meta, save_encrypted)

    # ------------------------------------------------------------------
    # misc
    # ------------------------------------------------------------------
    def _shortcut_handlers(self):
        return {
            "open_file": self.open_file,
            "save_file": self.save_file,
            "save_as": self.save_as,
            "close_tab": self.close_active_tab,
            "undo": self.undo,
            "redo": self.redo,
            "focus_search": lambda: self.sidebar_notebook.select(self.search_sidebar),
            "zoom_in": self.zoom_in,
            "zoom_out": self.zoom_out,
            "zoom_reset": self.zoom_reset,
            "prev_page": self.prev_page,
            "next_page": self.next_page,
            "first_page": lambda: self.goto_page(0),
            "last_page": lambda: self.goto_page(self._active_tab_state().pdf_doc.page_count - 1)
            if self._active_tab_state() else None,
            "goto_page": self.goto_page_prompt,
            "print_document": self.print_document,
            "delete_selected_page": self.delete_current_page,
            "merge_dialog": self.open_merge_dialog,
            "toggle_fullscreen": self.toggle_fullscreen,
        }

    def _show_about(self):
        messagebox.showinfo(
            "About FeatherPDF",
            "FeatherPDF\n\nA lightweight PDF viewer & toolkit built on "
            "PyMuPDF, Pillow, and Tkinter only -- no heavy GUI framework, "
            "no OpenCV.\n\nSee README.md and WALKTHROUGH.md for full usage."
            "\n\nLicensed under Attribution-NonCommercial -- see LICENSE."
            "\n\nCreated by Mehedy -- mehedy.netlify.app",
        )

    def _on_close(self):
        self.tts.stop()
        dirty_tabs = [t for t in self.app_state.tabs if t.pdf_doc.dirty]
        if dirty_tabs:
            if not messagebox.askyesno(
                "Exit", f"{len(dirty_tabs)} document(s) have unsaved changes. Exit anyway?"
            ):
                return
        self.destroy()
