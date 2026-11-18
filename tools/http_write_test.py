"""HTTP test: logRow/calculateRow with optional workbook writing."""
from __future__ import annotations

import json
import urllib.request

import openpyxl

URL = "http://127.0.0.1:8765/graphql"

QUERY = """
query Row($id: ID, $number: Int, $wc: Boolean!, $wd: Boolean!) {
  calculateRow(
    requestId: $id
    rowNumber: $number
    writeCalculated: $wc
    writeDifference: $wd
  ) {
    row {
      requestId
      rowNumber
      calculated { total }
      difference { total }
    }
    calculated { total }
    recorded { total }
    difference { reasoning total }
    written { workbook calculatedWritten differenceWritten }
  }
}
"""


def gql(variables: dict) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    request = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(request, timeout=300))


def main() -> None:
    read = gql({"id": None, "number": 9, "wc": False, "wd": False})
    print("read-only:", json.dumps(read, ensure_ascii=False)[:600])

    written = gql({"id": None, "number": 9, "wc": True, "wd": True})
    print("write:", json.dumps(written, ensure_ascii=False)[:600])
    payload = written["data"]["calculateRow"]
    if not payload or not payload.get("written"):
        return

    path = payload["written"]["workbook"]
    print("workbook:", path)
    workbook = openpyxl.load_workbook(path, data_only=True)
    ws = workbook["Сырые логи"]
    header = [cell.value for cell in next(ws.iter_rows(min_row=4, max_row=4))]
    calculated = [(i + 1, name) for i, name in enumerate(header) if name and str(name).startswith("calculated_")]
    difference = [(i + 1, name) for i, name in enumerate(header) if name and str(name).startswith("difference_")]
    print("calculated columns:", calculated)
    print("difference columns:", difference)
    values = {name: ws.cell(row=9, column=column).value for column, name in calculated + difference}
    print("row 9 values:")
    for name, value in values.items():
        print(f"  {name} = {value}")
    print("old total_cost AH9:", ws.cell(row=9, column=34).value)
    workbook.close()


if __name__ == "__main__":
    main()
