"""GraphQL calculator schema: models, their windows and reusable cost formulas."""
from __future__ import annotations

from datetime import datetime

import strawberry

from .calculator import Calculation, LogRow, calculate, calculate_log_row
from .comparison import CostDifference, difference
from .descriptions import apply_descriptions
from .enums import DayOfWeek, ModelName, PriceTier, WindowKind
from .formulas import Usage
from .logs import RecordedCost, RequestLog, load_logs, load_logs_by_row
from .summary import (
    CostTotals,
    DiscrepancyGroup,
    DiscrepancySummary,
    cost_totals as compute_cost_totals,
    summarize,
)
from .tariffs import Model, TariffWindow, load_models
from .writer import WriteResult, write_row


# --------------------------------------------------------------------------
# output types
# --------------------------------------------------------------------------
def _money(value: float) -> float:
    """Round only for display; calculations keep full precision."""
    rounded = round(value, 12)
    return 0.0 if rounded == 0.0 else rounded


@strawberry.type(name="CostComponent")
class CostComponentType:
    code: str
    label: str
    tokens: int | None
    rate_per_million: float | None
    amount: float


@strawberry.type(name="CostLine")
class CostLineType:
    code: str
    label: str
    tokens: int | None
    rate_per_million: float | None
    amount: float


@strawberry.type(name="Usage")
class UsageType:
    prompt_tokens: int
    completion_tokens: int
    cached_input_tokens: int
    cache_creation_tokens: int
    reasoning_tokens: int
    accepted_prediction_tokens: int
    rejected_prediction_tokens: int
    image_tokens: int
    output_image_tokens: int
    audio_input_tokens: int
    audio_output_tokens: int
    total_tokens: int
    text_tokens: int


def usage_type(value: Usage) -> UsageType:
    return UsageType(
        prompt_tokens=value.prompt_tokens,
        completion_tokens=value.completion_tokens,
        cached_input_tokens=value.cached_input_tokens,
        cache_creation_tokens=value.cache_creation_tokens,
        reasoning_tokens=value.reasoning_tokens,
        accepted_prediction_tokens=value.accepted_prediction_tokens,
        rejected_prediction_tokens=value.rejected_prediction_tokens,
        image_tokens=value.image_tokens,
        output_image_tokens=value.output_image_tokens,
        audio_input_tokens=value.audio_input_tokens,
        audio_output_tokens=value.audio_output_tokens,
        total_tokens=value.total_tokens,
        text_tokens=value.text_tokens,
    )


@strawberry.type(name="RecordedCost")
class RecordedCostType:
    input: float
    cached_input: float
    output: float
    reasoning: float
    prediction: float
    image: float
    cache_creation: float
    web_search: float
    total: float
    components_sum: float
    lines: list[CostLineType]

    @strawberry.field
    def components(self, include_zero: bool = False) -> list[CostComponentType]:
        values = [
            ("input", "input", self.input),
            ("cachedInput", "cached input", self.cached_input),
            ("output", "output", self.output),
            ("reasoning", "reasoning", self.reasoning),
            ("prediction", "prediction", self.prediction),
            ("image", "image", self.image),
            ("cacheCreation", "cache creation", self.cache_creation),
            ("webSearch", "web search", self.web_search),
        ]
        return [
            CostComponentType(
                code=code,
                label=label,
                tokens=None,
                rate_per_million=None,
                amount=_money(amount),
            )
            for code, label, amount in values
            if include_zero or abs(amount) > 1e-12
        ]


def _recorded_lines(value: RecordedCost, usage: Usage | None) -> list[CostLineType]:
    tokens: dict[str, int | None] = {
        "input": None,
        "cachedInput": None,
        "output": None,
        "reasoning": None,
        "prediction": None,
        "image": None,
        "cacheCreation": None,
        "webSearch": None,
    }
    if usage is not None:
        tokens.update(
            {
                "input": usage.prompt_tokens - usage.cached_input_tokens,
                "cachedInput": usage.cached_input_tokens,
                "output": usage.text_tokens,
                "reasoning": usage.reasoning_tokens,
                "prediction": usage.accepted_prediction_tokens + usage.rejected_prediction_tokens,
                "image": usage.image_tokens,
                "cacheCreation": usage.cache_creation_tokens,
            }
        )
    values = [
        ("input", "input", value.input),
        ("cachedInput", "cached input", value.cached_input),
        ("output", "output", value.output),
        ("reasoning", "reasoning", value.reasoning),
        ("prediction", "prediction", value.prediction),
        ("image", "image", value.image),
        ("cacheCreation", "cache creation", value.cache_creation),
        ("webSearch", "web search", value.web_search),
    ]
    return [
        CostLineType(
            code=code,
            label=label,
            tokens=tokens[code],
            rate_per_million=(
                _money(amount / tokens[code] * 1_000_000) if tokens[code] else None
            ),
            amount=_money(amount),
        )
        for code, label, amount in values
    ]


