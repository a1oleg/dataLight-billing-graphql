"""Extract the downloaded wheels into deps/ (directory tree must already exist)."""
from __future__ import annotations

import os
import zipfile

WHEELS = ".tmp/wheels"
DEPS = "deps"


def main() -> None:
    count = 0
    for filename in sorted(os.listdir(WHEELS)):
        if not filename.endswith(".whl"):
            continue
        with zipfile.ZipFile(os.path.join(WHEELS, filename)) as zf:
            zf.extractall(DEPS)
            count += 1
        print("extracted", filename)
    print(f"{count} wheels -> {DEPS}")


if __name__ == "__main__":
    main()
