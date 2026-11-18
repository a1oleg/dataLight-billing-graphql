"""Recalculate every log row and write calculated/difference columns into the original workbook."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from billing.writer import write_all  # noqa: E402

summary = write_all()
print(f"workbook={summary.workbook}")
print(f"rows={summary.rows}")
