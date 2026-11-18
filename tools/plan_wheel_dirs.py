"""List every directory stored in the downloaded wheels so PowerShell can pre-create them.

The Windows sandbox reliably allows writing files into directories that already
exist when the process starts, but writes into directories created by the same
process are intermittently denied.  Pre-creating the whole tree turns wheel
extraction into plain file writes.
"""
from __future__ import annotations

import os
import zipfile

WHEELS = ".tmp/wheels"
OUT = "reports/wheel_dirs.txt"


def main() -> None:
    dirs: set[str] = set()
    for filename in sorted(os.listdir(WHEELS)):
        if not filename.endswith(".whl"):
            continue
        with zipfile.ZipFile(os.path.join(WHEELS, filename)) as zf:
            for info in zf.infolist():
                name = info.filename
                if name.endswith("/"):
                    names = [name.rstrip("/")]
                else:
                    names = [os.path.dirname(name)]
                for d in names:
                    if d:
                        # include all ancestors
                        parts = d.split("/")
                        for i in range(1, len(parts) + 1):
                            dirs.add("/".join(parts[:i]))
    os.makedirs("reports", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        for d in sorted(dirs):
            fh.write(d.replace("/", "\\") + "\n")
    print(f"{len(dirs)} directories -> {OUT}")


if __name__ == "__main__":
    main()
