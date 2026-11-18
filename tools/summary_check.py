"""Print discrepancy group counts."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from billing.summary import summarize  # noqa: E402

summary = summarize()
print(f"requests={summary.requests} matched={summary.matched_requests} discrepant={summary.discrepant_requests}")
for group in summary.groups:
    print(
        f"{group.code:32s} {group.requests:6d} "
        f"recorded={group.recorded_total:10.6f} "
        f"calculated={group.calculated_total:10.6f} "
        f"difference={group.difference_total:+10.6f}"
    )
