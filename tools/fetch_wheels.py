"""Download the exact wheels needed for the GraphQL stack into .tmp/wheels.

pip cannot create its temporary directories reliably under the current Windows
sandbox policy, so the wheels are fetched directly from PyPI and installed by
``install_wheels.py`` after all target directories have been pre-created.
"""
from __future__ import annotations

import json
import os
import urllib.request

PKGS = [
    ("strawberry-graphql", "0.341.2"),
    ("graphql-core", "3.3.2"),
    ("typing-extensions", "4.16.0"),
    ("python-dateutil", "4.0.0"),
    ("uvicorn", "0.54.0"),
    ("click", "8.5.1"),
    ("h11", "0.16.0"),
    ("cross-web", "0.9.0"),
    ("packaging", "26.3"),
    ("tzdata", "2026.6"),
]

DEST = ".tmp/wheels"


def main() -> None:
    os.makedirs(DEST, exist_ok=True)
    for name, version in PKGS:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as resp:
            meta = json.load(resp)
        wheel = next(u for u in meta["urls"] if u["packagetype"] == "bdist_wheel")
        path = os.path.join(DEST, wheel["filename"])
        if os.path.exists(path) and os.path.getsize(path) == wheel["size"]:
            print("cached", wheel["filename"], wheel["size"])
            continue
        with urllib.request.urlopen(wheel["url"], timeout=120) as resp, open(path, "wb") as fh:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
        size = os.path.getsize(path)
        if size != wheel["size"]:
            raise SystemExit(f"size mismatch for {path}: {size} != {wheel['size']}")
        print("downloaded", wheel["filename"], size)


if __name__ == "__main__":
    main()
