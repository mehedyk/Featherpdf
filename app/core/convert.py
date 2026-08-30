"""
core/convert.py
Turns a list of image files into a single PDF, optionally running each
image through the scan-effect filters first.
"""
import io
import pymupdf
from PIL import Image
from app.core.document import PDFDocument
from app.core.scan_effect import apply_scan_effect, MODE_COLOR


def images_to_pdf(image_paths, output_doc: PDFDocument = None, scan_mode=None, page_size="fit"):
    """
    image_paths: ordered list of file paths.
    output_doc: an existing PDFDocument to append to, or None to create a new one.
    scan_mode: None to skip effects, or one of scan_effect.MODE_* to apply.
    page_size: "fit" (page matches image aspect ratio) or "a4" (fixed A4, image centered/scaled).
    """
    result = output_doc or PDFDocument()

    for path in image_paths:
        img = Image.open(path)
        img = img.convert("RGB")

        if scan_mode:
            img = apply_scan_effect(img, scan_mode)
            if scan_mode != MODE_COLOR:
                img = img.convert("RGB")  # PDF embedding wants RGB, not 'L' for consistency

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        img_bytes = buf.getvalue()

        img_w, img_h = img.size

        if page_size == "a4":
            page_w, page_h = 595, 842  # A4 at 72 dpi
            scale = min(page_w / img_w, page_h / img_h)
            draw_w, draw_h = img_w * scale, img_h * scale
            x0 = (page_w - draw_w) / 2
            y0 = (page_h - draw_h) / 2
            rect = pymupdf.Rect(x0, y0, x0 + draw_w, y0 + draw_h)
            page = result.doc.new_page(width=page_w, height=page_h)
        else:
            # page exactly matches the image aspect ratio at a sane DPI (150)
            dpi = 150
            page_w, page_h = img_w * 72 / dpi, img_h * 72 / dpi
            rect = pymupdf.Rect(0, 0, page_w, page_h)
            page = result.doc.new_page(width=page_w, height=page_h)

        page.insert_image(rect, stream=img_bytes)

    result.dirty = True
    return result
