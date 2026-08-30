"""
state/app_state.py
Global, app-wide state: open tabs, active tab, recent files, preferences.
Persisted preferences (theme, default zoom, recent files) live in config/settings.json.
"""
import json
import os

DEFAULT_SETTINGS = {
    "theme": "light",
    "default_zoom": 1.0,
    "default_fit_mode": "screen",
    "recent_files": [],
    "max_recent": 10,
    "compress_max_dpi": 220,
    "compress_jpeg_quality": 82,
}

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              "config", "settings.json")


class AppState:
    def __init__(self):
        self.tabs = []          # list of TabState
        self.active_tab_id = None
        self.settings = self._load_settings()

    # ---- tabs ----
    def add_tab(self, tab_state):
        self.tabs.append(tab_state)
        self.active_tab_id = tab_state.id
        return tab_state

    def get_active_tab(self):
        for t in self.tabs:
            if t.id == self.active_tab_id:
                return t
        return None

    def close_tab(self, tab_id):
        self.tabs = [t for t in self.tabs if t.id != tab_id]
        if self.active_tab_id == tab_id:
            self.active_tab_id = self.tabs[-1].id if self.tabs else None

    # ---- recent files ----
    def add_recent_file(self, path):
        recents = self.settings.get("recent_files", [])
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        self.settings["recent_files"] = recents[: self.settings.get("max_recent", 10)]
        self._save_settings()

    # ---- persistence ----
    def _load_settings(self):
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r") as f:
                    loaded = json.load(f)
                merged = dict(DEFAULT_SETTINGS)
                merged.update(loaded)
                return merged
            except Exception:
                return dict(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    def _save_settings(self):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump(self.settings, f, indent=2)
