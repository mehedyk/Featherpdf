"""
tools/generate_logo.py (dev-only script, not shipped as part of the app's
runtime code -- it's run once to produce assets/icons/logo_frames/*.png
and assets/icons/logo.gif, which ARE shipped).

Draws a simple document-with-folded-corner icon and animates a "scan line"
sweeping down it plus a gentle fade-in, entirely with Pillow's ImageDraw --
no external image assets, so the whole logo costs ~0 extra dependency weight.
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "icons", "logo_frames")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 200, 240
BG = (27, 30, 36, 0)
PAGE_COLOR = (245, 247, 250, 255)
PAGE_SHADOW = (10, 12, 16, 60)
FOLD_COLOR = (200, 206, 216, 255)
ACCENT = (74, 144, 217, 255)
SCAN_COLOR = (120, 220, 180, 220)
LINE_COLOR = (170, 178, 190, 255)

N_FRAMES = 24
PAGE_X0, PAGE_Y0, PAGE_X1, PAGE_Y1 = 50, 30, 150, 200
FOLD = 22


def draw_page(draw, alpha_scale=1.0):
    def a(c):
        r, g, b, al = c
        return (r, g, b, int(al * alpha_scale))

    # drop shadow
    draw.rounded_rectangle(
        [PAGE_X0 + 6, PAGE_Y0 + 8, PAGE_X1 + 6, PAGE_Y1 + 8], radius=10, fill=a(PAGE_SHADOW)
    )
    # page body
    draw.rounded_rectangle([PAGE_X0, PAGE_Y0, PAGE_X1, PAGE_Y1], radius=10, fill=a(PAGE_COLOR))
    # folded corner (top-right)
    draw.polygon(
        [
            (PAGE_X1 - FOLD, PAGE_Y0),
            (PAGE_X1, PAGE_Y0 + FOLD),
            (PAGE_X1 - FOLD, PAGE_Y0 + FOLD),
        ],
        fill=a(FOLD_COLOR),
    )
    # text lines
    for i in range(5):
        y = PAGE_Y0 + 40 + i * 20
        x1 = PAGE_X1 - 20 if i != 4 else PAGE_X1 - 45
        draw.rounded_rectangle([PAGE_X0 + 15, y, x1, y + 6], radius=3, fill=a(LINE_COLOR))


def draw_accent_ring(draw, progress):
    """A partial arc that sweeps in during the first half of the animation."""
    cx, cy, r = W // 2, H - 24, 14
    start_angle = -90
    end_angle = -90 + 360 * progress
    draw.arc(
        [cx - r, cy - r, cx + r, cy + r], start=start_angle, end=end_angle,
        fill=ACCENT, width=4,
    )


def make_frame(i):
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    fade_in = min(1.0, (i + 1) / 6)   # first 6 frames fade the page in
    draw_page(draw, alpha_scale=fade_in)

    # scan line sweeps top to bottom across frames 4..18, then fades
    scan_progress = (i - 3) / 14
    if 0 <= scan_progress <= 1:
        y = PAGE_Y0 + int(scan_progress * (PAGE_Y1 - PAGE_Y0))
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.rectangle([PAGE_X0, y - 2, PAGE_X1, y + 2], fill=SCAN_COLOR)
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

    ring_progress = min(1.0, max(0.0, (i - 8) / 12))
    draw_accent_ring(draw, ring_progress)

    return img


def main():
    frames = []
    for i in range(N_FRAMES):
        frame = make_frame(i)
        path = os.path.join(OUT_DIR, f"frame_{i:03d}.png")
        frame.save(path)
        frames.append(frame.convert("RGB"))

    gif_path = os.path.join(os.path.dirname(OUT_DIR), "logo.gif")
    frames[0].save(
        gif_path, save_all=True, append_images=frames[1:], duration=45, loop=0,
    )

    # also drop a static "largest, final frame" as the app's icon-ish PNG
    final_png = os.path.join(os.path.dirname(OUT_DIR), "logo.png")
    make_frame(N_FRAMES - 1).save(final_png)

    print(f"Wrote {len(frames)} frames to {OUT_DIR}")
    print(f"Wrote animated GIF to {gif_path}")
    print(f"Wrote static logo to {final_png}")


if __name__ == "__main__":
    main()
