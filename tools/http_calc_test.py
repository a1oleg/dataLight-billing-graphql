"""HTTP smoke test for the running calculator service."""
from __future__ import annotations

import json
import urllib.request

URL = "http://127.0.0.1:8765/graphql"


def gql(query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(request, timeout=60))


def main() -> None:
    html = urllib.request.urlopen("http://127.0.0.1:8765/", timeout=30).read().decode()
    print("GET / has calculate default:", "calculate(row:" in html)

    query = """
    query Calc($row: LogRowInput!) {
      calculate(row: $row) {
        requestId
        model { name slug }
        window { label tier }
        textTokens
        lines { code tokens ratePerMillion amount }
        total
      }
    }
    """
    row = {
        "requestId": "06faa446-23f5-4386-9838-81d847e3405d",
        "startTime": "2026-10-13T00:00:27.467Z",
        "model": "DEEPSEEK_V4_FLASH",
        "usage": {
            "promptTokens": 1020,
            "completionTokens": 2621,
            "cachedInputTokens": 128,
            "reasoningTokens": 2030,
        },
    }
    print(json.dumps(gql(query, {"row": row}), ensure_ascii=False, indent=1))

    models = gql("{ models { name slug } }")
    print("models:", [model["name"] for model in models["data"]["models"]])

    window = gql(
        '{ model(name: DEEPSEEK_FLASH) { slug windowAt(at: "2026-10-13T07:00:00Z") '
        "{ label tier inputPerMillion } } }"
    )
    print(json.dumps(window, ensure_ascii=False))


if __name__ == "__main__":
    main()
