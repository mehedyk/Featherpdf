"""
core/text_extraction.py
Word-level text extraction so selection/copy/highlight can work against
real text positions instead of an arbitrary dragged rectangle.
"""
import pymupdf


def get_words(page):
    """
    Returns a list of tuples from PyMuPDF: (x0, y0, x1, y1, word, block_no, line_no, word_no).
    Already in roughly reading order for normal left-to-right documents.
    """
    return page.get_text("words")


def get_page_text(page):
    return page.get_text("text")


def words_in_rect(words, rect):
    """
    rect: (x0, y0, x1, y1) in PDF page coordinates.
    Returns the subset of words whose bounding box intersects rect, sorted
    into reading order (block, line, word position). This is a simple
    "bounding-box overlap" selection rather than true multi-line text-flow
    selection (e.g. dragging from mid-line-1 to mid-line-3 selects every
    word whose box the drag rectangle touches, not "rest of line 1 + all
    of line 2 + start of line 3"). It covers the common case -- selecting
    a word, a line, or a block -- reliably and simply.
    """
    x0, y0, x1, y1 = rect
    selected = []
    for w in words:
        wx0, wy0, wx1, wy1 = w[0], w[1], w[2], w[3]
        if wx1 >= x0 and wx0 <= x1 and wy1 >= y0 and wy0 <= y1:
            selected.append(w)
    selected.sort(key=lambda w: (w[5], w[6], w[7]))
    return selected


def words_to_text(words):
    return " ".join(w[4] for w in words)


def word_rect(word):
    return pymupdf.Rect(word[0], word[1], word[2], word[3])
