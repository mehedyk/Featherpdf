# FeatherPDF

A fully-featured PDF viewer and toolkit that stays genuinely lightweight.
Built on exactly **two** third-party libraries — **PyMuPDF** and **Pillow** —
plus Python's built-in **Tkinter** for the interface. No Qt, no OpenCV,
no bundled browser engine.

Created by **Mehedy** — [mehedy.netlify.app](https://mehedy.netlify.app)

Packaged size: roughly **40–70 MB**, versus the 150–400 MB+ typical of
Electron/Qt-based PDF tools with a comparable feature set.

---

## Features

**Viewing**
- Zoom in / out, actual size (100%), Fit Width, Fit Page, Fit Screen
- Page navigation: next/prev, first/last, jump-to-page
- Thumbnail sidebar, bookmark/outline sidebar, full-text search with match navigation
- Rotate page view, dark mode (inverted page colors for reading)
- Multiple PDFs open at once, each in its own tab
- **Real text selection**: click-drag over text selects the actual words (via
  PyMuPDF's word positions), not just an approximate box
- **Copy** selected text to the system clipboard (`Ctrl+C`, right-click menu, or toolbar)
- **Read aloud**: speaks the current selection or the whole page out loud,
  using your OS's own built-in speech engine (no bundled voice model)

**Editing & page operations**
- Delete a page or a page range, insert blank pages, reorder pages (move up/down or via the thumbnail panel)
- Permanent page rotation (saved with the file)
- Undo / redo

**Annotations**
- Highlight, underline, strikeout, sticky notes, freehand drawing — click-and-drag
  directly on the page. When you drag over real text, the annotation snaps to the
  exact words (via the same text-selection engine); dragging over empty space (e.g.
  a diagram) falls back to marking the dragged rectangle.

**File tools**
- Merge multiple PDFs into one (with reorder-before-merge)
- Split a PDF every N pages, or extract a specific page range into a new file
- Image → PDF conversion, with three "document style" effects:
  - Color (contrast + sharpen)
  - Grayscale
  - Black & white "scanned document" look (adaptive thresholding, CamScanner-style)
- Compress a PDF by downsampling only the images that exceed a DPI threshold — nothing is touched unless it's genuinely higher resolution than needed, so there's no visible quality loss
- Document metadata editing (title/author/subject/keywords)
- Password-protect a copy (AES-256 encryption)
- Print via the OS's native print handling

---

## Installation

```bash
pip install -r requirements.txt
python main.py
```

That's the entire setup. No compilers, no system libraries beyond what
PyMuPDF's wheel already bundles.

### Building a standalone executable (optional)

```bash
pip install pyinstaller
pyinstaller build/pyinstaller.spec
```

The result lands in `dist/PDFLiteSuite/`. See the comments at the top of
`build/pyinstaller.spec` for a couple of manual size-trimming steps if you
want to squeeze it further.

---

## Project structure

```
pdf-lite-suite/
├── main.py                  # entry point (splash screen -> main window)
├── requirements.txt
├── config/settings.json     # persisted preferences
├── app/
│   ├── core/                # PDF logic only, no GUI (document, merge/split,
│   │                          convert, scan effects, compression, annotations,
│   │                          search, metadata, undo/redo)
│   ├── render/               # page -> image rendering + LRU caches
│   ├── state/                # app-wide and per-tab state
│   ├── gui/                  # all Tkinter windows, dialogs, toolbars
│   └── utils/                 # file dialogs, shortcuts, printing, logging
├── assets/icons/              # the animated logo + generated frames
├── tools/generate_logo.py     # regenerates the logo assets (dev-only)
└── build/pyinstaller.spec     # packaging config
```

`app/core` never imports from `app/gui` — the PDF logic works standalone
and is unit-testable without opening a window.

---

## Usage

See **WALKTHROUGH.md** for a full guided tour of every feature with
step-by-step instructions.

## Known limitations

- Continuous-scroll viewing isn't implemented — pages are shown one at a
  time (this keeps memory flat on very large PDFs without a virtualized
  scroll engine, which is a substantial chunk of complexity for a "lite" app).
- The black-and-white scan effect uses an adaptive-threshold approximation
  built entirely on Pillow; it does not do automatic edge/corner detection
  or perspective correction the way OpenCV-based scanner apps do, since
  OpenCV alone is roughly 3-4x this entire app's footprint.
- Text selection uses bounding-box overlap (every word whose box the drag
  touches gets selected), not true multi-line text-flow selection — dragging
  from the middle of line 1 to the middle of line 3 selects every word the
  rectangle overlaps rather than "rest of line 1, all of line 2, start of
  line 3". It covers selecting a word, a line, a sentence, or a block reliably.
- Read Aloud requires a system speech engine to be present: Windows and macOS
  have one built in; on Linux, install `espeak` (`sudo apt install espeak`)
  if it's not already on your system.

---

Made by **Mehedy** — [mehedy.netlify.app](https://mehedy.netlify.app)

