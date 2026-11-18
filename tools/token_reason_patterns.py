"""Count difference patterns by reason and changed token components."""
from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath("."))

from billing.calculator import calculate_log_row  # noqa: E402
from billing.comparison import difference  # noqa: E402
from billing.logs import load_logs_by_row  # noqa: E402
from billing.summary import classify_log_row  # noqa: E402

FIELDS = [
    ("input", "input"),
    ("cachedInput", "cached_input"),
    ("output", "output"),
    ("reasoning", "reasoning"),
    ("prediction", "prediction"),
    ("image", "image"),
    ("cacheCreation", "cache_creation"),
    ("webSearch", "web_search"),
]

patterns = Counter()
for row in load_logs_by_row().values():
    calculation = calculate_log_row(row)
    diff = difference(calculation, row.recorded)
    changed = tuple(code for code, attr in FIELDS if abs(getattr(diff, attr)) > 1e-9)
    reason = classify_log_row(row, calculation, diff)
    patterns[(reason, changed)] += 1

for (reason, changed), count in patterns.most_common():
    print(f"{reason:32s} {str(changed):60s} {count}")
