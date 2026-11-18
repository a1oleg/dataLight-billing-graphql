"""Print the first log rows whose recorded cost differs from the calculation."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from billing.calculator import LogRow, calculate  # noqa: E402
from billing.comparison import difference  # noqa: E402
from billing.logs import load_logs_by_row  # noqa: E402

COMPONENTS = ("input", "cached_input", "output", "reasoning", "prediction", "image", "cache_creation", "web_search")


def main() -> None:
    rows = sorted(load_logs_by_row().values(), key=lambda row: row.row_number)
    found = 0
    for row in rows:
        calculation = calculate(
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
        diff = difference(calculation, row.recorded)
        components = [name for name in COMPONENTS if abs(getattr(diff, name)) > 1e-9]
        if abs(diff.total) <= 1e-9 and not components:
            continue
        print(
            f"row {row.row_number}: {row.request_id} {row.model_group} "
            f"calculated={calculation.total:.12f} recorded={row.recorded.total:.12f} "
            f"difference={diff.total:+.12f} components={components or ['total']}"
        )
        found += 1
        if found >= 5:
            break


if __name__ == "__main__":
    main()
