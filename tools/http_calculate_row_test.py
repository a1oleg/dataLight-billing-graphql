"""HTTP smoke test for the calculateRow query."""
from __future__ import annotations

import json
import urllib.request

URL = "http://127.0.0.1:8765/graphql"

QUERY = """
query Row($id: ID, $number: Int) {
  calculateRow(requestId: $id, rowNumber: $number) {
    row { requestId rowNumber modelGroup }
    calculated { window { label tier } total }
    recorded { total }
    difference { input cachedInput output reasoning total }
  }
}
"""


def gql(variables: dict) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    request = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(request, timeout=120))


def main() -> None:
    cases = [
        ("first row", {"number": 5}),
        ("reasoning row", {"id": "99bd4acd-cf50-415d-b263-fb81683bbef0"}),
        ("off-peak row", {"id": "resp_04436d5c-b9ec-92ea-aae4-941c162ea044"}),
        ("missing row", {"number": 1}),
    ]
    for name, variables in cases:
        result = gql(variables)
        payload = result["data"]["calculateRow"]
        print(f"== {name} ==")
        if payload is None:
            print("  null")
            continue
        row = payload["row"]
        diff = payload["difference"]
        print(
            f"  {row['requestId']} (row {row['rowNumber']}, {row['modelGroup']})\n"
            f"  window={payload['calculated']['window']['label']} "
            f"calculated={payload['calculated']['total']:.12f} "
            f"recorded={payload['recorded']['total']:.12f} "
            f"difference={diff['total']:+.12f}\n"
            f"  diff input={diff['input']:+.12f} cached={diff['cachedInput']:+.12f} "
            f"output={diff['output']:+.12f} reasoning={diff['reasoning']:+.12f}"
        )


if __name__ == "__main__":
    main()
