"""Smoke-test the calculator schema in-process."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from billing.schema import schema  # noqa: E402

models = schema.execute_sync(
    "{ models { name slug windows { label tier kind days startHour endHour "
    "inputPerMillion outputPerMillion cacheReadPerMillion } } }"
)
print("models errors:", models.errors)
print("models count:", len(models.data["models"]))
print("first model:", json.dumps(models.data["models"][0], ensure_ascii=False))

QUERY = """
query Calc($row: LogRowInput!) {
  calculate(row: $row) {
    requestId
    model { name slug }
    window { label tier kind startHour endHour }
    textTokens
    lines { code label tokens ratePerMillion amount }
    total
  }
}
"""

ROWS = {
    "v4-flash all-day": {
        "requestId": "06faa446-23f5-4386-9838-81d847e3405d",
        "startTime": "2026-10-13T00:00:27.467Z",
        "model": "DEEPSEEK_V4_FLASH",
        "usage": {
            "promptTokens": 1020,
            "completionTokens": 2621,
            "cachedInputTokens": 128,
            "reasoningTokens": 2030,
            "totalTokens": 3641,
        },
    },
    "v4-flash reasoning bug": {
        "requestId": "99bd4acd-cf50-415d-b263-fb81683bbef0",
        "startTime": "2026-10-13T00:00:35.755Z",
        "model": "DEEPSEEK_V4_FLASH",
        "usage": {"promptTokens": 1311, "completionTokens": 648, "reasoningTokens": 626},
    },
    "v4-flash-0731 peak": {
        "requestId": "resp_04436d5c-b9ec-92ea-aae4-941c162ea044",
        "startTime": "2026-10-13T00:13:10.199Z",
        "model": "DEEPSEEK_V4_FLASH_0731",
        "usage": {"promptTokens": 75484, "completionTokens": 1915},
    },
    "deepseek-flash peak": {
        "startTime": "2026-10-13T07:00:00Z",
        "model": "DEEPSEEK_FLASH",
        "usage": {"promptTokens": 1000, "cachedInputTokens": 200, "completionTokens": 500, "reasoningTokens": 100},
    },
}

for name, row in ROWS.items():
    result = schema.execute_sync(QUERY, variable_values={"row": row})
    print(f"\n== {name} ==")
    if result.errors:
        for error in result.errors:
            print("ERROR:", error)
        continue
    data = result.data["calculate"]
    print("window:", data["window"]["label"], data["window"]["tier"], "text:", data["textTokens"])
    for line in data["lines"]:
        if line["tokens"] or line["amount"]:
            print(f"  {line['code']:14s} tokens={line['tokens']} rate={line['ratePerMillion']} amount={line['amount']:.12f}")
    print("  TOTAL:", f"{data['total']:.12f}")
