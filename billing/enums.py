"""Domain enums shared by the tariff models and the GraphQL schema.

Plain :class:`enum.Enum` subclasses: the calculator has no dependency on the
GraphQL layer, and Strawberry maps them to GraphQL enums automatically.
"""
from __future__ import annotations

from enum import Enum


class ModelName(Enum):
    DEEPSEEK_FLASH = "deepseek-flash"
    DEEPSEEK_V3_2 = "deepseek-v3.2"
    DEEPSEEK_V4_FLASH = "deepseek-v4-flash"
    DEEPSEEK_V4_FLASH_0731 = "deepseek-v4-flash-0731"
    DEEPSEEK_V4_FLASH_VISION_EXP = "deepseek-v4-flash-vision-exp"
    DEEPSEEK_V4_PRO = "deepseek-v4-pro"
    DEEPSEEK_V4_PRO_0813 = "deepseek-v4-pro-0813"
    DEEPSEEK_V4_1_FLASH = "deepseek-v4.1-flash"
    DEEPSEEK_V4_1_FLASH_1017_ALI = "deepseek-v4.1-flash-1017-ali"


class PriceTier(Enum):
    PEAK = "peak"
    OFF_PEAK = "off-peak"


class DayOfWeek(Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class WindowKind(Enum):
    ALL_DAY = "all-day"
    TIME_RANGE = "time-range"