def recorded_cost_type(value: RecordedCost, usage: Usage | None = None) -> RecordedCostType:
    return RecordedCostType(
        input=_money(value.input),
        cached_input=_money(value.cached_input),
        output=_money(value.output),
        reasoning=_money(value.reasoning),
        prediction=_money(value.prediction),
        image=_money(value.image),
        cache_creation=_money(value.cache_creation),
        web_search=_money(value.web_search),
        total=_money(value.total),
        components_sum=_money(value.components_sum),
        lines=_recorded_lines(value, usage),
    )


@strawberry.type(name="CostDifference")
class CostDifferenceType:
    input: float
    cached_input: float
    output: float
    reasoning: float
    prediction: float
    image: float
    cache_creation: float
    web_search: float
    total: float

    @strawberry.field
    def components(self, include_zero: bool = False) -> list[CostComponentType]:
        values = [
            ("input", "input", self.input),
            ("cachedInput", "cached input", self.cached_input),
            ("output", "output", self.output),
            ("reasoning", "reasoning", self.reasoning),
            ("prediction", "prediction", self.prediction),
            ("image", "image", self.image),
            ("cacheCreation", "cache creation", self.cache_creation),
            ("webSearch", "web search", self.web_search),
        ]
        return [
            CostComponentType(
                code=code,
                label=label,
                tokens=None,
                rate_per_million=None,
                amount=_money(amount),
            )
            for code, label, amount in values
            if include_zero or abs(amount) > 1e-12
        ]


def cost_difference_type(value: CostDifference) -> CostDifferenceType:
    return CostDifferenceType(
        input=_money(value.input),
        cached_input=_money(value.cached_input),
        output=_money(value.output),
        reasoning=_money(value.reasoning),
        prediction=_money(value.prediction),
        image=_money(value.image),
        cache_creation=_money(value.cache_creation),
        web_search=_money(value.web_search),
        total=_money(value.total),
    )


@strawberry.type(name="TariffWindow")
class TariffWindowType:
    domain: strawberry.Private[TariffWindow]

    @strawberry.field
    def label(self) -> str:
        return self.domain.label

    @strawberry.field
    def kind(self) -> WindowKind:
        return self.domain.kind

    @strawberry.field
    def days(self) -> list[DayOfWeek]:
        return list(self.domain.days)

    @strawberry.field
    def start_hour(self) -> int:
        return self.domain.start_hour

    @strawberry.field
    def end_hour(self) -> int:
        return self.domain.end_hour

    @strawberry.field
    def tier(self) -> PriceTier:
        return self.domain.tier

    @strawberry.field
    def input_per_million(self) -> float:
        return self.domain.input_per_million

    @strawberry.field
    def output_per_million(self) -> float:
        return self.domain.output_per_million

    @strawberry.field
    def cache_read_per_million(self) -> float:
        return self.domain.cache_read_per_million

    @strawberry.field
    def rate(self) -> float:
        return self.domain.rate

    @strawberry.field
    def search_context_cost_per_query(self) -> float | None:
        return self.domain.search_context_cost_per_query

    @strawberry.field
    def covers(self, at: datetime) -> bool:
        return self.domain.covers(at)


@strawberry.type(name="Model")
class ModelType:
    domain: strawberry.Private[Model]

    @strawberry.field
    def name(self) -> ModelName:
        return self.domain.name

    @strawberry.field
    def slug(self) -> str:
        return self.domain.slug

    @strawberry.field
    def price_list(self) -> str:
        return self.domain.price_list

    @strawberry.field
    def windows(self) -> list[TariffWindowType]:
        return [TariffWindowType(domain=window) for window in self.domain.windows]

    @strawberry.field
    def window_at(self, at: datetime) -> TariffWindowType | None:
        window = self.domain.window_at(at)
        return TariffWindowType(domain=window) if window else None


