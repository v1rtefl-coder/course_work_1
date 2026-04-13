import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, Mock, mock_open

from src.utils import (
    load_transactions,
    filter_transactions_by_date_range,
    get_greeting,
    get_card_spending,
    get_cashback,
    get_top_transactions,
    load_user_settings,
    load_exchange_rates,
    load_stock_prices,
)


class TestLoadTransactions:
    """Тесты загрузки транзакций."""

    @patch("pandas.read_excel")
    def test_load_transactions_success(self, mock_read_excel, sample_transactions_df):
        """Тест успешной загрузки."""
        mock_read_excel.return_value = sample_transactions_df

        result = load_transactions("test.xlsx")

        assert not result.empty
        assert len(result) == 6

    @patch("pandas.read_excel")
    def test_load_transactions_file_not_found(self, mock_read_excel):
        """Тест при отсутствии файла."""
        mock_read_excel.side_effect = FileNotFoundError()

        result = load_transactions("nonexistent.xlsx")

        assert result.empty

    @patch("pandas.read_excel")
    def test_load_transactions_error(self, mock_read_excel):
        """Тест при ошибке чтения."""
        mock_read_excel.side_effect = Exception("Read error")

        result = load_transactions("test.xlsx")

        assert result.empty


class TestFilterTransactions:
    """Тесты фильтрации транзакций."""

    def test_filter_by_date_range(self, sample_transactions_df):
        """Тест фильтрации по диапазону дат."""
        end_date = datetime(2021, 12, 15)
        result = filter_transactions_by_date_range(sample_transactions_df, end_date)

        # Должны остаться транзакции с 1 по 15 декабря
        assert len(result) >= 1

    def test_filter_with_start_date(self, sample_transactions_df):
        """Тест фильтрации с начальной датой."""
        end_date = datetime(2021, 12, 25)
        start_date = datetime(2021, 12, 10)
        result = filter_transactions_by_date_range(sample_transactions_df, end_date, start_date)

        assert len(result) >= 1

    def test_filter_empty_df(self):
        """Тест фильтрации пустого датафрейма."""
        result = filter_transactions_by_date_range(pd.DataFrame(), datetime.now())

        assert result.empty


class TestGetGreeting:
    """Тесты приветствий."""

    @pytest.mark.parametrize(
        "hour,expected",
        [
            (5, "Доброе утро"),
            (8, "Доброе утро"),
            (11, "Доброе утро"),
            (12, "Добрый день"),
            (15, "Добрый день"),
            (17, "Добрый день"),
            (18, "Добрый вечер"),
            (20, "Добрый вечер"),
            (22, "Добрый вечер"),
            (23, "Доброй ночи"),
            (0, "Доброй ночи"),
            (3, "Доброй ночи"),
        ],
    )
    def test_greeting_by_hour(self, hour, expected):
        """Параметризованный тест приветствий."""
        current_time = datetime(2021, 12, 25, hour)
        assert get_greeting(current_time) == expected


class TestGetCardSpending:
    """Тесты расходов по картам."""

    def test_get_card_spending_success(self, sample_transactions_df):
        """Тест расчета расходов по картам."""
        result = get_card_spending(sample_transactions_df)

        assert len(result) >= 1
        if len(result) > 0:
            assert "last_digits" in result[0]
            assert "total_spent" in result[0]
            assert "cashback" in result[0]

    def test_get_card_spending_empty_df(self):
        """Тест с пустым датафреймом."""
        result = get_card_spending(pd.DataFrame())

        assert result == []


class TestGetCashback:
    """Тесты расчета кешбэка."""

    def test_get_cashback_success(self, sample_transactions_df):
        """Тест расчета кешбэка."""
        result = get_cashback(sample_transactions_df)

        assert result >= 0

    def test_get_cashback_empty_df(self):
        """Тест с пустым датафреймом."""
        result = get_cashback(pd.DataFrame())

        assert result == 0.0


class TestGetTopTransactions:
    """Тесты топ транзакций."""

    def test_get_top_5_transactions(self, sample_transactions_df):
        """Тест получения топ-5 транзакций."""
        result = get_top_transactions(sample_transactions_df, 5)

        assert len(result) >= 1

    def test_get_top_empty_df(self):
        """Тест с пустым датафреймом."""
        result = get_top_transactions(pd.DataFrame())

        assert result == []


class TestLoadUserSettings:
    """Тесты загрузки настроек пользователя."""

    @patch("builtins.open", mock_open(read_data='{"user_currencies": ["USD"], "user_stocks": ["AAPL"]}'))
    def test_load_settings_success(self):
        """Тест успешной загрузки настроек."""
        result = load_user_settings("test.json")

        assert "user_currencies" in result
        assert "user_stocks" in result

    def test_load_settings_file_not_found(self):
        """Тест при отсутствии файла."""
        result = load_user_settings("nonexistent.json")

        assert "user_currencies" in result
        assert "user_stocks" in result


class TestLoadExchangeRates:
    """Тесты загрузки курсов валют."""

    @patch("requests.get")
    def test_load_exchange_rates_success(self, mock_get):
        """Тест успешной загрузки курсов."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rates": {"USD": 1.0, "EUR": 0.92, "RUB": 90.0}}
        mock_get.return_value = mock_response

        result = load_exchange_rates(["USD", "EUR"])

        assert "USD" in result
        assert "EUR" in result

    @patch("requests.get")
    def test_load_exchange_rates_api_error(self, mock_get):
        """Тест при ошибке API."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = load_exchange_rates(["USD", "EUR"])

        # Должны быть fallback значения
        assert "USD" in result


class TestLoadStockPrices:
    """Тесты загрузки цен акций."""

    @patch("requests.get")
    def test_load_stock_prices_success(self, mock_get):
        """Тест успешной загрузки цен акций."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Global Quote": {"05. price": "150.50"}}
        mock_get.return_value = mock_response

        result = load_stock_prices(["AAPL"])

        assert "AAPL" in result

    @patch("requests.get")
    def test_load_stock_prices_exception(self, mock_get):
        """Тест при исключении."""
        mock_get.side_effect = Exception("Network error")

        result = load_stock_prices(["AAPL"])

        assert "AAPL" in result
