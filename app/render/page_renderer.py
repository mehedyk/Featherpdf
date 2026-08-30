"""
render/page_renderer.py
Converts a pymupdf page into a PIL Image (and optionally a Tk PhotoImage)
at a given zoom factor. This is the ONLY place raster conversion happens,
so caching/quality decisions live in one spot.
"""
from PIL import Image, ImageOps
import pymupdf

BASE_DPI = 72  # pymupdf's native unit; zoom=1.0 means 72 dpi (screen-ish)


def render_page_to_pil(page, zoom=1.0, rotation_override=None) -> Image.Image:
    """
    zoom: 1.0 = 100%. Internally we render at a higher DPI matrix for crispness.
    rotation_override: if given, applies an EXTRA display-only rotation on top
    of the page's own saved rotation (for "view rotated without saving" mode).
    """
    matrix = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    mode = "RGB" if pix.n < 4 else "RGBA"
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)

    if rotation_override:
        img = img.rotate(-rotation_override, expand=True)

    return img


def invert_for_dark_mode(pil_image: Image.Image) -> Image.Image:
    """Cheap 'reading in dark mode' inversion, display-only."""
    rgb = pil_image.convert("RGB")
    return ImageOps.invert(rgb)


def compute_zoom_for_fit(page_w, page_h, viewport_w, viewport_h, mode="page"):
    """
    mode: 'width' -> fit to width, 'page' -> fit whole page in viewport,
    'screen' -> alias of 'page' at slightly reduced margin.
    Returns the zoom factor to pass to render_page_to_pil.
    """
    if mode == "width":
        return max(0.05, viewport_w / page_w)
    if mode == "screen":
        return max(0.05, min(viewport_w / page_w, viewport_h / page_h) * 0.97)
    # default: fit whole page
    return max(0.05, min(viewport_w / page_w, viewport_h / page_h))
