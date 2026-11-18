"""Tariff catalogue: models, their windows and rates.

The price CSV stores every ``$/1M`` value multiplied by 10 000 and formatted
with thousands separators (``"1,950"`` == ``0.195``), while ``rate`` and
``search_context_cost_per_query`` use a decimal comma.  :func:`load_models`
normalises everything to plain USD per 1M tokens.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .enums import DayOfWeek, ModelName, PriceTier, WindowKind

PRICES_CSV = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
PRICE_SCALE = 10_000.0
WINDOW_RE = re.compile(r"^[tw](\d{2})-(\d{2})$")

DAY_INDEX = {
    DayOfWeek.MON: 0,
    DayOfWeek.TUE: 1,
    DayOfWeek.WED: 2,
    DayOfWeek.THU: 3,
    DayOfWeek.FRI: 4,
    DayOfWeek.SAT: 5,
    DayOfWeek.SUN: 6,
}


def ensure_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


@dataclass(frozen=True)
class TariffWindow:
    label: str
    kind: WindowKind
    days: tuple[DayOfWeek, ...]
    start_hour: int
    end_hour: int
    tier: PriceTier
    input_per_million: float
    output_per_million: float
    cache_read_per_million: float
    rate: float
    search_context_cost_per_query: float | None = None

    def covers(self, moment: datetime) -> bool:
        moment = ensure_utc(moment)
        if moment.weekday() not in {DAY_INDEX[day] for day in self.days}:
            return False
        if self.kind is WindowKind.ALL_DAY:
            return True
        minutes = moment.hour * 60 + moment.minute
        return self.start_hour * 60 <= minutes < self.end_hour * 60


@dataclass(frozen=True)
class Model:
    name: ModelName
    slug: str
    price_list: str
    windows: tuple[TariffWindow, ...]

    def window_at(self, moment: datetime) -> TariffWindow | None:
        for window in self.windows:
            if window.covers(moment):
                return window
        return None


def _price(raw: str) -> float:
    cleaned = raw.strip().replace(" ", "").replace(",", "")
    if not cleaned:
        raise ValueError("empty price")
    return float(cleaned) / PRICE_SCALE


def _decimal(raw: str) -> float:
    return float(raw.strip().replace(",", "."))


def _days(raw: str) -> tuple[DayOfWeek, ...]:
    text = raw.strip().lower()
    if text.startswith("ежедневно"):
        return tuple(DayOfWeek)
    parts = [part for part in re.split(r"[,\s]+", text) if part]
    return tuple(DayOfWeek(part) for part in parts)


def _window(raw: str) -> tuple[WindowKind, int, int]:
    text = raw.strip().lower()
    if "одна цена" in text:
        return WindowKind.ALL_DAY, 0, 24
    match = WINDOW_RE.match(text)
    if not match:
        raise ValueError(f"unknown window: {raw!r}")
    start, end = int(match.group(1)), int(match.group(2))
    if not 0 <= start < end <= 24:
        raise ValueError(f"bad window: {raw!r}")
    return WindowKind.TIME_RANGE, start, end


@lru_cache(maxsize=4)
def load_models(path: str | None = None) -> dict[ModelName, Model]:
    csv_path = Path(path) if path else PRICES_CSV
    windows: dict[str, list[TariffWindow]] = {}
    price_lists: dict[str, str] = {}
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            slug = row["Модель"].strip()
            if not slug:
                continue
            kind, start, end = _window(row["Окно (UTC)"])
            search_raw = (row.get("search_context_cost_per_query, $") or "").strip()
            window = TariffWindow(
                label=row["Окно (UTC)"].strip(),
                kind=kind,
                days=_days(row["Дни"]),
                start_hour=start,
                end_hour=end,
                tier=PriceTier(row["Peak или off-peak"].strip().lower()),
                input_per_million=_price(row["Input $/1M"]),
                output_per_million=_price(row["Output $/1M"]),
                cache_read_per_million=_price(row["Cache read $/1M"]),
                rate=_decimal(row["rate"]),
                search_context_cost_per_query=_decimal(search_raw) if search_raw else None,
            )
            windows.setdefault(slug, []).append(window)
            price_lists[slug] = row["Прайс-лист"].strip()
    return {
        ModelName(slug): Model(
            name=ModelName(slug),
            slug=slug,
            price_list=price_lists[slug],
            windows=tuple(items),
        )
        for slug, items in windows.items()
    }
