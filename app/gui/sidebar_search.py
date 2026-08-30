"""
gui/sidebar_search.py
Search box + results list. Delegates the actual search to core/search.py
and just manages navigation + display of the match count.
"""
import tkinter as tk
from tkinter import ttk
from app.core.search import search_document


class SearchSidebar(tk.Frame):
    def __init__(self, parent, get_active_tab, on_navigate):
        super().__init__(parent, bg="#d0d0d0")
        self.get_active_tab = get_active_tab
        self.on_navigate = on_navigate

        top = tk.Frame(self, bg="#d0d0d0")
        top.pack(fill="x", padx=4, pady=4)
        self.query_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.run_search())
        ttk.Button(top, text="Find", command=self.run_search).pack(side="left", padx=2)

        nav = tk.Frame(self, bg="#d0d0d0")
        nav.pack(fill="x", padx=4)
        ttk.Button(nav, text="◀ Prev", command=self.prev_match).pack(side="left", padx=2)
        ttk.Button(nav, text="Next ▶", command=self.next_match).pack(side="left", padx=2)
        self.status_label = tk.Label(self, text="No search yet", bg="#d0d0d0")
        self.status_label.pack(fill="x", padx=4, pady=4)

    def focus_entry(self):
        pass  # entry focus wired by caller if desired

    def run_search(self):
        tab = self.get_active_tab()
        if not tab:
            return
        query = self.query_var.get()
        tab.search_query = query
        tab.search_matches = search_document(tab.pdf_doc, query)
        tab.search_index = 0 if tab.search_matches else -1
        self._update_status(tab)
        if tab.search_matches:
            self.on_navigate(tab.search_matches[0][0])

    def next_match(self):
        tab = self.get_active_tab()
        if not tab or not tab.search_matches:
            return
        tab.search_index = (tab.search_index + 1) % len(tab.search_matches)
        self._update_status(tab)
        self.on_navigate(tab.search_matches[tab.search_index][0])

    def prev_match(self):
        tab = self.get_active_tab()
        if not tab or not tab.search_matches:
            return
        tab.search_index = (tab.search_index - 1) % len(tab.search_matches)
        self._update_status(tab)
        self.on_navigate(tab.search_matches[tab.search_index][0])

    def _update_status(self, tab):
        if not tab.search_matches:
            self.status_label.configure(text="No matches found")
        else:
            self.status_label.configure(
                text=f"Match {tab.search_index + 1} of {len(tab.search_matches)}"
            )
