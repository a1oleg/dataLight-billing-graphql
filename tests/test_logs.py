"""Tests for the raw log lookup used by the ``logRow`` query."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from billing.enums import ModelName  # noqa: E402
from billing.logs import load_logs, load_logs_by_row  # noqa: E402


class TestLogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_logs()

    def test_known_request_row(self) -> None:
        row = self.rows["06faa446-23f5-4386-9838-81d847e3405d"]
        self.assertEqual(row.model_name, ModelName.DEEPSEEK_V4_FLASH)
        self.assertEqual(row.client, "ООО Вектор")
        self.assertEqual(row.status, "success")
        self.assertEqual(row.usage.prompt_tokens, 1020)
        self.assertEqual(row.usage.text_tokens, 591)
        self.assertAlmostEqual(row.recorded.total, 0.0015399512, places=12)
        self.assertEqual(row.row_number, 5)  # first data row in the sheet

    def test_excel_row_lookup(self) -> None:
        by_row = load_logs_by_row()
        self.assertEqual(len(by_row), 30980)
        self.assertEqual(by_row[5].request_id, "06faa446-23f5-4386-9838-81d847e3405d")
        self.assertEqual(by_row[30984].request_id, "gen-1792022391-CBwGwO5FBtw4TZiQLhUr")
        self.assertNotIn(1, by_row)
        self.assertNotIn(30985, by_row)

    def test_unknown_request_is_absent(self) -> None:
        self.assertNotIn("no-such-request", self.rows)


if __name__ == "__main__":
    unittest.main()
