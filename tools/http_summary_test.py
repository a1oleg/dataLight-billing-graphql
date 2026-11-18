"""HTTP smoke test for the discrepancy summary query."""
from __future__ import annotations

import json
import urllib.request

QUERY = """
{
  discrepancySummary {
    requests
    matchedRequests
    discrepantRequests
    groups {
      code
      title
      requests
      recordedTotal
      calculatedTotal
      differenceTotal
      sampleRequestIds
    }
  }
}
"""

request = urllib.request.Request(
    "http://127.0.0.1:8765/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"content-type": "application/json"},
)
result = json.load(urllib.request.urlopen(request, timeout=300))
print(json.dumps(result, ensure_ascii=False, indent=1))
