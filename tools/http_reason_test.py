"""Smoke test for the writeReason argument and reasonWritten field."""
from __future__ import annotations

import json
import urllib.request

QUERY = """
{
  calculateRow(rowNumber: 5, writeReason: false) {
    row { requestId rowNumber }
    written { workbook calculatedWritten differenceWritten reasonWritten }
  }
}
"""

request = urllib.request.Request(
    "http://127.0.0.1:8765/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"content-type": "application/json"},
)
print(json.dumps(json.load(urllib.request.urlopen(request, timeout=120)), ensure_ascii=False, indent=1))
