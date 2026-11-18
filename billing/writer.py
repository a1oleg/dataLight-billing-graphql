"""Write calculated and difference columns into the original workbook."""
from __future__ import annotations

import threading
from dataclasses import dataclass

import openpyxl

from .calculator import Calculation, calculate_log_row
from .comparison import CostDifference, difference
from .logs import DATA_XLSX, RequestLog, load_logs_by_row
from .summary import classify_log_row

HEADER_ROW = 4
DISCREPANCY_REASON = "discrepancy_reason"

CALCULATED_FIELDS = [
    ("input", "calculated_input_cost"),
    ("cachedInput", "calculated_cached_input_cost"),
    ("output", "calculated_output_cost"),
    ("reasoning", "calculated_reasoning_cost"),
    ("prediction", "calculated_prediction_cost"),
    ("image", "calculated_image_cost"),
    ("cacheCreation", "calculated_cache_creation_cost"),
    ("webSearch", "calculated_web_search_cost"),
]
CALCULATED_TOTAL = "calculated_total_cost"

DIFFERENCE_FIELDS = [
    ("input", "difference_input_cost"),
    ("cached_input", "difference_cached_input_cost"),
    ("output", "difference_output_cost"),
    ("reasoning", "difference_reasoning_cost"),
    ("prediction", "difference_prediction_cost"),
    ("image", "difference_image_cost"),
    ("cache_creation", "difference_cache_creation_cost"),
    ("web_search", "difference_web_search_cost"),
]
DIFFERENCE_TOTAL = "difference_total_cost"

_LOCK = threading.Lock()


@dataclass(frozen=True)
class WriteResult:
    workbook: str
    calculated_written: bool
    difference_written: bool
    reason_written: bool


@dataclass(frozen=True)
class WriteSummary:
    workbook: str
    rows: int


def _money(value: float) -> float:
    rounded = round(value, 12)
    return 0.0 if rounded == 0.0 else rounded


def _headers(ws) -> dict[str, int]:
    headers: dict[str, int] = {}
    for column in range(1, ws.max_column + 1):
        value = ws.cell(row=HEADER_ROW, column=column).value
        if value is not None:
            headers[str(value)] = column
    return headers


def _ensure_columns(ws, headers: dict[str, int], names: list[str]) -> dict[str, int]:
    columns: dict[str, int] = {}
    next_column = ws.max_column + 1
    for name in names:
        column = headers.get(name)
        if column is None:
            column = next_column
            next_column += 1
            ws.cell(row=HEADER_ROW, column=column, value=name)
            headers[name] = column
        columns[name] = column
    return columns


def _write_values(
    ws,
    row_number: int,
    calculation: Calculation,
    difference: CostDifference,
    calculated_columns: dict[str, int],
    difference_columns: dict[str, int],
    reason_column: int,
    reason: str | None,
    write_calculated: bool,
    write_difference: bool,
    write_reason: bool,
) -> None:
    amounts = {line.code: line.amount for line in calculation.lines}

    if write_calculated:
        for code, name in CALCULATED_FIELDS:
            ws.cell(row=row_number, column=calculated_columns[name], value=_money(amounts.get(code, 0.0)))
        ws.cell(row=row_number, column=calculated_columns[CALCULATED_TOTAL], value=_money(calculation.total))

    if write_difference:
        for field_name, name in DIFFERENCE_FIELDS:
            ws.cell(
                row=row_number,
                column=difference_columns[name],
                value=_money(getattr(difference, field_name)),
            )
        ws.cell(row=row_number, column=difference_columns[DIFFERENCE_TOTAL], value=_money(difference.total))

    if write_reason and reason is not None:
        ws.cell(row=row_number, column=reason_column, value=reason)


def write_row(
    row: RequestLog,
    calculation: Calculation,
    diff: CostDifference,
    write_calculated: bool,
    write_difference: bool,
    write_reason: bool,
) -> WriteResult | None:
    if not (write_calculated or write_difference or write_reason):
        return None

    with _LOCK:
        workbook = openpyxl.load_workbook(DATA_XLSX)
        try:
            ws = workbook["Сырые логи"]
            headers = _headers(ws)
            calculated_columns = _ensure_columns(
                ws, headers, [name for _, name in CALCULATED_FIELDS] + [CALCULATED_TOTAL]
            )
            difference_columns = _ensure_columns(
                ws, headers, [name for _, name in DIFFERENCE_FIELDS] + [DIFFERENCE_TOTAL]
            )
            reason_columns = _ensure_columns(ws, headers, [DISCREPANCY_REASON])
            reason = classify_log_row(row, calculation, diff) if write_reason else None
            _write_values(
                ws,
                row.row_number,
                calculation,
                diff,
                calculated_columns,
                difference_columns,
                reason_columns[DISCREPANCY_REASON],
                reason,
                write_calculated,
                write_difference,
                write_reason,
            )
            workbook.save(DATA_XLSX)
        finally:
            workbook.close()

    return WriteResult(
        workbook=str(DATA_XLSX),
        calculated_written=write_calculated,
        difference_written=write_difference,
        reason_written=write_reason,
    )


def write_all() -> WriteSummary:
    """Recalculate every log row and write both column groups into the original file."""
    rows = []
    with _LOCK:
        workbook = openpyxl.load_workbook(DATA_XLSX)
        try:
            ws = workbook["Сырые логи"]
            headers = _headers(ws)
            calculated_columns = _ensure_columns(
                ws, headers, [name for _, name in CALCULATED_FIELDS] + [CALCULATED_TOTAL]
            )
            difference_columns = _ensure_columns(
                ws, headers, [name for _, name in DIFFERENCE_FIELDS] + [DIFFERENCE_TOTAL]
            )
            reason_columns = _ensure_columns(ws, headers, [DISCREPANCY_REASON])

            rows = sorted(load_logs_by_row().values(), key=lambda item: item.row_number)
            for row in rows:
                calculation = calculate_log_row(row)
                diff = difference(calculation, row.recorded)
                reason = classify_log_row(row, calculation, diff)
                _write_values(
                    ws,
                    row.row_number,
                    calculation,
                    diff,
                    calculated_columns,
                    difference_columns,
                    reason_columns[DISCREPANCY_REASON],
                    reason,
                    True,
                    True,
                    True,
                )

            workbook.save(DATA_XLSX)
        finally:
            workbook.close()

    return WriteSummary(workbook=str(DATA_XLSX), rows=len(rows))
