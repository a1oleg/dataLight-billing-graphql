"""Run the GraphQL service: python server.py (PYTHONPATH must include deps/)."""
from __future__ import annotations

import os

import uvicorn

from billing.app import app


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