@strawberry.type(name="Calculation")
class CalculationType:
    request_id: str | None
    model: ModelType
    window: TariffWindowType
    usage: UsageType
    text_tokens: int
    lines: list[CostLineType]
    total: float

    @strawberry.field
    def components(self, include_zero: bool = False) -> list[CostComponentType]:
        return [
            CostComponentType(
                code=line.code,
                label=line.label,
                tokens=line.tokens,
                rate_per_million=line.rate_per_million,
                amount=line.amount,
            )
            for line in self.lines
            if include_zero or abs(line.amount) > 1e-12
        ]


def calculation_type(value: Calculation) -> CalculationType:
    return CalculationType(
        request_id=value.request_id,
        model=ModelType(domain=value.model),
        window=TariffWindowType(domain=value.window),
        usage=usage_type(value.usage),
        text_tokens=value.usage.text_tokens,
        lines=[
            CostLineType(
                code=line.code,
                label=line.label,
                tokens=line.tokens,
                rate_per_million=line.rate_per_million,
                amount=_money(line.amount),
            )
            for line in value.lines
        ],
        total=_money(value.total),
    )


@strawberry.type(name="LogRow")
class LogRowType:
    request_id: strawberry.ID
    start_time: datetime
    organization_id: str
    client: str
    model_group: str
    model: str
    real_model: str
    call_type: str
    status: str
    http_status: int
    model_name: ModelName | None
    usage: UsageType
    recorded: RecordedCostType
    row_number: int
    calculated: CalculationType
    difference: CostDifferenceType


def log_row_type(
    value: RequestLog,
    calculation: Calculation | None = None,
    diff: CostDifference | None = None,
) -> LogRowType:
    if calculation is None:
        calculation = calculate_log_row(value)
    if diff is None:
        diff = difference(calculation, value.recorded)
    return LogRowType(
        request_id=value.request_id,
        start_time=value.start_time,
        organization_id=value.organization_id,
        client=value.client,
        model_group=value.model_group,
        model=value.model,
        real_model=value.real_model,
        call_type=value.call_type,
        status=value.status,
        http_status=value.http_status,
        model_name=value.model_name,
        usage=usage_type(value.usage),
        recorded=recorded_cost_type(value.recorded, value.usage),
        row_number=value.row_number,
        calculated=calculation_type(calculation),
        difference=cost_difference_type(diff),
    )


@strawberry.type(name="WriteResult")
class WriteResultType:
    workbook: str
    calculated_written: bool
    difference_written: bool
    reason_written: bool


def write_result_type(value: WriteResult) -> WriteResultType:
    return WriteResultType(
        workbook=value.workbook,
        calculated_written=value.calculated_written,
        difference_written=value.difference_written,
        reason_written=value.reason_written,
    )


@strawberry.type(name="DiscrepancyGroup")
class DiscrepancyGroupType:
    code: str
    title: str
    requests: int
    recorded_total: float
    calculated_total: float
    difference_total: float
    sample_request_ids: list[str]

    @strawberry.field
    def recorded(self) -> float:
        return self.recorded_total

    @strawberry.field
    def calculated(self) -> float:
        return self.calculated_total

    @strawberry.field
    def difference(self) -> float:
        return self.difference_total


def discrepancy_group_type(value: DiscrepancyGroup) -> DiscrepancyGroupType:
    return DiscrepancyGroupType(
        code=value.code,
        title=value.title,
        requests=value.requests,
        recorded_total=_money(value.recorded_total),
        calculated_total=_money(value.calculated_total),
        difference_total=_money(value.difference_total),
        sample_request_ids=list(value.sample_request_ids),
    )


@strawberry.type(name="DiscrepancySummary")
class DiscrepancySummaryType:
    requests: int
    matched_requests: int
    discrepant_requests: int
    groups: list[DiscrepancyGroupType]


def discrepancy_summary_type(value: DiscrepancySummary) -> DiscrepancySummaryType:
    return DiscrepancySummaryType(
        requests=value.requests,
        matched_requests=value.matched_requests,
        discrepant_requests=value.discrepant_requests,
        groups=[discrepancy_group_type(group) for group in value.groups],
    )


@strawberry.type(name="CostTotals")
class CostTotalsType:
    requests: int
    recorded_total: float
    calculated_total: float
    difference_total: float


def cost_totals_type(value: CostTotals) -> CostTotalsType:
    return CostTotalsType(
        requests=value.requests,
        recorded_total=_money(value.recorded_total),
        calculated_total=_money(value.calculated_total),
        difference_total=_money(value.difference_total),
    )


