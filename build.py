#!/usr/bin/env python3
"""Vane — packages the skin into a WeeWX-installable zip.

Usage:
    python build.py

Reads the version and file list straight out of install.py via `ast` (not
`import` — install.py imports `weecfg.extension`, which isn't installed on
a plain dev machine, only inside a WeeWX environment). This means the zip
can never silently drift out of sync with what `weectl extension install`
will actually look for: any file install.py declares but that doesn't
exist on disk fails the build instead of shipping a broken extension.

Output: dist/vane-<version>.zip, ready for:
    weectl extension install dist/vane-<version>.zip
"""
import ast
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"

# Not needed by WeeWX at install time (weectl only looks at install.py's own
# files=[...] list), but included anyway so a downloaded zip carries its own
# license/attribution instead of only being visible in the git repo — MIT
# (Meteocons/uPlot/MQTT.js) requires the notice to travel with the copy.
EXTRA_FILES = ["LICENSE", "THIRD-PARTY-LICENSES.md"]


def _extract_installer_info():
    tree = ast.parse((ROOT / "install.py").read_text(encoding="utf-8"))
    version = None
    files = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword):
            if node.arg == "version" and isinstance(node.value, ast.Constant):
                version = node.value.value
            if node.arg == "files" and isinstance(node.value, ast.List):
                for group in node.value.elts:
                    # Each group is (dest_dir, [file, file, ...]) — we only
                    # need the file paths, the dest_dir is install.py's own
                    # business at install time.
                    file_list = group.elts[1]
                    for f in file_list.elts:
                        files.append(f.value)
    return version, files


def main():
    version, files = _extract_installer_info()
    if not version or not files:
        raise SystemExit("Could not parse version/files out of install.py — "
                          "did its structure change?")

    missing = [f for f in files + EXTRA_FILES if not (ROOT / f).exists()]
    if missing:
        raise SystemExit(
            "install.py declares files that don't exist on disk:\n  " +
            "\n  ".join(missing) +
            "\n(fix install.py's files=[...] list or restore the file(s))")

    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"vane-{version}.zip"
    top = f"vane-{version}"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(ROOT / "install.py", f"{top}/install.py")
        for f in files:
            zf.write(ROOT / f, f"{top}/{f}")
        for f in EXTRA_FILES:
            zf.write(ROOT / f, f"{top}/{f}")

    print("Built %s (%d files, version %s)" % (
        zip_path, len(files) + 1 + len(EXTRA_FILES), version))


if __name__ == "__main__":
    main()
