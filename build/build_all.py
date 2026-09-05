#!/usr/bin/env python3
"""
build/build_all.py
Builds all three PyInstaller variants in one go, and -- this is the part
that actually matters -- moves each one's output out of the way before
starting the next, since all three specs produce something named
"FeatherPDF" and would otherwise silently overwrite each other in dist/.

Usage:
    python build/build_all.py                 # builds all three
    python build/build_all.py standard         # builds just one
    python build/build_all.py onefile
    python build/build_all.py autocrop

Output layout after a full run:
    dist_builds/
        standard/FeatherPDF/       (~115 MB folder)
        onefile/FeatherPDF.exe     (~52 MB single file)
        autocrop/FeatherPDF/       (~200 MB folder, OpenCV bundled)

Requires PyInstaller (`pip install pyinstaller`). The autocrop variant
additionally requires OpenCV to be installed in this environment first
(`pip install -r requirements-optional.txt`) -- otherwise PyInstaller has
nothing to bundle and that build's Auto-Crop button won't actually work,
silently defeating the point of building this variant at all. This script
checks for that and warns you before wasting time on the build.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT, "build")
DIST_DIR = os.path.join(ROOT, "dist")
OUTPUT_ROOT = os.path.join(ROOT, "dist_builds")
CACHE_DIR = os.path.join(BUILD_DIR, "_cache")

VARIANTS = {
    "standard": {
        "spec": "pyinstaller.spec",
        "produces": "dir",          # dist/FeatherPDF/ (a folder)
        "needs_opencv": False,
    },
    "onefile": {
        "spec": "pyinstaller-onefile.spec",
        "produces": "file",         # dist/FeatherPDF.exe (or FeatherPDF, no ext, on Linux/Mac)
        "needs_opencv": False,
    },
    "autocrop": {
        "spec": "pyinstaller-with-autocrop.spec",
        "produces": "dir",
        "needs_opencv": True,
    },
}


def opencv_available():
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        return False


def clean_dist():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)


def build_variant(key):
    info = VARIANTS[key]

    if info["needs_opencv"] and not opencv_available():
        print(f"\n[{key}] SKIPPED -- this variant needs OpenCV installed first:")
        print("    pip install -r requirements-optional.txt")
        return False

    spec_path = os.path.join("build", info["spec"])
    print(f"\n[{key}] Building with {info['spec']} ...")

    # Each variant gets its OWN cache subfolder, never shared with the others.
    # PyInstaller's build cache can otherwise carry stale analysis/binaries
    # across specs when the same --workpath is reused back-to-back for
    # different specs in one session -- confirmed this empirically: reusing
    # one shared cache folder across all three builds inflated every variant
    # well past its true size (e.g. the plain "standard" build measured
    # 159MB instead of its real ~114MB, and "autocrop" hit 524MB instead of
    # ~200MB) purely from cross-contamination, not any actual code change.
    variant_cache = os.path.join(CACHE_DIR, key)
    if os.path.exists(variant_cache):
        shutil.rmtree(variant_cache)

    clean_dist()
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", spec_path,
         "--workpath", variant_cache, "--noconfirm"],
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"[{key}] BUILD FAILED (PyInstaller exited with {result.returncode})")
        return False

    dest = os.path.join(OUTPUT_ROOT, key)
    if os.path.exists(dest):
        shutil.rmtree(dest) if os.path.isdir(dest) else os.remove(dest)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    if info["produces"] == "dir":
        src = os.path.join(DIST_DIR, "FeatherPDF")
        shutil.move(src, dest)
        size_mb = _dir_size_mb(dest)
    else:
        # onefile: PyInstaller names it "FeatherPDF" on Linux/Mac, "FeatherPDF.exe" on Windows
        src_candidates = [os.path.join(DIST_DIR, "FeatherPDF.exe"), os.path.join(DIST_DIR, "FeatherPDF")]
        src = next((p for p in src_candidates if os.path.exists(p)), None)
        if not src:
            print(f"[{key}] BUILD FAILED -- expected output not found in dist/")
            return False
        os.makedirs(dest, exist_ok=True)
        final_path = os.path.join(dest, os.path.basename(src))
        shutil.move(src, final_path)
        size_mb = os.path.getsize(final_path) / (1024 * 1024)

    print(f"[{key}] Done -> {dest}  ({size_mb:.0f} MB)")
    return True


def _dir_size_mb(path):
    """
    Sums real file bytes only, skipping symlinks. PyInstaller creates many
    versioned symlink aliases pointing at the same shared library (e.g.
    libX11.so.6 alongside a couple of other names for the same file) --
    counting the target size once per symlink inflates the total well
    past the real on-disk size, the same mistake `du` avoids by default.
    """
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp) and not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def main():
    requested = sys.argv[1:] or list(VARIANTS.keys())
    unknown = [r for r in requested if r not in VARIANTS]
    if unknown:
        print(f"Unknown variant(s): {unknown}. Choose from: {list(VARIANTS.keys())}")
        sys.exit(1)

    print(f"Building: {requested}")
    results = {key: build_variant(key) for key in requested}

    clean_dist()  # tidy up the scratch dist/ folder now that everything's moved

    print("\n" + "=" * 50)
    print("SUMMARY")
    for key, ok in results.items():
        print(f"  {key}: {'OK' if ok else 'SKIPPED/FAILED'}")
    print(f"\nBuilt outputs are in: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
