"""Install the GraphiQL UMD bundle (with React 18 UMD) into web/."""
from __future__ import annotations

import json
import os
import tarfile
import urllib.request

DEST = ".tmp/pkgs"
WEB = "web"

PACKAGES = {
    "graphiql": ("4.0.0", {"graphiql.min.js", "graphiql.min.css"}),
    "react": ("18.3.1", {"react.production.min.js"}),
    "react-dom": ("18.3.1", {"react-dom.production.min.js"}),
}


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def download(url: str, path: str) -> None:
    if os.path.exists(path):
        return
    with urllib.request.urlopen(url, timeout=180) as resp, open(path, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)


def main() -> None:
    os.makedirs(DEST, exist_ok=True)
    os.makedirs(WEB, exist_ok=True)
    for name, (version, wanted) in PACKAGES.items():
        meta = fetch_json(f"https://registry.npmjs.org/{name}/{version}")
        tarball = meta["dist"]["tarball"]
        path = os.path.join(DEST, f"{name}-{version}.tgz")
        download(tarball, path)
        with tarfile.open(path, "r:gz") as tf:
            for member in tf.getmembers():
                base = os.path.basename(member.name)
                if base not in wanted:
                    continue
                data = tf.extractfile(member).read()
                out = os.path.join(WEB, base)
                with open(out, "wb") as fh:
                    fh.write(data)
                print(f"{name} {version}: {base} {len(data)} bytes")


if __name__ == "__main__":
    main()
