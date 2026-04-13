import json
import logging
from datetime import datetime

from src.utils import (
    filter_transactions_by_date_range,
    get_card_spending,
    get_cashback,
    get_greeting,
    get_top_transactions,
    load_exchange_rates,
    load_stock_prices,
    load_transactions,
    load_user_settings,
)

logger = logging.getLogger(__name__)


def main_page(date_time_str: str) -> str:
    """
    Генерирует JSON-ответ для главной страницы.

    Args:
        date_time_str: Строка с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        str: JSON-строка с данными для главной страницы
    """
    try:
        logger.info(f"Обработка запроса для главной страницы с датой: {date_time_str}")

        current_datetime = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')

        transactions_df = load_transactions()

        if transactions_df.empty:
            logger.warning("Нет данных о транзакциях")
            return json.dumps({"error": "Нет данных о транзакциях"}, ensure_ascii=False)

        filtered_df = filter_transactions_by_date_range(transactions_df, current_datetime)

        greeting = get_greeting(current_datetime)
        cards_data = get_card_spending(filtered_df)
        cashback = get_cashback(filtered_df)
        top_transactions = get_top_transactions(filtered_df, 5)

        user_settings = load_user_settings()
        exchange_rates = load_exchange_rates(user_settings.get('user_currencies', ['USD', 'EUR']))
        stock_prices = load_stock_prices(user_settings.get('user_stocks', ['AAPL', 'AMZN', 'GOOGL', 'MSFT', 'TSLA']))

        response = {
            "greeting": greeting,
            "cards": cards_data,
            "total_cashback": cashback,
            "top_transactions": top_transactions,
            "exchange_rates": exchange_rates,
            "stock_prices": stock_prices,
            "period": {
                "start": current_datetime.replace(day=1).strftime('%Y-%m-%d'),
                "end": current_datetime.strftime('%Y-%m-%d')
            }
        }

        result_json = json.dumps(response, ensure_ascii=False, indent=2)
        logger.info("JSON-ответ успешно сгенерирован")
        return result_json

    except ValueError as e:
        logger.error(f"Ошибка формата даты: {e}")
        return json.dumps({"error": f"Неверный формат даты: {e}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return json.dumps({"error": f"Внутренняя ошибка сервера: {e}"}, ensure_ascii=False)
