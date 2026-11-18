"""Compare a calculation with the cost recorded in the log row."""
from __future__ import annotations

from dataclasses import dataclass

from .calculator import Calculation
from .logs import RecordedCost


@dataclass(frozen=True)
class CostDifference:
    input: float = 0.0
    cached_input: float = 0.0
    output: float = 0.0
    reasoning: float = 0.0
    prediction: float = 0.0
    image: float = 0.0
    cache_creation: float = 0.0
    web_search: float = 0.0
    total: float = 0.0


def difference(calculation: Calculation, recorded: RecordedCost) -> CostDifference:
    """calculated - recorded, component by component."""
    amounts = {line.code: line.amount for line in calculation.lines}
    return CostDifference(
        input=amounts.get("input", 0.0) - recorded.input,
        cached_input=amounts.get("cachedInput", 0.0) - recorded.cached_input,
        output=amounts.get("output", 0.0) - recorded.output,
        reasoning=amounts.get("reasoning", 0.0) - recorded.reasoning,
        prediction=amounts.get("prediction", 0.0) - recorded.prediction,
        image=amounts.get("image", 0.0) - recorded.image,
        cache_creation=amounts.get("cacheCreation", 0.0) - recorded.cache_creation,
        web_search=amounts.get("webSearch", 0.0) - recorded.web_search,
        total=calculation.total - recorded.total,
    )
