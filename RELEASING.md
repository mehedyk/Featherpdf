<div align="center">
<img src="assets/icons/logo.gif" width="90" alt="FeatherPDF logo">

# RELEASING.md — cutting a new release

</div>

This is for whoever maintains this repo, not for people just wanting to
download and use the app (that's [the Download section in
README.md](README.md#download)).

Built executables are **never committed to the repo** — they're
attached to GitHub Releases instead. Committing 50–300MB binaries
directly into git bloats the repo's history permanently: even if you
delete the file in a later commit, everyone who clones the repo still
downloads it from history forever. Releases keep binaries versioned and
downloadable without that cost.

## 1. Build everything

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # needed for the autocrop variant
pip install pyinstaller

python build/build_all.py
```

This produces (see README.md's build section for exact measured sizes):
```
dist_builds/
    standard/FeatherPDF/       (folder -- feeds the installer, step 2)
    onefile/FeatherPDF.exe     (single file -- rename directly, step 3)
    autocrop/FeatherPDF/       (folder -- zip it, step 3)
```

If `dist_builds/autocrop/` is missing, `requirements-optional.txt` wasn't
installed before the build — the script skips that variant rather than
failing, but you'll want it present for a real release.

## 2. Build the installer (from the `standard` output)

Requires [Inno Setup](https://jrsoftware.org/isdl.php) on Windows:

```bash
ISCC.exe build\installer.iss
```

This reads `dist/FeatherPDF/` (Inno Setup's script expects the plain
`dist/` path, not `dist_builds/standard/` — either re-run just the
standard build with `python build/build_all.py standard` right before
this step so `dist/` is freshly populated, or point `installer.iss`'s
`[Files]` source at `dist_builds\standard\FeatherPDF\*` instead if you'd
rather not rebuild).

Output: `dist_installer/FeatherPDF-Setup.exe` — this is asset #1.

## 3. Name and package the other two assets

The filenames below are exactly what README.md's Download table links
to — **matching them precisely matters**, since GitHub's
`/releases/latest/download/<filename>` links only work if the attached
asset is named exactly that.

```bash
# Asset 2: the portable single-file exe, just needs renaming
cp dist_builds/onefile/FeatherPDF.exe FeatherPDF-Portable.exe

# Asset 3: the autocrop-bundled folder, zipped
# (PowerShell)
Compress-Archive -Path dist_builds\autocrop\* -DestinationPath FeatherPDF-AutoCrop.zip
```

You should now have three files ready to upload:
- `dist_installer/FeatherPDF-Setup.exe`
- `FeatherPDF-Portable.exe`
- `FeatherPDF-AutoCrop.zip`

## 4. Publish the release on GitHub

**Via the web UI:** repo page → **Releases** → **Draft a new release** →
pick a tag (e.g. `v1.0.0`) → drag all three files into the assets area →
**Publish release**.

**Via the `gh` CLI**, if you have it installed:
```bash
gh release create v1.0.0 \
    dist_installer/FeatherPDF-Setup.exe \
    FeatherPDF-Portable.exe \
    FeatherPDF-AutoCrop.zip \
    --title "FeatherPDF v1.0.0" \
    --notes "See README.md for what's new."
```

## 5. Double-check the README's Download links actually work

`README.md`'s Download table uses `YOUR-USERNAME/featherpdf` as a
placeholder — make sure that's been replaced with this repo's real
GitHub path (in both the Download section and here in RELEASING.md's
`gh release create` example, if you copy it). After publishing, click
each of the three README download links yourself once to confirm they
resolve — a typo'd filename here is a silent broken link, not an error
anyone sees until a user reports it.

## Versioning note

`build/installer.iss` has its own `AppVersion` (`#define MyAppVersion`)
separate from the git tag — bump that too when you cut a release with
real changes, so Windows' "Apps & Features" shows the right version
number and future installers correctly recognize themselves as upgrades
rather than fresh installs.
