import json
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock


class TestMainPage:
    """Тесты для главной страницы."""

    @patch("src.views.filter_transactions_by_date_range")
    @patch("src.views.load_stock_prices")
    @patch("src.views.load_exchange_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions")
    @patch("src.views.get_top_transactions")
    @patch("src.views.get_cashback")
    @patch("src.views.get_card_spending")
    @patch("src.views.get_greeting")
    def test_main_page_success(
        self,
        mock_greeting,
        mock_card_spending,
        mock_cashback,
        mock_top_transactions,
        mock_load,
        mock_settings,
        mock_rates,
        mock_stocks,
        mock_filter,
    ):
        """Тест успешной генерации главной страницы."""
        # Создаем НЕ пустой датафрейм для фильтрации
        test_df = pd.DataFrame(
            {
                "Дата операции": pd.to_datetime(["2021-12-01"]),
                "Номер карты": [1234556],
                "Статус": ["OK"],
                "Сумма платежа": [-1000],
                "Валюта платежа": ["RUB"],
            }
        )

        # Настройка моков
        mock_greeting.return_value = "Добрый день"
        mock_card_spending.return_value = [{"last_digits": "4556", "total_spent": 1000.0, "cashback": 10.0}]
        mock_cashback.return_value = 10.0
        mock_top_transactions.return_value = [
            {"date": "2021-12-01", "amount": 1000, "currency": "RUB", "description": "Test", "category": "Test"}
        ]
        mock_load.return_value = test_df  # Возвращаем тестовый датафрейм
        mock_filter.return_value = test_df  # Фильтр возвращает НЕ пустой датафрейм
        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = {"USD": 1.0}
        mock_stocks.return_value = {"AAPL": 150.0}

        from src.views import main_page

        result = main_page("2021-12-25 14:30:00")
        data = json.loads(result)

        # Проверяем структуру ответа
        assert "greeting" in data
        assert "cards" in data
        assert "total_cashback" in data
        assert "top_transactions" in data
        assert "exchange_rates" in data
        assert "stock_prices" in data
        assert "period" in data

        # Проверяем значения
        assert data["greeting"] == "Добрый день"
        assert data["total_cashback"] == 10.0
        assert len(data["cards"]) == 1
        assert len(data["top_transactions"]) == 1

    @patch("src.views.load_transactions")
    def test_main_page_invalid_date_format(self, mock_load):
        """Тест с неверным форматом даты."""
        mock_load.return_value = pd.DataFrame()

        from src.views import main_page

        result = main_page("invalid-date")
        data = json.loads(result)

        assert "error" in data

    @patch("src.views.load_transactions")
    def test_main_page_empty_data(self, mock_load):
        """Тест с пустыми данными."""
        mock_load.return_value = pd.DataFrame()

        from src.views import main_page

        result = main_page("2021-12-25 14:30:00")
        data = json.loads(result)

        assert "error" in data

    @patch("src.views.load_transactions")
    def test_main_page_with_error(self, mock_load):
        """Тест с ошибкой при загрузке данных."""
        mock_load.side_effect = Exception("Test error")

        from src.views import main_page

        result = main_page("2021-12-25 14:30:00")
        data = json.loads(result)

        assert "error" in data

    def test_main_page_greeting_morning(self):
        """Тест приветствия для утра."""
        from src.utils import get_greeting

        morning_time = datetime(2021, 12, 25, 8, 0, 0)
        greeting = get_greeting(morning_time)

        assert greeting == "Доброе утро"

    def test_main_page_greeting_evening(self):
        """Тест приветствия для вечера."""
        from src.utils import get_greeting

        evening_time = datetime(2021, 12, 25, 20, 0, 0)
        greeting = get_greeting(evening_time)

        assert greeting == "Добрый вечер"

    def test_main_page_greeting_night(self):
        """Тест приветствия для ночи."""
        from src.utils import get_greeting

        night_time = datetime(2021, 12, 25, 2, 0, 0)
        greeting = get_greeting(night_time)

        assert greeting == "Доброй ночи"

    def test_main_page_greeting_afternoon(self):
        """Тест приветствия для дня."""
        from src.utils import get_greeting

        afternoon_time = datetime(2021, 12, 25, 15, 0, 0)
        greeting = get_greeting(afternoon_time)

        assert greeting == "Добрый день"


