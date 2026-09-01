<div align="center">

<img src="assets/icons/logo.gif" width="140" alt="FeatherPDF animated logo">

# FeatherPDF

### A fully-featured PDF viewer & toolkit that stays genuinely lightweight

[![License](https://img.shields.io/badge/license-Attribution--NonCommercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Built with](https://img.shields.io/badge/built%20with-PyMuPDF%20%2B%20Pillow%20%2B%20Tkinter-4a90d9)](#tech-stack)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#installation)

Two third-party dependencies. No Qt. No OpenCV. No bundled browser engine.
Just a fast, small, no-nonsense PDF app.

**Made by [Mehedy](https://mehedy.netlify.app)**

</div>

---

<div align="center">
<img src="assets/screenshots/demo.gif" width="800" alt="FeatherPDF demo: opening a document, navigating pages, zooming, selecting text, highlighting, and toggling dark mode">
<br>
<sub>Real screen capture — opening a doc, navigating, zooming, selecting real text, highlighting it, and toggling dark mode.</sub>
</div>

---

## Table of contents

- [Why FeatherPDF](#why-featherpdf)
- [Features](#features)
- [Installation](#installation)
- [Building a standalone .exe](#building-a-standalone-executable-optional)
- [Project structure](#project-structure)
- [Usage](#usage)
- [Known limitations](#known-limitations)
- [License](#license)

## Why FeatherPDF

Most "full-featured" PDF apps ship 150–400 MB of Electron/Qt/Chromium
just to show you a page. FeatherPDF packs viewing, editing, annotating,
merging, converting, compressing, and reading-aloud into roughly
**40–70 MB** — because the entire feature set sits on top of exactly
**two** third-party libraries:

<a name="tech-stack"></a>

| Library | What it does here |
|---|---|
| 🐍 **PyMuPDF** | All PDF logic — rendering, merge/split, text extraction, annotations, search, compression |
| 🖼️ **Pillow** | Image filters for the scan-effect / CamScanner-style conversion, dark-mode inversion |
| 🪟 **Tkinter** | The entire interface — built into Python, zero extra install |

That's it. No Electron shell, no Chromium, no OpenCV, no Qt runtime.

---

## Features

### 👁️ Viewing
- Zoom in / out, actual size (100%), Fit Width, Fit Page, Fit Screen
- Page navigation: next/prev, first/last, jump-to-page
- Thumbnail sidebar, bookmark/outline sidebar, full-text search with match navigation
- Rotate page view, dark mode (inverted page colors for reading)
- Multiple PDFs open at once, each in its own tab
- **Real text selection** — click-drag over text selects the actual words
  (via PyMuPDF's word positions), not just an approximate box
- **Copy** selected text to the system clipboard (`Ctrl+C`, right-click menu, or toolbar)
- **Read aloud** 🔊 — speaks the current selection or the whole page out
  loud, using your OS's own built-in speech engine (no bundled voice model)

### ✏️ Editing & page operations
- Delete a page or a page range, insert blank pages, reorder pages (move
  up/down or via the thumbnail panel)
- Permanent page rotation (saved with the file)
- Undo / redo

### 🖍️ Annotations
- Highlight, underline, strikeout, sticky notes, freehand drawing —
  click-and-drag directly on the page. Drag over real text and the
  annotation snaps to the exact words; drag over empty space (like a
  diagram) and it falls back to marking the dragged rectangle.

### 🛠️ File tools
- Merge multiple PDFs into one (with reorder-before-merge)
- Split a PDF every N pages, or extract a specific page range into a new file
- Image → PDF conversion, with three "document style" effects:
  - Color (contrast + sharpen)
  - Grayscale
  - Black & white "scanned document" look (adaptive thresholding, CamScanner-style)
- Compress a PDF by downsampling only the images that exceed a DPI
  threshold — nothing is touched unless it's genuinely higher resolution
  than needed, so there's no visible quality loss
- Document metadata editing (title/author/subject/keywords)
- Password-protect a copy (AES-256 encryption)
- Print via the OS's native print handling

### 📱 Interface that fits *your* window
Both toolbars auto-wrap their buttons to however wide your window
actually is — more rows on a narrow window, fewer on a wide one — so
nothing ever gets clipped off the edge, and nothing wastes space either.

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
python -m PyInstaller build/pyinstaller.spec --workpath build/_cache
```

The `--workpath build/_cache` matters: PyInstaller's own build cache
defaults to `./build/<specname>/`, which collides with this project's
`build/pyinstaller.spec` file since they'd share the same `build/` folder.
Pointing `--workpath` at a subfolder keeps PyInstaller's temporary files
separate from the checked-in spec — both `build/_cache/` and `dist/` are
already covered by `.gitignore` and safe to delete any time.

The final app lands in `dist/FeatherPDF/` — that whole folder is what you
share, not just the `.exe` inside it (it depends on the sibling files next
to it). See the comments at the top of `build/pyinstaller.spec` for a
couple of manual size-trimming steps if you want to squeeze it further.

**Windows: `pyinstaller: command not found`?** This is a PATH issue, not a
missing-install issue — pip installed it, but to your *user* site-packages
(you'll see "Defaulting to user installation" in the pip output) because
your main Python folder isn't writable, and that user folder's `Scripts`
directory usually isn't on PATH. Two ways to fix it:

- **Easiest — skip the PATH entirely:** run it as a Python module instead
  of a standalone command, which always works since `python` itself is
  already on PATH:
  ```bash
  python -m PyInstaller build/pyinstaller.spec --workpath build/_cache
  ```
- **Or add it to PATH properly:** find the folder pip installed into (shown
  in the "Requirement already satisfied" line, typically something like
  `C:\Users\<you>\AppData\Roaming\Python\Python3XX\site-packages`), go up
  one level to its sibling `Scripts` folder, and add *that* to your PATH
  environment variable. Restart your terminal afterward — PATH changes
  don't apply to already-open shells.

### Sharing the built .exe

Zip the whole `dist/FeatherPDF/` folder before sending it to anyone:

```powershell
Compress-Archive -Path dist\FeatherPDF -DestinationPath FeatherPDF-Windows.zip
```

Recipients unzip it and run `FeatherPDF.exe` directly — no Python or
install step needed on their end. Unsigned `.exe` files commonly trigger a
Windows SmartScreen "unrecognized publisher" warning; that's expected for
an unsigned build, not a sign anything's wrong — tell recipients to click
"More info → Run anyway."

---

## Project structure

```
featherpdf/
├── main.py                  # entry point (splash screen -> main window)
├── requirements.txt
├── LICENSE
├── config/settings.json     # persisted preferences
├── app/
│   ├── core/                # PDF logic only, no GUI (document, merge/split,
│   │                          convert, scan effects, compression, annotations,
│   │                          search, metadata, undo/redo, text-to-speech)
│   ├── render/               # page -> image rendering + LRU caches
│   ├── state/                # app-wide and per-tab state
│   ├── gui/                  # all Tkinter windows, dialogs, toolbars,
│   │                           flow-layout container
│   └── utils/                 # file dialogs, shortcuts, printing, logging
├── assets/
│   ├── icons/                 # the animated logo + generated frames
│   └── screenshots/            # README demo GIF + static screenshot
├── tools/generate_logo.py     # regenerates the logo assets (dev-only)
└── build/pyinstaller.spec     # packaging config
```

`app/core` never imports from `app/gui` — the PDF logic works standalone
and is unit-testable without opening a window.

---

## Usage

See **[WALKTHROUGH.md](WALKTHROUGH.md)** for a full guided tour of every
feature with step-by-step instructions and a keyboard shortcut reference.

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

## License

FeatherPDF is released under a custom **Attribution — Non-Commercial**
license (see [LICENSE](LICENSE) for the full text). In short:

- ✅ **Free to use and modify** for your own personal, educational, or
  internal projects
- ✅ **Free to share** modified or unmodified copies
- 🔒 **Credit required** — any use, share, or modification must visibly
  credit the original author: *FeatherPDF by Mehedy
  ([mehedy.netlify.app](https://mehedy.netlify.app))*
- ❌ **No selling or commercial resale** of the software (as-is or
  modified) without asking first

Not a lawyer, not legal advice — if you have a commercial use case with
real stakes, reach out via [mehedy.netlify.app](https://mehedy.netlify.app)
first.

---

<div align="center">

Made with 🪶 by **[Mehedy](https://mehedy.netlify.app)**

</div>
