"""Count log rows by discrepancy group."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

from .calculator import calculate_log_row
from .comparison import CostDifference, difference
from .enums import PriceTier
from .logs import RequestLog, load_logs_by_row

TOL = 1e-9
REL = 1e-6

MATCH = "match"
REASONING_DOUBLE = "reasoning_double_billing"
OFF_PEAK_IN_PEAK = "off_peak_rate_in_peak_window"
ZERO_TOTAL = "zero_total"
TOTAL_NOT_SUM = "total_not_sum_of_components"
OTHER = "other"

TITLES = {
    MATCH: "расхождений нет",
    REASONING_DOUBLE: "reasoning по двойной ставке",
    OFF_PEAK_IN_PEAK: "off-peak цена в peak-окне",
    ZERO_TOTAL: "total_cost = 0 при ненулевых компонентах",
    TOTAL_NOT_SUM: "total_cost не равен сумме колонок",
    OTHER: "прочие расхождения",
}
ORDER = [MATCH, ZERO_TOTAL, TOTAL_NOT_SUM, REASONING_DOUBLE, OFF_PEAK_IN_PEAK, OTHER]

RECORDED_ATTR = {
    "input": "input",
    "cachedInput": "cached_input",
    "output": "output",
    "reasoning": "reasoning",
    "prediction": "prediction",
    "image": "image",
    "cacheCreation": "cache_creation",
    "webSearch": "web_search",
}
DIFF_ATTR = {
    "input": "input",
    "cachedInput": "cached_input",
    "output": "output",
    "reasoning": "reasoning",
    "prediction": "prediction",
    "image": "image",
    "cacheCreation": "cache_creation",
    "webSearch": "web_search",
}


@dataclass(frozen=True)
class DiscrepancyGroup:
    code: str
    title: str
    requests: int
    recorded_total: float
    calculated_total: float
    difference_total: float
    sample_request_ids: tuple[str, ...]


@dataclass(frozen=True)
class DiscrepancySummary:
    requests: int
    matched_requests: int
    discrepant_requests: int
    groups: tuple[DiscrepancyGroup, ...]


def _near(left: float, right: float) -> bool:
    return abs(left - right) <= TOL + REL * max(abs(left), abs(right))


def _classify(row: RequestLog, calculation, diff: CostDifference) -> str:
    if abs(row.recorded.total) <= TOL and calculation.total > TOL:
        return ZERO_TOTAL
    if abs(row.recorded.total - row.recorded.components_sum) > TOL:
        return TOTAL_NOT_SUM

    calculated = {line.code: line.amount for line in calculation.lines}
    recorded = {code: getattr(row.recorded, attr) for code, attr in RECORDED_ATTR.items()}
    deltas = {code: getattr(diff, attr) for code, attr in DIFF_ATTR.items()}
    nonzero = {code for code, value in deltas.items() if abs(value) > TOL}
    if not nonzero:
        return MATCH

    if nonzero == {"reasoning"}:
        reasoning = calculated.get("reasoning", 0.0)
        if reasoning > TOL and _near(recorded["reasoning"], 2.0 * reasoning):
            return REASONING_DOUBLE

    if calculation.window.tier is PriceTier.PEAK:
        priced = [code for code, value in calculated.items() if abs(value) > TOL]
        if priced and all(_near(recorded[code], 0.5 * calculated[code]) for code in priced):
            return OFF_PEAK_IN_PEAK

    return OTHER


def classify_log_row(row: RequestLog, calculation=None, diff: CostDifference | None = None) -> str:
    """Public classifier used by the writer and the summary."""
    calculation = calculation or calculate_log_row(row)
    diff = diff or difference(calculation, row.recorded)
    return _classify(row, calculation, diff)


@lru_cache(maxsize=1)
def summarize() -> DiscrepancySummary:
    buckets: dict[str, list[tuple[RequestLog, object, CostDifference]]] = defaultdict(list)
    rows = load_logs_by_row().values()
    for row in rows:
        calculation = calculate_log_row(row)
        diff = difference(calculation, row.recorded)
        buckets[_classify(row, calculation, diff)].append((row, calculation, diff))

    groups: list[DiscrepancyGroup] = []
    for code in ORDER:
        items = buckets.get(code, [])
        groups.append(
            DiscrepancyGroup(
                code=code,
                title=TITLES[code],
                requests=len(items),
                recorded_total=sum(row.recorded.total for row, _, _ in items),
                calculated_total=sum(calc.total for _, calc, _ in items),
                difference_total=sum(diff.total for _, _, diff in items),
                sample_request_ids=tuple(row.request_id for row, _, _ in items[:5]),
            )
        )

    matched = len(buckets.get(MATCH, []))
    total = sum(group.requests for group in groups)
    return DiscrepancySummary(
        requests=total,
        matched_requests=matched,
        discrepant_requests=total - matched,
        groups=tuple(groups),
    )
