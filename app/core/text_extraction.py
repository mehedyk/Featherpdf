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
    into reading order (block, line, word position).
    """
    x0, y0, x1, y1 = rect
    selected = []
    for w in words:
        wx0, wy0, wx1, wy1 = w[0], w[1], w[2], w[3]
        if wx1 >= x0 and wx0 <= x1 and wy1 >= y0 and wy0 <= y1:
            selected.append(w)
    selected.sort(key=lambda w: (w[5], w[6], w[7]))
    return selected


def words_in_flow(words, p0, p1):
    """
    p0: (x0, y0), p1: (x1, y1) in PDF page coordinates.
    Returns words in true reading order between the drag start and drag end points.
    Enables natural multi-line text selection (rest of line 1, all of line 2, start of line 3).
    """
    if not words:
        return []

    def dist_sq(p, w):
        dx = max(0, w[0] - p[0], p[0] - w[2])
        dy = max(0, w[1] - p[1], p[1] - w[3])
        return dx * dx + (dy * 3) * (dy * 3)

    d0 = [dist_sq(p0, w) for w in words]
    d1 = [dist_sq(p1, w) for w in words]
    min0, min1 = min(d0), min(d1)

    # If the drag occurred completely outside any text area, fall back to rectangle overlap
    if min0 > 10000 and min1 > 10000:
        rect = (min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))
        return words_in_rect(words, rect)

    i0 = d0.index(min0)
    i1 = d1.index(min1)
    return words[min(i0, i1) : max(i0, i1) + 1]


def words_to_text(words):
    return " ".join(w[4] for w in words)


def word_rect(word):
    return pymupdf.Rect(word[0], word[1], word[2], word[3])
