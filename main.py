#!/usr/bin/env python3
"""
main.py
Entry point for FeatherPDF.

Shows a brief animated splash (logo fades/spins in), then opens the main
window. The splash is pure Tkinter + Pillow -- no extra dependency -- and
gracefully skips itself if the logo frames aren't found for any reason.
"""
import os
import sys
import tkinter as tk

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_ROOT)

from app.gui.main_window import MainWindow  # noqa: E402

LOGO_DIR = os.path.join(APP_ROOT, "assets", "icons", "logo_frames")
SPLASH_MS_PER_FRAME = 45


def show_splash_and_launch():
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#1b1e24")

    frames = []
    try:
        from PIL import Image, ImageTk
        frame_files = sorted(
            f for f in os.listdir(LOGO_DIR) if f.lower().endswith(".png")
        )
        for fname in frame_files:
            img = Image.open(os.path.join(LOGO_DIR, fname))
            frames.append(ImageTk.PhotoImage(img))
    except Exception:
        frames = []

    width, height = 420, 320
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")

    canvas = tk.Canvas(splash, width=width, height=height, bg="#1b1e24", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    label_text = canvas.create_text(
        width // 2, height - 40, text="FeatherPDF",
        fill="#e8ecf4", font=("Segoe UI", 16, "bold"),
    )
    sub_text = canvas.create_text(
        width // 2, height - 16, text="by Mehedy · mehedy.netlify.app",
        fill="#7d8697", font=("Segoe UI", 9),
    )

    image_item = None
    if frames:
        image_item = canvas.create_image(width // 2, height // 2 - 20, image=frames[0])

    state = {"i": 0, "after_id": None}

    def animate():
        if not frames:
            return
        state["i"] = (state["i"] + 1) % len(frames)
        canvas.itemconfig(image_item, image=frames[state["i"]])
        state["after_id"] = splash.after(SPLASH_MS_PER_FRAME, animate)

    if frames:
        animate()

    def launch_main():
        if state["after_id"] is not None:
            try:
                splash.after_cancel(state["after_id"])
            except Exception:
                pass
        splash.destroy()
        app = MainWindow()
        app.mainloop()

    # keep the splash up briefly so the animation is actually seen,
    # then hand off to the real window
    total_display_ms = max(1200, SPLASH_MS_PER_FRAME * len(frames) * 2) if frames else 900
    splash.after(total_display_ms, launch_main)
    splash.mainloop()


if __name__ == "__main__":
    show_splash_and_launch()
