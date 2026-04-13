import glob
import json
import logging
import os
from datetime import datetime  # удалили timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def parse_date(date_series):
    """
    Универсальный парсинг дат из Excel.

    Args:
        date_series: Серия с датами

    Returns:
        pd.Series: Серия с datetime объектами
    """
    return pd.to_datetime(date_series, format='%d.%m.%Y %H:%M:%S', errors='coerce')


def load_transactions(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """
    Загружает транзакции из Excel файла.

    Args:
        file_path: Путь к файлу с транзакциями

    Returns:
        pd.DataFrame: Датафрейм с транзакциями
    """
    try:
        # Если файл не найден, ищем в папке data
        if not os.path.exists(file_path):
            excel_files = glob.glob("data/*.xlsx")
            if excel_files:
                file_path = excel_files[0]
                logger.info(f"Найден файл: {file_path}")

        df = pd.read_excel(file_path)

        # Парсинг даты операции с учетом времени
        if 'Дата операции' in df.columns:
            df['Дата операции'] = parse_date(df['Дата операции'])
            df = df.dropna(subset=['Дата операции'])

        logger.info(f"Загружено {len(df)} транзакций из {file_path}")
        return df
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return pd.DataFrame()


def filter_transactions_by_date_range(
    df: pd.DataFrame, end_date: datetime, start_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Фильтрует транзакции по диапазону дат.

    Args:
        df: Датафрейм с транзакциями
        end_date: Конечная дата
        start_date: Начальная дата (если не указана - начало месяца end_date)

    Returns:
        pd.DataFrame: Отфильтрованный датафрейм
    """
    if df.empty:
        return df

    if 'Дата операции' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['Дата операции']):
            df['Дата операции'] = parse_date(df['Дата операции'])

    if start_date is None:
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0)

    mask = (df['Дата операции'].dt.date >= start_date.date()) & (df['Дата операции'].dt.date <= end_date.date())
    filtered_df = df[mask]

    logger.info(f"Отфильтровано {len(filtered_df)} транзакций за период {start_date.date()} - {end_date.date()}")
    return filtered_df


def get_greeting(current_time: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    Args:
        current_time: Текущее время

    Returns:
        str: Приветствие
    """
    hour = current_time.hour

    if 5 <= hour < 12:
        greeting = "Доброе утро"
    elif 12 <= hour < 18:
        greeting = "Добрый день"
    elif 18 <= hour < 23:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"

    logger.debug(f"Приветствие для часа {hour}: {greeting}")
    return greeting


def get_card_spending(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Рассчитывает расходы по каждой карте.

    Args:
        df: Датафрейм с транзакциями

    Returns:
        List[Dict]: Список словарей с данными по картам
    """
    if df.empty:
        return []

    successful_df = df[df['Статус'] == 'OK'].copy()

    if successful_df.empty:
        return []

    has_cashback = 'Кешбэк' in successful_df.columns

    agg_dict = {'Сумма платежа': 'sum'}
    if has_cashback:
        agg_dict['Кешбэк'] = 'sum'

    card_stats = successful_df.groupby('Номер карты').agg(agg_dict).reset_index()

    result = []
    for _, row in card_stats.iterrows():
        card_number = str(row['Номер карты'])[-4:]
        total_spent = abs(row['Сумма платежа'])

        if has_cashback and pd.notna(row.get('Кешбэк', 0)):
            cashback = row['Кешбэк']
        else:
            cashback = total_spent / 100

        result.append({
            "last_digits": card_number,
            "total_spent": round(total_spent, 2),
            "cashback": round(cashback, 2)
        })

    logger.info(f"Рассчитаны данные по {len(result)} картам")
    return result


def get_cashback(df: pd.DataFrame) -> float:
    """
    Рассчитывает общий кешбэк.

    Args:
        df: Датафрейм с транзакциями

    Returns:
        float: Сумма кешбэка
    """
    if df.empty:
        return 0.0

    successful_df = df[df['Статус'] == 'OK']

    if 'Кешбэк' in successful_df.columns:
        cashback_sum = successful_df['Кешбэк'].sum()
        if cashback_sum > 0:
            return round(cashback_sum, 2)

    total_expenses = abs(successful_df[successful_df['Сумма платежа'] < 0]['Сумма платежа'].sum())
    calculated_cashback = total_expenses / 100

    logger.info(f"Рассчитан кешбэк: {round(calculated_cashback, 2)} руб.")
    return round(calculated_cashback, 2)


def get_top_transactions(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """
    Возвращает топ N транзакций по сумме платежа.

    Args:
        df: Датафрейм с транзакциями
        n: Количество транзакций

    Returns:
        List[Dict]: Список топ транзакций
    """
    if df.empty:
        return []

    df_sorted = df.sort_values('Сумма платежа', key=abs, ascending=False).head(n)

    result = []
    for _, row in df_sorted.iterrows():
        date_val = row['Дата операции']
        if pd.notna(date_val):
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
        else:
            date_str = ""

        result.append({
            "date": date_str,
            "amount": abs(row['Сумма платежа']),
            "currency": row['Валюта платежа'] if pd.notna(row['Валюта платежа']) else "RUB",
            "description": row['Описание'] if pd.notna(row['Описание']) else "",
            "category": row['Категория'] if pd.notna(row['Категория']) else ""
        })

    logger.info(f"Сформирован топ-{n} транзакций")
    return result


def load_user_settings(file_path: str = "user_settings.json") -> Dict[str, List[str]]:
    """
    Загружает пользовательские настройки из JSON файла.

    Args:
        file_path: Путь к файлу настроек

    Returns:
        Dict: Словарь с настройками
    """
    default_settings = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            logger.info(f"Загружены настройки из {file_path}")
            return settings
    except FileNotFoundError:
        logger.warning(f"Файл {file_path} не найден, используются настройки по умолчанию")
        return default_settings
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return default_settings


def load_exchange_rates(currencies: List[str]) -> Dict[str, float]:
    """
    Загружает курсы валют через API.

    Args:
        currencies: Список валют

    Returns:
        Dict: Словарь с курсами валют
    """
    rates = {}

    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            for currency in currencies:
                if currency in data.get('rates', {}):
                    rates[currency] = data['rates'][currency]
            logger.info(f"Загружены курсы валют: {rates}")
        else:
            logger.error(f"Ошибка API: {response.status_code}")
            for currency in currencies:
                rates[currency] = 90.0 if currency == 'RUB' else 95.0 if currency == 'EUR' else 1.0
    except Exception as e:
        logger.error(f"Ошибка при загрузке курсов валют: {e}")
        for currency in currencies:
            rates[currency] = 90.0 if currency == 'RUB' else 95.0 if currency == 'EUR' else 1.0

    return rates


def load_stock_prices(stocks: List[str]) -> Dict[str, float]:
    """
    Загружает цены на акции через API.

    Args:
        stocks: Список тикеров акций

    Returns:
        Dict: Словарь с ценами акций
    """
    prices = {}

    try:
        api_key = os.getenv('STOCK_API_KEY')
        api_url = os.getenv('STOCK_API_URL', 'https://www.alphavantage.co/query')

        for stock in stocks:
            if api_key:
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': stock,
                    'apikey': api_key
                }
                response = requests.get(api_url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if 'Global Quote' in data and '05. price' in data['Global Quote']:
                        prices[stock] = float(data['Global Quote']['05. price'])
                    else:
                        prices[stock] = 150.0
                else:
                    prices[stock] = 150.0
            else:
                prices[stock] = 150.0

        logger.info(f"Загружены цены акций: {prices}")

    except Exception as e:
        logger.error(f"Ошибка при загрузке цен акций: {e}")
        for stock in stocks:
            prices[stock] = 150.0

    return prices
