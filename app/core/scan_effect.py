"""
core/scan_effect.py
Pillow-only filters to make a photographed page look like a clean scan.
No OpenCV -> no automatic corner/edge detection, but the filters below
cover the visual result most "document mode" scanner apps aim for.
"""
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

MODE_COLOR = "color"          # contrast + sharpen only, keeps color
MODE_GRAY = "grayscale"       # grayscale + contrast + sharpen
MODE_BW = "black_white"       # adaptive-style threshold -> pure black/white "document" look


def _auto_contrast_sharpen(img, contrast=1.35, sharpness=1.6):
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img


def _adaptive_threshold(gray_img, block_size=35, c=15):
    """
    Lightweight adaptive threshold using Pillow only:
    compare each pixel to a blurred (local mean) version of itself.
    Mimics OpenCV's adaptiveThreshold without the OpenCV dependency.
    """
    blurred = gray_img.filter(ImageFilter.GaussianBlur(radius=block_size / 4))
    gray_px = gray_img.load()
    blur_px = blurred.load()
    w, h = gray_img.size
    out = Image.new("L", (w, h))
    out_px = out.load()
    for y in range(h):
        for x in range(w):
            out_px[x, y] = 255 if gray_px[x, y] > (blur_px[x, y] - c) else 0
    return out


def _adaptive_threshold_fast(gray_img, radius=25, c=12):
    """
    Fast adaptive threshold using only PIL's C-level ops (no numpy, no per-pixel
    Python loop). gray - blurred + c is clamped to 0 by ImageChops.subtract when
    negative, so any remaining positive value means the pixel is 'lighter than
    its local neighbourhood' -> keep white, otherwise -> black.
    """
    blurred = gray_img.filter(ImageFilter.GaussianBlur(radius=radius))
    diff = ImageChops.subtract(gray_img, blurred, scale=1.0, offset=c)
    return diff.point(lambda p: 255 if p > 0 else 0)


def apply_scan_effect(pil_image: Image.Image, mode: str = MODE_BW) -> Image.Image:
    """Return a new PIL Image with the requested document effect applied."""
    img = pil_image.convert("RGB")

    if mode == MODE_COLOR:
        return _auto_contrast_sharpen(img)

    gray = ImageOps.grayscale(img)
    gray = _auto_contrast_sharpen(gray, contrast=1.25, sharpness=1.4)

    if mode == MODE_GRAY:
        return gray

    if mode == MODE_BW:
        return _adaptive_threshold_fast(gray)

    raise ValueError(f"Unknown scan effect mode: {mode}")
