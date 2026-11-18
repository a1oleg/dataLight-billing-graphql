"""Tests for the price catalogue, window matching and the calculator."""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from billing.calculator import LogRow, calculate  # noqa: E402
from billing.enums import DayOfWeek, ModelName, PriceTier, WindowKind  # noqa: E402
from billing.formulas import Usage  # noqa: E402
from billing.tariffs import load_models  # noqa: E402

UTC = timezone.utc
MONDAY = datetime(2026, 10, 12, tzinfo=UTC)  # Monday


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=UTC)


class TestPriceCatalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.models = load_models()

    def test_all_csv_models_have_enum(self) -> None:
        self.assertEqual(len(self.models), 9)
        self.assertEqual({model.name for model in self.models.values()}, set(ModelName))

    def test_prices_are_normalised_to_usd_per_million(self) -> None:
        flash = self.models[ModelName.DEEPSEEK_FLASH]
        window = flash.window_at(at(13, 0, 30))
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window.label, "t00-01")
        self.assertEqual(window.kind, WindowKind.TIME_RANGE)
        self.assertEqual(window.tier, PriceTier.OFF_PEAK)
        self.assertAlmostEqual(window.input_per_million, 0.195)
        self.assertAlmostEqual(window.output_per_million, 0.78)
        self.assertAlmostEqual(window.cache_read_per_million, 0.0039)
        self.assertAlmostEqual(window.rate, 1.3)

    def test_window_start_is_inclusive_and_end_exclusive(self) -> None:
        flash = self.models[ModelName.DEEPSEEK_FLASH]
        self.assertEqual(flash.window_at(at(13, 5, 59)).label, "t04-06")
        self.assertEqual(flash.window_at(at(13, 6, 0)).label, "t06-10")
        self.assertEqual(flash.window_at(at(13, 9, 59)).label, "t06-10")
        self.assertEqual(flash.window_at(at(13, 10, 0)).label, "t10-14")

    def test_weekend_window(self) -> None:
        flash = self.models[ModelName.DEEPSEEK_FLASH]
        window = flash.window_at(at(17, 7, 0))  # Saturday
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window.label, "w00-24")
        self.assertEqual(window.days, (DayOfWeek.SAT, DayOfWeek.SUN))

    def test_all_day_model(self) -> None:
        model = self.models[ModelName.DEEPSEEK_V4_FLASH]
        window = model.window_at(at(17, 3, 0))  # Saturday night
        self.assertIsNotNone(window)
        assert window is not None
        self.assertEqual(window.kind, WindowKind.ALL_DAY)
        self.assertAlmostEqual(window.input_per_million, 0.25)
        self.assertAlmostEqual(window.output_per_million, 0.5)
        self.assertAlmostEqual(window.cache_read_per_million, 0.0504)

    def test_every_model_covers_the_whole_week(self) -> None:
        for model in self.models.values():
            for day in range(7):
                for hour in range(24):
                    moment = MONDAY.replace(day=MONDAY.day + day, hour=hour, minute=30)
                    self.assertIsNotNone(
                        model.window_at(moment),
                        f"{model.slug} has no window at {moment.isoformat()}",
                    )


class TestFormulas(unittest.TestCase):
    def test_text_tokens_subtracts_non_text_output(self) -> None:
        usage = Usage(
            completion_tokens=100,
            reasoning_tokens=60,
            audio_input_tokens=5,
            image_tokens=3,
            output_image_tokens=2,
        )
        self.assertEqual(usage.text_tokens, 30)

    def test_uploaded_cache_creation_and_web_search_are_added(self) -> None:
        models = load_models()
        row = LogRow(
            start_time=at(13, 0, 30),
            model=ModelName.DEEPSEEK_V4_FLASH,
            usage=Usage(prompt_tokens=1000, completion_tokens=500),
            cache_creation_cost=0.01,
            web_search_cost=0.02,
        )
        result = calculate(row, models)
        self.assertAlmostEqual(result.total, 0.00025 + 0.00025 + 0.03, places=12)
        codes = [line.code for line in result.lines]
        self.assertIn("cacheCreation", codes)
        self.assertIn("webSearch", codes)


class TestCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.models = load_models()

    def test_v4_flash_known_row(self) -> None:
        # 06faa446-23f5-4386-9838-81d847e3405d
        row = LogRow(
            start_time=datetime(2026, 10, 13, 0, 0, 27, 467000, tzinfo=UTC),
            model=ModelName.DEEPSEEK_V4_FLASH,
            usage=Usage(
                prompt_tokens=1020,
                completion_tokens=2621,
                cached_input_tokens=128,
                reasoning_tokens=2030,
                total_tokens=3641,
            ),
        )
        result = calculate(row, self.models)
        self.assertEqual(result.window.label, "(одна цена на все сутки)")
        self.assertEqual(result.usage.text_tokens, 591)
        self.assertAlmostEqual(result.total, 0.0015399512, places=12)

    def test_v4_flash_reasoning_row(self) -> None:
        # 99bd4acd-cf50-415d-b263-fb81683bbef0: reasoning is charged once
        row = LogRow(
            start_time=datetime(2026, 10, 13, 0, 0, 35, 755000, tzinfo=UTC),
            model=ModelName.DEEPSEEK_V4_FLASH,
            usage=Usage(prompt_tokens=1311, completion_tokens=648, reasoning_tokens=626),
        )
        result = calculate(row, self.models)
        self.assertAlmostEqual(result.total, 0.00065175, places=12)

    def test_v4_flash_0731_peak_window(self) -> None:
        # resp_04436d5c-b9ec-92ea-aae4-941c162ea044: t00-01 is peak for this model
        row = LogRow(
            start_time=datetime(2026, 10, 13, 0, 13, 10, 199000, tzinfo=UTC),
            model=ModelName.DEEPSEEK_V4_FLASH_0731,
            usage=Usage(prompt_tokens=75484, completion_tokens=1915),
        )
        result = calculate(row, self.models)
        self.assertEqual(result.window.label, "t00-01")
        self.assertEqual(result.window.tier, PriceTier.PEAK)
        self.assertAlmostEqual(result.total, 0.046462988, places=12)

    def test_deepseek_flash_peak_window(self) -> None:
        row = LogRow(
            start_time=at(13, 7, 0),
            model=ModelName.DEEPSEEK_FLASH,
            usage=Usage(
                prompt_tokens=1000,
                cached_input_tokens=200,
                completion_tokens=500,
                reasoning_tokens=100,
            ),
        )
        result = calculate(row, self.models)
        self.assertEqual(result.window.label, "t06-10")
        self.assertAlmostEqual(result.total, 0.00109356, places=12)


if __name__ == "__main__":
    unittest.main()
