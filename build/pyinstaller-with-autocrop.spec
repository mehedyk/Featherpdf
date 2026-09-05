# build/pyinstaller-with-autocrop.spec
# Build with:  python -m PyInstaller build/pyinstaller-with-autocrop.spec --workpath build/_cache
#
# Same as pyinstaller.spec (the standard --onedir build), except it does NOT
# exclude cv2/numpy -- so the Auto-Crop feature works out of the box for
# whoever you send this build to, with no separate `pip install` needed on
# their end. The trade-off is size: this build is roughly 90MB bigger
# (OpenCV itself), landing around 200MB total instead of ~115MB.
#
# You must have run `pip install -r requirements-optional.txt` yourself
# before building this -- PyInstaller can only bundle what's actually
# installed in the environment doing the build.
#
# Use this variant if you're distributing to people who you know want
# Auto-Crop and shouldn't have to think about installing anything extra.
# Use the standard pyinstaller.spec for everyone else.

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
        # cv2 is intentionally NOT excluded below, but its own optional
        # GUI-backend extras are still worth excluding explicitly since
        # this app never opens an OpenCV window -- only uses it for
        # headless image processing.
    ],
    hookspath=[],
    excludes=[
        'matplotlib', 'scipy', 'pandas',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'test', 'unittest', 'pydoc_data',
        # NOTE: numpy and cv2 are deliberately NOT in this list, unlike
        # pyinstaller.spec -- that's the entire point of this variant.
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
