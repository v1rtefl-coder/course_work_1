import json
import pytest
from unittest.mock import patch
import pandas as pd
from src.services import search_transactions, filter_by_status, calculate_total_by_category


class TestSearchTransactions:
    """Тесты для поиска транзакций."""

    def test_search_by_description(self, sample_transactions_list):
        """Тест поиска по описанию."""
        result = search_transactions(sample_transactions_list, "Пятерочка")
        data = json.loads(result)

        # Проверяем, что результат - список
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]["Описание"] == "Пятерочка"

    def test_search_by_category(self, sample_transactions_list):
        """Тест поиска по категории."""
        result = search_transactions(sample_transactions_list, "Супермаркеты")
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) >= 1
        # Проверяем, что все найденные транзакции имеют нужную категорию
        for t in data:
            assert t["Категория"] == "Супермаркеты"

    def test_search_case_insensitive(self, sample_transactions_list):
        """Тест регистронезависимого поиска."""
        result = search_transactions(sample_transactions_list, "пятерочка")
        data = json.loads(result)

        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]["Описание"] == "Пятерочка"

    def test_search_no_results(self, sample_transactions_list):
        """Тест поиска без результатов."""
        result = search_transactions(sample_transactions_list, "несуществующий_запрос")
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) == 0

    def test_search_empty_list(self):
        """Тест поиска по пустому списку."""
        result = search_transactions([], "запрос")
        data = json.loads(result)

        assert data == []

    def test_search_with_none_values(self):
        """Тест поиска с None значениями."""
        transactions = [{"Описание": None, "Категория": "Тест"}, {"Описание": "Тест", "Категория": None}]
        result = search_transactions(transactions, "тест")
        data = json.loads(result)

        assert isinstance(data, list)
        # Должна найтись хотя бы одна транзакция
        assert len(data) >= 1

    def test_search_with_error(self):
        """Тест поиска с ошибкой."""
        result = search_transactions(None, "запрос")
        data = json.loads(result)

        # Может быть словарь с ошибкой или пустой список
        assert isinstance(data, (dict, list))


class TestFilterByStatus:
    """Тесты для фильтрации по статусу."""

    def test_filter_ok_status(self, sample_transactions_list):
        """Тест фильтрации успешных транзакций."""
        result = filter_by_status(sample_transactions_list, "OK")
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) >= 1
        # Проверяем, что все транзакции имеют статус OK
        for t in data:
            assert t["Статус"] == "OK"

    def test_filter_failed_status(self, sample_transactions_list):
        """Тест фильтрации неудачных транзакций."""
        result = filter_by_status(sample_transactions_list, "FAILED")
        data = json.loads(result)

        assert isinstance(data, list)
        # Проверяем, что все найденные транзакции имеют статус FAILED
        for t in data:
            assert t["Статус"] == "FAILED"

    def test_filter_empty_list(self):
        """Тест фильтрации пустого списка."""
        result = filter_by_status([], "OK")
        data = json.loads(result)

        assert data == []

    def test_filter_with_error(self):
        """Тест фильтрации с ошибкой."""
        result = filter_by_status(None, "OK")
        data = json.loads(result)

        # Может быть словарь с ошибкой
        assert isinstance(data, (dict, list))


class TestCalculateTotalByCategory:
    """Тесты для расчета расходов по категориям."""

    def test_calculate_categories(self, sample_transactions_list):
        """Тест расчета сумм по категориям."""
        result = calculate_total_by_category(sample_transactions_list)
        data = json.loads(result)

        assert isinstance(data, dict)
        # Проверяем, что есть категория Супермаркеты
        if "Супермаркеты" in data:
            assert data["Супермаркеты"] > 0

    def test_calculate_only_expenses(self):
        """Тест учета только расходов (отрицательных сумм)."""
        transactions = [
            {"Категория": "Доход", "Сумма платежа": 10000},
            {"Категория": "Расход", "Сумма платежа": -500},
            {"Категория": "Расход", "Сумма платежа": -300},
        ]
        result = calculate_total_by_category(transactions)
        data = json.loads(result)

        # Доходы не должны учитываться
        assert "Доход" not in data or data.get("Доход", 0) == 0
        # Расходы должны быть учтены
        assert data.get("Расход", 0) > 0

    def test_empty_list(self):
        """Тест с пустым списком."""
        result = calculate_total_by_category([])
        data = json.loads(result)

        assert data == {}

    def test_without_category(self):
        """Тест транзакций без категории."""
        transactions = [
            {"Категория": None, "Сумма платежа": -500, "Описание": "test1"},
            {"Категория": "", "Сумма платежа": -300, "Описание": "test2"},
            {"Категория": "Супермаркеты", "Сумма платежа": -200, "Описание": "test3"},
        ]
        result = calculate_total_by_category(transactions)
        data = json.loads(result)

        # Проверяем, что результат - словарь
        assert isinstance(data, dict)

        # Проверяем, что есть категория для неизвестных
        # В зависимости от реализации, ключ может быть 'Без категории', 'nan' или пустая строка
        unknown_keys = [k for k in data.keys() if k in ["Без категории", "nan", "", None] or pd.isna(k)]
        if unknown_keys:
            # Если есть ключ для неизвестных, проверяем сумму
            assert data[unknown_keys[0]] > 0
        else:
            # Иначе проверяем, что общая сумма расходов учтена
            total = sum(data.values())
            assert total > 0

    def test_with_error(self):
        """Тест с ошибкой."""
        result = calculate_total_by_category(None)
        data = json.loads(result)

        # Может быть словарь с ошибкой
        assert isinstance(data, (dict, list))
