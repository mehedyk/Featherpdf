"""
utils/printing.py
Hands the PDF off to the OS's own print handling rather than implementing
a print pipeline ourselves -- keeps this app lite and lets the OS driver
deal with paper size/duplex/etc.
"""
import subprocess
import sys


def print_pdf(path):
    if sys.platform.startswith("win"):
        import os
        os.startfile(path, "print")
    elif sys.platform == "darwin":
        subprocess.run(["lp", path], check=False)
    else:
        subprocess.run(["lp", path], check=False)


def open_print_dialog_hint():
    """Returns a short message for the status bar since we don't render a custom dialog."""
    if sys.platform.startswith("win"):
        return "Sent to default printer via Windows print handler."
    return "Sent to the system print queue (lp)."