# --------------------------------------------------------------------------
# row-level calculation
# --------------------------------------------------------------------------
@strawberry.type(name="RowCalculation")
class RowCalculationType:
    row: LogRowType
    recorded: RecordedCostType
    calculated: CalculationType
    difference: CostDifferenceType
    written: WriteResultType | None


def find_log_row(request_id: str | None, row_number: int | None) -> RequestLog | None:
    if request_id is not None:
        return load_logs().get(request_id)
    if row_number is not None:
        return load_logs_by_row().get(row_number)
    return None


# --------------------------------------------------------------------------
# input types
# --------------------------------------------------------------------------
@strawberry.input
class UsageInput:
    prompt_tokens: int
    completion_tokens: int
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


@strawberry.input
class LogRowInput:
    start_time: datetime
    model: ModelName
    usage: UsageInput
    request_id: str | None = None
    organization_id: str | None = None
    status: str | None = None
    cache_creation_cost: float = 0.0
    web_search_cost: float = 0.0


def usage_from_input(value: UsageInput) -> Usage:
    return Usage(
        prompt_tokens=value.prompt_tokens,
        completion_tokens=value.completion_tokens,
        cached_input_tokens=value.cached_input_tokens,
        cache_creation_tokens=value.cache_creation_tokens,
        reasoning_tokens=value.reasoning_tokens,
        accepted_prediction_tokens=value.accepted_prediction_tokens,
        rejected_prediction_tokens=value.rejected_prediction_tokens,
        image_tokens=value.image_tokens,
        output_image_tokens=value.output_image_tokens,
        audio_input_tokens=value.audio_input_tokens,
        audio_output_tokens=value.audio_output_tokens,
        total_tokens=value.total_tokens,
    )


# --------------------------------------------------------------------------
# query
# --------------------------------------------------------------------------
@strawberry.type
class Query:
    @strawberry.field
    def models(self) -> list[ModelType]:
        return [ModelType(domain=model) for model in load_models().values()]

    @strawberry.field
    def model(self, name: ModelName) -> ModelType | None:
        model = load_models().get(name)
        return ModelType(domain=model) if model else None

    @strawberry.field
    def discrepancy_summary(self) -> DiscrepancySummaryType:
        """Count rows by discrepancy group (match / reasoning / peak / zero / other)."""
        return discrepancy_summary_type(summarize())

    @strawberry.field
    def cost_totals(self) -> CostTotalsType:
        """Total recorded, recalculated and difference costs over the whole table."""
        return cost_totals_type(compute_cost_totals())

    @strawberry.field
    def log_row(
        self,
        request_id: strawberry.ID | None = None,
        row_number: int | None = None,
    ) -> LogRowType | None:
        """Look a row up by request id or by Excel sheet row number.

        ``requestId`` wins when both arguments are passed; ``rowNumber`` is the
        row as seen in the worksheet (the first data row is 5, the last 30984).
        """
        row = find_log_row(str(request_id) if request_id is not None else None, row_number)
        return log_row_type(row) if row else None

    @strawberry.field
    def calculate_row(
        self,
        request_id: strawberry.ID | None = None,
        row_number: int | None = None,
        write_calculated: bool = False,
        write_difference: bool = False,
        write_reason: bool = False,
    ) -> RowCalculationType | None:
        """Calculate a log row, show the difference, optionally write the groups."""
        row = find_log_row(str(request_id) if request_id is not None else None, row_number)
        if row is None:
            return None
        calculation = calculate_log_row(row)
        diff = difference(calculation, row.recorded)
        written = write_row(
            row, calculation, diff, write_calculated, write_difference, write_reason
        )
        return RowCalculationType(
            row=log_row_type(row, calculation, diff),
            calculated=calculation_type(calculation),
            recorded=recorded_cost_type(row.recorded, row.usage),
            difference=cost_difference_type(diff),
            written=write_result_type(written) if written else None,
        )

    @strawberry.field
    def calculate(self, row: LogRowInput) -> CalculationType:
        domain_row = LogRow(
            start_time=row.start_time,
            model=row.model,
            usage=usage_from_input(row.usage),
            request_id=row.request_id,
            organization_id=row.organization_id,
            status=row.status,
            cache_creation_cost=row.cache_creation_cost,
            web_search_cost=row.web_search_cost,
        )
        return calculation_type(calculate(domain_row))


schema = strawberry.Schema(query=Query)
apply_descriptions(schema)
