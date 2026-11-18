"""HTTP smoke test for logRow by id and by row number."""
from __future__ import annotations

import json
import urllib.request

URL = "http://127.0.0.1:8765/graphql"

QUERY = """
query Row($id: ID, $number: Int) {
  logRow(requestId: $id, rowNumber: $number) {
    requestId
    rowNumber
    modelGroup
    status
    usage { promptTokens completionTokens textTokens }
    recorded { total }
    calculated { total }
    difference { total }
  }
}
"""


def gql(variables: dict) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    request = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(request, timeout=120))


def main() -> None:
    cases = [
        ("by id", {"id": "06faa446-23f5-4386-9838-81d847e3405d"}),
        ("by rowNumber=5", {"number": 5}),
        ("by rowNumber=30984", {"number": 30984}),
        ("rowNumber=1", {"number": 1}),
        ("no arguments", {}),
        ("both (id wins)", {"id": "99bd4acd-cf50-415d-b263-fb81683bbef0", "number": 5}),
    ]
    for name, variables in cases:
        result = gql(variables)
        print(f"== {name} ==")
        print(json.dumps(result, ensure_ascii=False, indent=1)[:800])


if __name__ == "__main__":
    main()
