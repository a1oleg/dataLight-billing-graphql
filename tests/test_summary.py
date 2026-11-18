"""Classification tests for the discrepancy summary."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from billing.calculator import calculate_log_row  # noqa: E402
from billing.comparison import difference  # noqa: E402
from billing.logs import load_logs  # noqa: E402
from billing.summary import (  # noqa: E402
    MATCH,
    OFF_PEAK_IN_PEAK,
    REASONING_DOUBLE,
    TOTAL_NOT_SUM,
    ZERO_TOTAL,
    _classify,
    cost_totals,
)


class TestSummaryClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_logs()

    def classify(self, request_id: str) -> str:
        row = self.rows[request_id]
        calculation = calculate_log_row(row)
        return _classify(row, calculation, difference(calculation, row.recorded))

    def test_match(self) -> None:
        self.assertEqual(self.classify("06faa446-23f5-4386-9838-81d847e3405d"), MATCH)

    def test_reasoning_double(self) -> None:
        self.assertEqual(
            self.classify("99bd4acd-cf50-415d-b263-fb81683bbef0"), REASONING_DOUBLE
        )

    def test_off_peak_in_peak(self) -> None:
        self.assertEqual(
            self.classify("resp_04436d5c-b9ec-92ea-aae4-941c162ea044"), OFF_PEAK_IN_PEAK
        )

    def test_zero_total(self) -> None:
        self.assertEqual(
            self.classify("e22a748c-70bc-480f-94af-a0ee7735456f"), ZERO_TOTAL
        )

    def test_total_not_sum(self) -> None:
        self.assertEqual(
            self.classify("chatcmpl-6c961de6-b0de-9a91-8835-35a79b0bfff3"), TOTAL_NOT_SUM
        )


class TestCostTotals(unittest.TestCase):
    def test_table_and_calculated_totals(self) -> None:
        totals = cost_totals()
        self.assertEqual(totals.requests, 30980)
        self.assertAlmostEqual(totals.recorded_total, 249.8098483731, places=6)
        self.assertAlmostEqual(totals.calculated_total, 244.7406233137, places=6)
        self.assertAlmostEqual(totals.difference_total, 5.0692250594, places=6)


if __name__ == "__main__":
    unittest.main()
