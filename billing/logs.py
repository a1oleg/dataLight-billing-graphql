"""Access to the raw log rows from the workbook, indexed by request id."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .enums import ModelName
from .formulas import Usage

DATA_XLSX = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "DeepSeek_peak_offpeak_октябрь_2026_Тест.xlsx"
)


@dataclass(frozen=True)
class RecordedCost:
    input: float = 0.0
    cached_input: float = 0.0
    output: float = 0.0
    reasoning: float = 0.0
    prediction: float = 0.0
    image: float = 0.0
    cache_creation: float = 0.0
    web_search: float = 0.0
    total: float = 0.0

    @property
    def components_sum(self) -> float:
        return (
            self.input
            + self.cached_input
            + self.output
            + self.reasoning
            + self.prediction
            + self.image
            + self.cache_creation
            + self.web_search
        )


@dataclass(frozen=True)
class RequestLog:
    request_id: str
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
    usage: Usage
    recorded: RecordedCost
    row_number: int  # Excel sheet row (the first data row is 5)


def _int(value) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _float(value) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _start_time(value) -> datetime:
    if isinstance(value, datetime):
        moment = value
    else:
        text = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                moment = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"bad start_time: {value!r}")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


@lru_cache(maxsize=1)
def load_logs(path: str | None = None) -> dict[str, RequestLog]:
    import pandas as pd

    frame = pd.read_excel(path or DATA_XLSX, sheet_name="Сырые логи", header=3)
    frame.columns = [str(column).strip() for column in frame.columns]
    frame = frame.rename(columns={"Клиент": "client"})

    rows: dict[str, RequestLog] = {}
    for data_index, record in enumerate(frame.itertuples(index=False), start=1):
        model_group = str(record.model_group).strip()
        try:
            model_name: ModelName | None = ModelName(model_group)
        except ValueError:
            model_name = None
        usage = Usage(
            prompt_tokens=_int(record.prompt_tokens),
            completion_tokens=_int(record.completion_tokens),
            cached_input_tokens=_int(record.cached_input_tokens),
            cache_creation_tokens=_int(record.cache_creation_tokens),
            reasoning_tokens=_int(record.reasoning_tokens),
            accepted_prediction_tokens=_int(record.accepted_prediction_tokens),
            rejected_prediction_tokens=_int(record.rejected_prediction_tokens),
            image_tokens=_int(record.image_tokens),
            output_image_tokens=_int(record.output_image_tokens),
            audio_input_tokens=_int(record.audio_input_tokens),
            audio_output_tokens=_int(record.audio_output_tokens),
            total_tokens=_int(record.total_tokens),
        )
        recorded = RecordedCost(
            input=_float(record.input_cost),
            cached_input=_float(record.cached_input_cost),
            output=_float(record.output_cost),
            reasoning=_float(record.reasoning_cost),
            prediction=_float(record.prediction_cost),
            image=_float(record.image_cost),
            cache_creation=_float(record.cache_creation_cost),
            web_search=_float(record.web_search_cost),
            total=_float(record.total_cost),
        )
        request_id = str(record.request_id).strip()
        rows[request_id] = RequestLog(
            request_id=request_id,
            start_time=_start_time(record[0]),
            organization_id=str(record.organization_id).strip(),
            client=str(record.client).strip(),
            model_group=model_group,
            model=str(record.model).strip(),
            real_model=str(record.real_model).strip(),
            call_type=str(record.call_type).strip(),
            status=str(record.status).strip(),
            http_status=_int(record.http_status),
            model_name=model_name,
            usage=usage,
            recorded=recorded,
            row_number=data_index + 4,  # header is row 4, the first data row is 5
        )
    return rows


@lru_cache(maxsize=1)
def load_logs_by_row() -> dict[int, RequestLog]:
    """Map Excel sheet row number -> log row."""
    return {row.row_number: row for row in load_logs().values()}
