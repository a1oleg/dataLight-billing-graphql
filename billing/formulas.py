"""Reusable cost formulas: one implementation for every model and window."""
from __future__ import annotations

from dataclasses import dataclass

from .tariffs import TariffWindow

TOKEN_UNIT = 1_000_000


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_input_tokens: int = 0
    cache_creation_tokens: int = 0
    reasoning_tokens: int = 0
    accepted_prediction_tokens: int = 0
    rejected_prediction_tokens: int = 0
    image_tokens: int = 0
    output_image_tokens: int = 0
    audio_input_tokens: int = 0
    audio_output_tokens: int = 0
    total_tokens: int = 0

    @property
    def text_tokens(self) -> int:
        """completion - reasoning - audio - image - output_image."""
        return (
            self.completion_tokens
            - self.reasoning_tokens
            - self.audio_input_tokens
            - self.image_tokens
            - self.output_image_tokens
        )


@dataclass(frozen=True)
class CostLine:
    code: str
    label: str
    tokens: int | None
    rate_per_million: float | None
    amount: float


def compute_lines(
    usage: Usage,
    window: TariffWindow,
    cache_creation_cost: float = 0.0,
    web_search_cost: float = 0.0,
) -> list[CostLine]:
    """Turn token usage and one tariff window into itemised cost lines.

    The same function serves every model: only the window's rates change.
    """
    input_rate = window.input_per_million / TOKEN_UNIT
    output_rate = window.output_per_million / TOKEN_UNIT
    cache_rate = window.cache_read_per_million / TOKEN_UNIT

    text_tokens = usage.text_tokens
    input_tokens = usage.prompt_tokens - usage.cached_input_tokens
    prediction_tokens = usage.accepted_prediction_tokens + usage.rejected_prediction_tokens

    return [
        CostLine("input", "input", input_tokens, window.input_per_million, input_tokens * input_rate),
        CostLine(
            "cachedInput",
            "cached input",
            usage.cached_input_tokens,
            window.cache_read_per_million,
            usage.cached_input_tokens * cache_rate,
        ),
        CostLine("output", "output", text_tokens, window.output_per_million, text_tokens * output_rate),
        CostLine(
            "reasoning",
            "reasoning",
            usage.reasoning_tokens,
            window.output_per_million,
            usage.reasoning_tokens * output_rate,
        ),
        CostLine(
            "prediction",
            "prediction",
            prediction_tokens,
            window.output_per_million,
            prediction_tokens * output_rate,
        ),
        CostLine("image", "image", usage.image_tokens, window.input_per_million, usage.image_tokens * input_rate),
        CostLine("cacheCreation", "cache creation", usage.cache_creation_tokens, None, cache_creation_cost),
        CostLine("webSearch", "web search", None, None, web_search_cost),
    ]


def total(lines: list[CostLine]) -> float:
    return sum(line.amount for line in lines)
