"""Tests for the calculated-vs-recorded difference."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from billing.calculator import LogRow, calculate  # noqa: E402
from billing.comparison import difference  # noqa: E402
from billing.logs import RequestLog, load_logs  # noqa: E402


def calc(row: RequestLog):
    return calculate(
        LogRow(
            start_time=row.start_time,
            model=row.model_name,
            usage=row.usage,
            request_id=row.request_id,
            organization_id=row.organization_id,
            status=row.status,
            cache_creation_cost=row.recorded.cache_creation,
            web_search_cost=row.recorded.web_search,
        )
    )


class TestDifference(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_logs()

    def test_matching_row_has_zero_difference(self) -> None:
        row = self.rows["06faa446-23f5-4386-9838-81d847e3405d"]
        diff = difference(calc(row), row.recorded)
        self.assertAlmostEqual(diff.total, 0.0, places=12)
        for field in ("input", "cached_input", "output", "reasoning"):
            self.assertAlmostEqual(getattr(diff, field), 0.0, places=12)

    def test_reasoning_double_billing_is_negative(self) -> None:
        row = self.rows["99bd4acd-cf50-415d-b263-fb81683bbef0"]
        diff = difference(calc(row), row.recorded)
        self.assertAlmostEqual(diff.reasoning, -0.000313, places=12)
        self.assertAlmostEqual(diff.total, -0.000313, places=12)
        self.assertAlmostEqual(diff.input, 0.0, places=12)

    def test_off_peak_in_peak_window_is_positive(self) -> None:
        row = self.rows["resp_04436d5c-b9ec-92ea-aae4-941c162ea044"]
        diff = difference(calc(row), row.recorded)
        self.assertAlmostEqual(diff.input, 0.021588424, places=12)
        self.assertAlmostEqual(diff.total, 0.023231494, places=12)


if __name__ == "__main__":
    unittest.main()
