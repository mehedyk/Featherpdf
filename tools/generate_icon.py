"""
tools/generate_icon.py (dev-only)
Redraws the FeatherPDF logo at high resolution (matching tools/generate_logo.py's
final-frame look: fully faded in, full accent ring, no scan line) and exports a
proper multi-resolution Windows .ico -- the low-res logo.png used for the README
is too small to downsample cleanly into a crisp 256x256 icon, so this draws fresh
at 4x scale instead of just resizing.
"""
import os
from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

SCALE = 4
W, H = 200 * SCALE, 240 * SCALE
PAGE_COLOR = (245, 247, 250, 255)
PAGE_SHADOW = (10, 12, 16, 60)
FOLD_COLOR = (200, 206, 216, 255)
ACCENT = (74, 144, 217, 255)
LINE_COLOR = (170, 178, 190, 255)

PAGE_X0, PAGE_Y0 = 50 * SCALE, 30 * SCALE
PAGE_X1, PAGE_Y1 = 150 * SCALE, 200 * SCALE
FOLD = 22 * SCALE


def draw_icon():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r = 10 * SCALE
    draw.rounded_rectangle(
        [PAGE_X0 + 6 * SCALE, PAGE_Y0 + 8 * SCALE, PAGE_X1 + 6 * SCALE, PAGE_Y1 + 8 * SCALE],
        radius=r, fill=PAGE_SHADOW,
    )
    draw.rounded_rectangle([PAGE_X0, PAGE_Y0, PAGE_X1, PAGE_Y1], radius=r, fill=PAGE_COLOR)
    draw.polygon(
        [
            (PAGE_X1 - FOLD, PAGE_Y0),
            (PAGE_X1, PAGE_Y0 + FOLD),
            (PAGE_X1 - FOLD, PAGE_Y0 + FOLD),
        ],
        fill=FOLD_COLOR,
    )
    for i in range(5):
        y = PAGE_Y0 + 40 * SCALE + i * 20 * SCALE
        x1 = PAGE_X1 - 20 * SCALE if i != 4 else PAGE_X1 - 45 * SCALE
        draw.rounded_rectangle(
            [PAGE_X0 + 15 * SCALE, y, x1, y + 6 * SCALE], radius=3 * SCALE, fill=LINE_COLOR,
        )

    cx, cy, ring_r = W // 2, H - 24 * SCALE, 14 * SCALE
    draw.arc(
        [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], start=-90, end=270,
        fill=ACCENT, width=4 * SCALE,
    )
    return img


def main():
    icon_img = draw_icon()

    # Pad onto a square canvas -- ICO entries should be square (16x16, 32x32,
    # etc.); the page graphic itself is taller than wide, so exporting directly
    # would give non-square icon entries that Windows can render oddly.
    side = max(icon_img.width, icon_img.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    paste_x = (side - icon_img.width) // 2
    paste_y = (side - icon_img.height) // 2
    square.paste(icon_img, (paste_x, paste_y), icon_img)

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = os.path.join(OUT_DIR, "icon.ico")
    square.save(ico_path, format="ICO", sizes=sizes)

    # also drop a high-res PNG in case it's useful for the installer's wizard graphic
    png_path = os.path.join(OUT_DIR, "icon_512.png")
    square.resize((512, 512), Image.LANCZOS).save(png_path)

    print(f"Wrote {ico_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
