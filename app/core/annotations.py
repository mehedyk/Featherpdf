"""
core/annotations.py
Thin wrappers around pymupdf's annotation API so the GUI never touches
fitz/pymupdf objects directly.
"""
import pymupdf

COLOR_YELLOW = (1, 1, 0)
COLOR_GREEN = (0, 1, 0)
COLOR_RED = (1, 0, 0)
COLOR_BLUE = (0, 0.4, 1)


def highlight_text(page, quads, color=COLOR_YELLOW):
    annot = page.add_highlight_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def underline_text(page, quads, color=COLOR_RED):
    annot = page.add_underline_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def strikeout_text(page, quads, color=COLOR_RED):
    annot = page.add_strikeout_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def add_freetext(page, rect, text, font_size=12, color=(0, 0, 0)):
    annot = page.add_freetext_annot(rect, text, fontsize=font_size, text_color=color)
    annot.update()
    return annot


def add_ink(page, strokes, color=COLOR_RED, width=2.0):
    """strokes: list of point-lists, each a freehand stroke: [[(x,y), (x,y), ...], ...]"""
    annot = page.add_ink_annot(strokes)
    annot.set_colors(stroke=color)
    annot.set_border(width=width)
    annot.update()
    return annot


def add_note(page, point, text, icon="Comment"):
    annot = page.add_text_annot(point, text, icon=icon)
    annot.update()
    return annot


def delete_annotation(page, annot):
    page.delete_annot(annot)


def list_annotations(page):
    """Return a list of (annot, type_name, rect) for every annotation on the page."""
    result = []
    for annot in page.annots():
        result.append((annot, annot.type[1], annot.rect))
    return result
