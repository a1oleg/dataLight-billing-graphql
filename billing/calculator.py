"""Calculator: a log row in, an itemised calculation out."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from .enums import ModelName
from .formulas import CostLine, Usage, compute_lines, total
from .logs import RequestLog
from .tariffs import Model, TariffWindow, load_models


@dataclass(frozen=True)
class LogRow:
    start_time: datetime
    model: ModelName
    usage: Usage
    request_id: str | None = None
    organization_id: str | None = None
    status: str | None = None
    cache_creation_cost: float = 0.0
    web_search_cost: float = 0.0


@dataclass(frozen=True)
class Calculation:
    request_id: str | None
    model: Model
    window: TariffWindow
    usage: Usage
    lines: tuple[CostLine, ...]
    total: float


def calculate(row: LogRow, models: Mapping[ModelName, Model] | None = None) -> Calculation:
    catalogue = models if models is not None else load_models()
    model = catalogue[row.model]
    window = model.window_at(row.start_time)
    if window is None:
        raise ValueError(
            f"no tariff window for {row.model.value} at {row.start_time.isoformat()}"
        )
    lines = compute_lines(row.usage, window, row.cache_creation_cost, row.web_search_cost)
    return Calculation(
        request_id=row.request_id,
        model=model,
        window=window,
        usage=row.usage,
        lines=tuple(lines),
        total=total(lines),
    )


def calculate_log_row(row: RequestLog) -> Calculation:
    """Calculate a workbook log row using its model and recorded cache/web costs."""
    if row.model_name is None:
        raise ValueError(f"model {row.model_group!r} is not in the price list")
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
