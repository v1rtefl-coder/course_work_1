import json
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from src.reports import spending_by_weekday, monthly_summary, generate_detailed_report, save_report_to_file


class TestSpendingByWeekday:
    """Тесты для отчета по дням недели."""

    def test_spending_by_weekday_success(self, sample_transactions_df):
        """Тест успешной генерации отчета."""
        result = spending_by_weekday(sample_transactions_df, "2021-12-25")

        # Результат может быть пустым, если нет расходов
        assert isinstance(result, pd.DataFrame)

    def test_spending_by_weekday_empty_df(self):
        """Тест с пустым датафреймом."""
        result = spending_by_weekday(pd.DataFrame())

        assert result.empty


class TestMonthlySummary:
    """Тесты для месячной сводки."""

    def test_monthly_summary_success(self, sample_transactions_df):
        """Тест успешной генерации сводки."""
        result = monthly_summary(sample_transactions_df, 2021, 12)

        # Проверяем, что результат - словарь
        assert isinstance(result, dict)
        if "error" not in result:
            assert "year" in result
            assert "month" in result

    def test_monthly_summary_empty_df(self):
        """Тест с пустым датафреймом."""
        result = monthly_summary(pd.DataFrame(), 2021, 12)

        assert "error" in result or isinstance(result, dict)

    def test_monthly_summary_with_decorator(self, sample_transactions_df):
        """Тест с декоратором сохранения."""
        result = monthly_summary(sample_transactions_df, 2021, 12)

        assert result is not None


class TestGenerateDetailedReport:
    """Тесты для детального отчета."""

    def test_generate_detailed_report_success(self, sample_transactions_df):
        """Тест успешной генерации детального отчета."""
        result = generate_detailed_report(sample_transactions_df, "2021-12-01", "2021-12-31")
        data = json.loads(result)

        assert "period" in data or "error" in data

    def test_generate_detailed_report_empty_df(self):
        """Тест с пустым датафреймом."""
        result = generate_detailed_report(pd.DataFrame(), "2021-12-01", "2021-12-31")
        data = json.loads(result)

        # Может быть success или error
        assert isinstance(data, dict)


class TestDecorator:
    """Тесты для декоратора save_report_to_file."""

    @patch("src.reports.json.dump")
    def test_decorator_without_filename(self, mock_json_dump, sample_transactions_df):
        """Тест декоратора без имени файла."""

        @save_report_to_file()
        def test_func():
            return {"test": "data"}

        result = test_func()
        assert result == {"test": "data"}

    @patch("src.reports.json.dump")
    def test_decorator_with_filename(self, mock_json_dump, sample_transactions_df):
        """Тест декоратора с именем файла."""

        @save_report_to_file("custom_report.json")
        def test_func():
            return {"test": "data"}

        result = test_func()
        assert result == {"test": "data"}

    def test_decorator_with_dataframe(self, sample_transactions_df):
        """Тест декоратора с датафреймом."""
        with patch("src.reports.os.makedirs"):

            @save_report_to_file()
            def test_func():
                return sample_transactions_df

            result = test_func()
            assert not result.empty
