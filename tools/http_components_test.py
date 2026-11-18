"""HTTP test for non-zero component lists and schema field order."""
from __future__ import annotations

import json
import urllib.request

URL = "http://127.0.0.1:8765/graphql"


def gql(query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(request, timeout=120))


def main() -> None:
    query = """
    {
      calculateRow(rowNumber: 9) {
        row { requestId rowNumber }
        recorded { components { code amount } total }
        calculated { components { code tokens ratePerMillion amount } total }
        difference { components { code amount } total }
      }
    }
    """
    print(json.dumps(gql(query), ensure_ascii=False, indent=1))

    with_zero = """
    {
      calculateRow(rowNumber: 9) {
        recorded { components(includeZero: true) { code amount } }
        calculated { components(includeZero: true) { code amount } }
        difference { components(includeZero: true) { code amount } total }
      }
    }
    """
    print("includeZero:", json.dumps(gql(with_zero), ensure_ascii=False)[:800])

    order = gql('{ __type(name: "RowCalculation") { fields { name } } }')
    print("RowCalculation fields:", [field["name"] for field in order["data"]["__type"]["fields"]])


if __name__ == "__main__":
    main()
