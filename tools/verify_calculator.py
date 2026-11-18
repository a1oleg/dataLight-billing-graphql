"""Verify the calculator against real log rows from the workbook."""
from __future__ import annotations

import os
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.abspath("."))

from billing.calculator import LogRow, calculate  # noqa: E402
from billing.enums import ModelName  # noqa: E402
from billing.formulas import Usage  # noqa: E402

XLSX = "data/DeepSeek_peak_offpeak_октябрь_2026_Тест.xlsx"
SAMPLE_IDS = [
    "06faa446-23f5-4386-9838-81d847e3405d",
    "7e42a397-1a83-4f03-93c2-dbf8e1f629c9",
    "99bd4acd-cf50-415d-b263-fb81683bbef0",
    "resp_04436d5c-b9ec-92ea-aae4-941c162ea044",
    "chatcmpl-fabd7e24-2b03-986c-9247-5df0fbd1ffa4",
    "e22a748c-70bc-480f-94af-a0ee7735456f",
]


def parse_start(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d %H:%M:%S.%f")


def main() -> None:
    frame = pd.read_excel(XLSX, sheet_name="Сырые логи", header=3)
    frame.columns = [str(c).strip() for c in frame.columns]
    frame = frame.rename(columns={"Клиент": "client"})
    by_id = frame.set_index("request_id")

    print(f"{'request_id':38s} {'model':32s} {'window':12s} {'computed':>12s} {'recorded':>12s} {'diff':>11s}")
    for request_id in SAMPLE_IDS:
        r = by_id.loc[request_id]
        usage = Usage(
            prompt_tokens=int(r.prompt_tokens),
            completion_tokens=int(r.completion_tokens),
            cached_input_tokens=int(r.cached_input_tokens),
            cache_creation_tokens=int(r.cache_creation_tokens),
            reasoning_tokens=int(r.reasoning_tokens),
            accepted_prediction_tokens=int(r.accepted_prediction_tokens),
            rejected_prediction_tokens=int(r.rejected_prediction_tokens),
            image_tokens=int(r.image_tokens),
            output_image_tokens=int(r.output_image_tokens),
            audio_input_tokens=int(r.audio_input_tokens),
            audio_output_tokens=int(r.audio_output_tokens),
            total_tokens=int(r.total_tokens),
        )
        row = LogRow(
            start_time=parse_start(r["start_time (UTC)"]),
            model=ModelName(str(r.model_group)),
            usage=usage,
            request_id=request_id,
            organization_id=str(r.organization_id),
            status=str(r.status),
            cache_creation_cost=float(r.cache_creation_cost),
            web_search_cost=float(r.web_search_cost),
        )
        result = calculate(row)
        recorded = float(r.total_cost)
        print(
            f"{request_id:38s} {r.model_group:32s} {result.window.label:12s} "
            f"{result.total:12.9f} {recorded:12.9f} {result.total - recorded:+11.9f}"
        )


if __name__ == "__main__":
    main()
