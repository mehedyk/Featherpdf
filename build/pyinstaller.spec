# build/pyinstaller.spec
# Build with:  pyinstaller build/pyinstaller.spec
# Produces a --onedir build (faster startup than --onefile) in dist/PDFLiteSuite/
#
# Size-reduction notes:
#  - excludes are listed for common heavy stdlib/pillow extras this app never uses
#  - Tcl/Tk's own bundled demo/doc files are NOT excluded automatically by PyInstaller;
#    if you need to shave more, manually prune dist/PDFLiteSuite/_internal/tcl8.6/{demos,tzdata}
#    after building (tzdata is only needed if you rely on Tcl's clock/timezone commands, which
#    this app does not).

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../assets', 'assets'),
        ('../config', 'config'),
    ],
    hiddenimports=[],
    hookspath=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',   # not used by this app
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',     # we use Tkinter only
        'test', 'unittest', 'pydoc_data',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FeatherPDF',
    debug=False,
    strip=True,
    upx=True,
    console=False,
    icon='../assets/icons/logo.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    name='FeatherPDF',
)