class TestMainPageAdditional:
    """Дополнительные тесты для увеличения покрытия."""

    @patch("src.views.filter_transactions_by_date_range")
    @patch("src.views.load_stock_prices")
    @patch("src.views.load_exchange_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions")
    @patch("src.views.get_top_transactions")
    @patch("src.views.get_cashback")
    @patch("src.views.get_card_spending")
    @patch("src.views.get_greeting")
    def test_main_page_with_multiple_cards(
        self,
        mock_greeting,
        mock_card_spending,
        mock_cashback,
        mock_top_transactions,
        mock_load,
        mock_settings,
        mock_rates,
        mock_stocks,
        mock_filter,
    ):
        """Тест с несколькими картами."""
        test_df = pd.DataFrame(
            {
                "Дата операции": pd.to_datetime(["2021-12-01"]),
                "Номер карты": [1234556],
                "Статус": ["OK"],
                "Сумма платежа": [-1000],
                "Валюта платежа": ["RUB"],
            }
        )

        mock_greeting.return_value = "Добрый день"
        mock_card_spending.return_value = [
            {"last_digits": "4556", "total_spent": 1000.0, "cashback": 10.0},
            {"last_digits": "5091", "total_spent": 500.0, "cashback": 5.0},
            {"last_digits": "7197", "total_spent": 300.0, "cashback": 3.0},
        ]
        mock_cashback.return_value = 18.0
        mock_top_transactions.return_value = [
            {"date": "2021-12-01", "amount": 1000, "currency": "RUB", "description": "Test1", "category": "Cat1"},
            {"date": "2021-12-02", "amount": 500, "currency": "RUB", "description": "Test2", "category": "Cat2"},
        ]
        mock_load.return_value = test_df
        mock_filter.return_value = test_df
        mock_settings.return_value = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]}
        mock_rates.return_value = {"USD": 1.0, "EUR": 0.92}
        mock_stocks.return_value = {"AAPL": 150.0, "GOOGL": 2800.0}

        from src.views import main_page

        result = main_page("2021-12-25 14:30:00")
        data = json.loads(result)

        assert len(data["cards"]) == 3
        assert len(data["top_transactions"]) == 2
        assert len(data["exchange_rates"]) == 2
        assert len(data["stock_prices"]) == 2

    @patch("src.views.filter_transactions_by_date_range")
    @patch("src.views.load_stock_prices")
    @patch("src.views.load_exchange_rates")
    @patch("src.views.load_user_settings")
    @patch("src.views.load_transactions")
    @patch("src.views.get_top_transactions")
    @patch("src.views.get_cashback")
    @patch("src.views.get_card_spending")
    @patch("src.views.get_greeting")
    def test_main_page_empty_cards(
        self,
        mock_greeting,
        mock_card_spending,
        mock_cashback,
        mock_top_transactions,
        mock_load,
        mock_settings,
        mock_rates,
        mock_stocks,
        mock_filter,
    ):
        """Тест когда нет данных по картам."""
        test_df = pd.DataFrame(
            {
                "Дата операции": pd.to_datetime(["2021-12-01"]),
                "Номер карты": [1234556],
                "Статус": ["OK"],
                "Сумма платежа": [-1000],
                "Валюта платежа": ["RUB"],
            }
        )

        mock_greeting.return_value = "Добрый день"
        mock_card_spending.return_value = []
        mock_cashback.return_value = 0.0
        mock_top_transactions.return_value = []
        mock_load.return_value = test_df
        mock_filter.return_value = test_df
        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = {"USD": 1.0}
        mock_stocks.return_value = {"AAPL": 150.0}

        from src.views import main_page

        result = main_page("2021-12-25 14:30:00")
        data = json.loads(result)

        assert data["cards"] == []
        assert data["total_cashback"] == 0.0
        assert data["top_transactions"] == []
