"""
core/auto_crop.py
Automatic document-edge detection + perspective correction ("auto crop and
straighten," the CamScanner-style feature that handles a photo taken at an
angle, not just a perfectly-square scan).

This is the ONE feature in the app that uses OpenCV, and it's an OPTIONAL
dependency for exactly that reason: OpenCV is ~90MB, which would roughly
triple this app's install size for every user even if they never touch
this feature. Both cv2 AND numpy are imported lazily, only inside the
functions that need them -- NOT at module level. This matters: this
module gets imported eagerly at app startup (main_window.py and
convert_dialog.py both reference it to check availability for the
Auto-Crop checkbox), so a module-level `import numpy` would make numpy a
hard requirement for the whole app to even launch, silently defeating the
entire point of keeping this optional. (numpy happens to already be a
transitive dependency of opencv-python-headless, so in practice it's
"free" whenever cv2 is installed -- but it must still never be imported
unconditionally here.)

Algorithm (standard "document scanner" approach):
  1. Downscale for fast, robust detection (a huge photo doesn't need full
     resolution just to find the paper's edges).
  2. Grayscale + blur + Canny edge detection.
  3. Dilate the edges slightly so a document's boundary forms one closed
     contour even where lighting made a segment of the true edge faint.
  4. Find all external contours, keep the largest ones, and look for the
     first one that approximates to a 4-sided polygon of significant area
     -- that's almost always the document (page borders are the biggest
     hard edge in a document photo).
  5. Order its 4 corners consistently (top-left, top-right, bottom-right,
     bottom-left) and compute the correct output width/height from the
     actual corner distances (so a non-rectangular photo angle still
     produces a proper rectangle at the real document's proportions).
  6. Map the ORIGINAL full-resolution corners (not the downscaled ones)
     through a perspective warp into that straightened rectangle.

If no confident 4-sided contour is found (busy background, document edge
not visible, etc.), this returns None rather than guessing -- the caller
falls back to using the untouched original photo, which is always safer
than a wrong crop.
"""
from PIL import Image

DETECTION_WIDTH = 700  # downscale target for step 1-4; corners get scaled back up


class OpenCVNotAvailable(Exception):
    pass


def _require_deps():
    """Lazily imports and returns (cv2, numpy). Neither is imported at module
    level -- see the module docstring for why that matters here specifically."""
    try:
        import cv2
        import numpy as np
        return cv2, np
    except ImportError:
        raise OpenCVNotAvailable(
            "Auto-crop needs OpenCV, which isn't installed. Run:\n"
            "    pip install opencv-python-headless\n"
            "This is optional -- the rest of the app works fine without it."
        )


def _order_corners(np, pts):
    """Return corners ordered as top-left, top-right, bottom-right, bottom-left."""
    pts = np.array(pts, dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    ordered = np.zeros((4, 2), dtype="float32")
    ordered[0] = pts[np.argmin(s)]       # top-left: smallest x+y
    ordered[2] = pts[np.argmax(s)]       # bottom-right: largest x+y
    ordered[1] = pts[np.argmin(diff)]    # top-right: smallest y-x
    ordered[3] = pts[np.argmax(diff)]    # bottom-left: largest y-x
    return ordered


def _find_document_corners(cv2, np, gray):
    """Runs the edge/contour pipeline on an already-grayscale, downscaled image."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:8]
    img_area = gray.shape[0] * gray.shape[1]

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(approx) > 0.15 * img_area:
            return approx.reshape(4, 2)

    return None


def detect_and_crop(pil_image: Image.Image):
    """
    Attempts to find the document's 4 corners and perspective-correct it.
    Returns a new, straightened PIL Image on success, or None if no
    confident document boundary was found (caller should keep the original).
    Raises OpenCVNotAvailable if OpenCV isn't installed.
    """
    cv2, np = _require_deps()

    rgb = pil_image.convert("RGB")
    orig = np.array(rgb)
    orig_h, orig_w = orig.shape[:2]

    scale = DETECTION_WIDTH / orig_w if orig_w > DETECTION_WIDTH else 1.0
    small = cv2.resize(orig, (int(orig_w * scale), int(orig_h * scale))) if scale != 1.0 else orig
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

    corners_small = _find_document_corners(cv2, np, gray)
    if corners_small is None:
        return None

    corners_full = corners_small.astype("float32") / scale
    ordered = _order_corners(np, corners_full)
    (tl, tr, br, bl) = ordered

    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    out_w = int(max(width_top, width_bottom))
    out_h = int(max(height_left, height_right))

    if out_w < 20 or out_h < 20:
        return None  # degenerate detection, not worth trusting

    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(orig, matrix, (out_w, out_h))

    return Image.fromarray(warped)


def is_available():
    try:
        _require_deps()
        return True
    except OpenCVNotAvailable:
        return False
