"""
core/compress.py
Shrinks file size by downsampling embedded images that exceed a DPI threshold
and recompressing them as JPEG, while leaving already-reasonable images alone.
This is the "reduce size without visibly reducing quality" behavior: nothing
gets touched unless it's genuinely higher resolution than the page needs.
"""
import io
import pymupdf
from PIL import Image
from app.core.document import PDFDocument

# Effective DPI above which an embedded image is considered "wasteful" for on-screen
# or standard print use. 220 keeps print quality; drop to ~150 for a more aggressive squeeze.
DEFAULT_MAX_DPI = 220
DEFAULT_JPEG_QUALITY = 82


def _effective_dpi(img_w_px, img_h_px, rect):
    """Estimate the DPI the image is actually displayed at on its page rect."""
    rect_w_in = rect.width / 72.0
    rect_h_in = rect.height / 72.0
    if rect_w_in <= 0 or rect_h_in <= 0:
        return 0
    dpi_x = img_w_px / rect_w_in
    dpi_y = img_h_px / rect_h_in
    return max(dpi_x, dpi_y)


def compress_pdf(pdf_doc: PDFDocument, max_dpi=DEFAULT_MAX_DPI, jpeg_quality=DEFAULT_JPEG_QUALITY):
    """
    Mutates pdf_doc in place: downsamples oversized embedded images.
    Returns (images_touched, images_skipped) counts for UI feedback.
    """
    doc = pdf_doc.doc
    touched, skipped = 0, 0

    for page_index in range(doc.page_count):
        page = doc[page_index]
        img_list = page.get_images(full=True)
        for img_info in img_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                skipped += 1
                continue

            img_bytes = base_image["image"]
            pil_img = Image.open(io.BytesIO(img_bytes))
            img_w, img_h = pil_img.size

            # find where this image is actually placed to estimate effective DPI
            rects = page.get_image_rects(xref)
            rect = rects[0] if rects else pymupdf.Rect(0, 0, img_w, img_h)
            dpi = _effective_dpi(img_w, img_h, rect)

            if dpi <= max_dpi:
                skipped += 1
                continue

            scale = max_dpi / dpi
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))
            resized = pil_img.convert("RGB").resize((new_w, new_h), Image.LANCZOS)

            buf = io.BytesIO()
            resized.save(buf, format="JPEG", quality=jpeg_quality)
            new_bytes = buf.getvalue()

            try:
                doc.update_stream(xref, new_bytes)
                # ensure the image is flagged as DCTDecode/JPEG after the stream swap
                touched += 1
            except Exception:
                skipped += 1

    pdf_doc.dirty = True
    return touched, skipped


def estimate_size_reduction(pdf_doc: PDFDocument, max_dpi=DEFAULT_MAX_DPI):
    """Dry-run: returns estimated (current_bytes, estimated_new_bytes) without mutating."""
    current_bytes = len(pdf_doc.doc.tobytes())
    # cheap approximation: clone in memory, compress the clone, measure
    clone = pymupdf.open("pdf", pdf_doc.doc.tobytes())
    from app.core.document import PDFDocument as _PD
    wrapper = _PD()
    wrapper.doc.close()
    wrapper.doc = clone
    compress_pdf(wrapper, max_dpi=max_dpi)
    estimated_bytes = len(wrapper.doc.tobytes(garbage=4, deflate=True))
    wrapper.close()
    return current_bytes, estimated_bytes
