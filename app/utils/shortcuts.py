"""
utils/shortcuts.py
All keyboard shortcuts bound in one place so two features never fight
over the same key combo.
"""

SHORTCUTS = {
    "<Control-o>": "open_file",
    "<Control-s>": "save_file",
    "<Control-Shift-S>": "save_as",
    "<Control-w>": "close_tab",
    "<Control-z>": "undo",
    "<Control-y>": "redo",
    "<Control-Shift-Z>": "redo",
    "<Control-f>": "focus_search",
    "<Control-plus>": "zoom_in",
    "<Control-minus>": "zoom_out",
    "<Control-0>": "zoom_reset",
    "<Control-equal>": "zoom_in",  # some keyboards send '=' instead of '+'
    "<Prior>": "prev_page",         # Page Up
    "<Next>": "next_page",          # Page Down
    "<Home>": "first_page",
    "<End>": "last_page",
    "<Control-g>": "goto_page",
    "<Control-p>": "print_document",
    "<Delete>": "delete_selected_page",
    "<Control-m>": "merge_dialog",
    "<F11>": "toggle_fullscreen",
}


def bind_all_shortcuts(root, handler_map):
    """
    handler_map: dict of action_name -> callable.
    Any SHORTCUTS entry without a matching handler is silently skipped
    (keeps this file usable even before every feature is wired up).
    """
    for key_combo, action_name in SHORTCUTS.items():
        handler = handler_map.get(action_name)
        if handler:
            root.bind_all(key_combo, lambda event, h=handler: h())
