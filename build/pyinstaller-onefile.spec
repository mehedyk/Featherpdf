# build/pyinstaller-onefile.spec
# Build with:  python -m PyInstaller build/pyinstaller-onefile.spec --workpath build/_cache
#
# Produces a SINGLE FILE: dist/FeatherPDF.exe -- nothing else needed next to
# it, no _internal/ folder, genuinely one independent file you can email,
# put on a USB stick, or drop in any folder and run.
#
# TRADE-OFF vs pyinstaller.spec (the --onedir build): onefile is more
# convenient to share but slower to START -- every launch, it silently
# unpacks itself into a temp folder before running (usually under a
# second, but noticeable), whereas onedir is already unpacked and starts
# faster. Use onefile for "send one file to a non-technical person to try
# it"; use the onedir + Inno Setup installer (see README.md) for anything
# you expect people to use regularly, since a real install feels faster
# and behaves like a normal installed app (Start Menu entry, uninstaller).
#
# Everything else -- the icon, the hidden imports, the excludes that keep
# OpenCV/numpy out of the base build -- is identical to pyinstaller.spec.
# Keep the two in sync if you change one.

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../assets', 'assets'),
        ('../config', 'config'),
    ],
    hiddenimports=[
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'pyttsx3.drivers.nsss',
        'pyttsx3.drivers.espeak',
    ],
    hookspath=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'test', 'unittest', 'pydoc_data',
        'cv2', 'opencv_contrib_python', 'opencv_python', 'opencv_python_headless',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FeatherPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='../assets/icons/icon.ico',
)
