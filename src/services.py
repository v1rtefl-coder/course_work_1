import json
import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def search_transactions(transactions: List[Dict[str, Any]], search_query: str) -> str:
    """
    Выполняет поиск транзакций по описанию или категории.

    Args:
        transactions: Список транзакций в формате словарей
        search_query: Строка для поиска

    Returns:
        str: JSON-строка с найденными транзакциями
    """
    try:
        logger.info(f"Поиск транзакций по запросу: '{search_query}'")

        if not transactions:
            logger.warning("Список транзакций пуст")
            return json.dumps([], ensure_ascii=False)

        search_query_lower = search_query.lower()

        def matches_query(transaction):
            description = transaction.get('Описание', '')
            category = transaction.get('Категория', '')

            if not isinstance(description, str):
                description = str(description) if description is not None else ''
            if not isinstance(category, str):
                category = str(category) if category is not None else ''

            return (
                search_query_lower in description.lower() or
                search_query_lower in category.lower()
            )

        filtered_transactions = list(filter(matches_query, transactions))

        logger.info(f"Найдено {len(filtered_transactions)} транзакций")

        result = []
        for transaction in filtered_transactions:
            transaction_copy = {}
            for key, value in transaction.items():
                if hasattr(value, 'isoformat'):
                    transaction_copy[key] = value.isoformat()
                elif isinstance(value, float) and pd.isna(value):
                    transaction_copy[key] = None
                else:
                    transaction_copy[key] = value
            result.append(transaction_copy)

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        return json.dumps({"error": f"Ошибка поиска: {e}"}, ensure_ascii=False)


def filter_by_status(transactions: List[Dict[str, Any]], status: str) -> str:
    """
    Фильтрует транзакции по статусу.

    Args:
        transactions: Список транзакций
        status: Статус для фильтрации

    Returns:
        str: JSON-строка с отфильтрованными транзакциями
    """
    try:
        filtered = list(filter(lambda t: t.get('Статус') == status, transactions))
        return json.dumps(filtered, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Ошибка фильтрации: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def calculate_total_by_category(transactions: List[Dict[str, Any]]) -> str:
    """
    Рассчитывает суммы расходов по категориям.

    Args:
        transactions: Список транзакций

    Returns:
        str: JSON-строка с суммами по категориям
    """
    try:
        # Фильтрация только расходов (отрицательные суммы)
        expenses = list(filter(lambda t: t.get('Сумма платежа', 0) < 0, transactions))

        # Группировка по категориям и суммирование
        categories = {}
        for expense in expenses:
            category = expense.get('Категория', 'Без категории')
            if category is None or category == '':
                category = 'Без категории'
            amount = abs(expense.get('Сумма платежа', 0))
            categories[category] = categories.get(category, 0) + amount

        # Сортировка по убыванию
        sorted_categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

        return json.dumps(sorted_categories, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка расчета: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
