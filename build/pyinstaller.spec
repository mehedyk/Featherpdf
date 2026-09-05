# build/pyinstaller.spec
# Build with:  python -m PyInstaller build/pyinstaller.spec --workpath build/_cache
# (use "python -m PyInstaller" rather than the bare "pyinstaller" command --
#  on Windows, pip often installs the console script to a user Scripts folder
#  that isn't on PATH, and the module form always works since it just needs
#  "python" on PATH, which it already is)
# (the --workpath flag matters too: PyInstaller's own build cache defaults to
#  ./build/<specname>/, which collides with this very file living at
#  build/pyinstaller.spec -- pointing --workpath at a subfolder keeps its
#  temp files out of the way. Both build/_cache/ and dist/ are gitignored.)
# Produces a --onedir build (faster startup than --onefile) in dist/FeatherPDF/
#
# Size-reduction notes:
#  - excludes are listed for common heavy stdlib/pillow extras this app never uses
#  - Tcl/Tk's own bundled demo/doc files are NOT excluded automatically by PyInstaller;
#    if you need to shave more, manually prune dist/FeatherPDF/_internal/tcl8.6/{demos,tzdata}
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
    hiddenimports=[
        # pyttsx3 loads its platform speech driver dynamically at runtime
        # (importlib, not a plain "import" statement), which PyInstaller's
        # static analysis can miss -- without these listed explicitly, the
        # built exe can fail to find the driver on a machine where it wasn't
        # built, even though `pip install pyttsx3` alone works fine locally.
        # Windows only needs sapi5, but listing all three keeps this spec
        # correct regardless of which OS you build it on.
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'pyttsx3.drivers.nsss',
        'pyttsx3.drivers.espeak',
    ],
    hookspath=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',   # not used by this app
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',     # we use Tkinter only
        'test', 'unittest', 'pydoc_data',
        # cv2/numpy power the OPTIONAL Auto-Crop feature (see core/auto_crop.py)
        # and are never imported at module level anywhere in the app -- but
        # PyInstaller's static analysis finds the "import cv2"/"import numpy"
        # text inside auto_crop.py's functions regardless of it being a lazy,
        # conditional import, and will bundle the real packages (91MB+ for
        # OpenCV alone) if they happen to be installed on the machine doing
        # the build -- which is exactly what happens if you've locally
        # installed requirements-optional.txt to test Auto-Crop yourself.
        # Excluding them here keeps the STANDARD build genuinely lite
        # regardless of what's on the build machine; see
        # pyinstaller-with-autocrop.spec for the variant that intentionally
        # includes them.
        'cv2', 'opencv_contrib_python', 'opencv_python', 'opencv_python_headless',
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
    icon='../assets/icons/icon.ico',
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
