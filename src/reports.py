import json
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def save_report_to_file(filename: Optional[str] = None):
    """
    Декоратор для сохранения отчета в файл.

    Args:
        filename: Имя файла для сохранения (опционально)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Выполнение функции
            result = func(*args, **kwargs)

            # Определение имени файла
            if filename:
                report_filename = filename
            else:
                # Формат имени файла по умолчанию: report_YYYYMMDD_HHMMSS.json
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_filename = f"report_{func.__name__}_{timestamp}.json"

            # Создание директории для отчетов
            os.makedirs('reports_output', exist_ok=True)
            filepath = os.path.join('reports_output', report_filename)

            # Сохранение результата
            try:
                if isinstance(result, pd.DataFrame):
                    result.to_json(
                        filepath, orient='records', force_ascii=False,
                        indent=2, date_format='iso'
                    )
                elif isinstance(result, (dict, list)):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(
                            result, f, ensure_ascii=False,
                            indent=2, default=str
                        )
                else:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(result))

                logger.info(f"Отчет сохранен в {filepath}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result
        return wrapper
    return decorator


@save_report_to_file()
def spending_by_weekday(
    transactions: pd.DataFrame, date: Optional[str] = None
) -> pd.DataFrame:
    """
    Возвращает средние траты по дням недели за последние 3 месяца.

    Args:
        transactions: Датафрейм с транзакциями
        date: Опциональная дата в формате 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: Датафрейм со средними тратами по дням недели
    """
    try:
        logger.info("Генерация отчета 'Траты по дням недели'")

        if transactions.empty:
            logger.warning("Датафрейм транзакций пуст")
            return pd.DataFrame()

        # Копируем данные чтобы не изменять оригинал
        df = transactions.copy()

        # Парсинг даты операции
        if 'Дата операции' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['Дата операции']):
                df['Дата операции'] = pd.to_datetime(
                    df['Дата операции'], format='%d.%m.%Y %H:%M:%S', errors='coerce'
                )
            df = df.dropna(subset=['Дата операции'])

        # Определение даты
        if date:
            end_date = datetime.strptime(date, '%Y-%m-%d')
        else:
            end_date = datetime.now()

        # Расчет даты 3 месяца назад
        start_date = end_date - timedelta(days=90)

        # Фильтрация за последние 3 месяца
        mask = (
            (df['Дата операции'].dt.date >= start_date.date()) &
            (df['Дата операции'].dt.date <= end_date.date())
        )
        filtered_df = df[mask].copy()

        # Фильтрация только расходов (отрицательные суммы)
        expenses_df = filtered_df[filtered_df['Сумма платежа'] < 0].copy()

        if expenses_df.empty:
            logger.warning("Нет расходов за указанный период")
            return pd.DataFrame()

        # Добавление дня недели
        day_names_map = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник',
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
        }

        expenses_df['День недели_en'] = expenses_df['Дата операции'].dt.day_name()
        expenses_df['День недели'] = expenses_df['День недели_en'].map(day_names_map)

        # Группировка по дням недели
        weekday_spending = expenses_df.groupby('День недели').agg({
            'Сумма платежа': lambda x: abs(x.mean())
        }).round(2)

        # Порядок дней недели
        weekday_order = [
            'Понедельник', 'Вторник', 'Среда',
            'Четверг', 'Пятница', 'Суббота', 'Воскресенье'
        ]
        weekday_spending = weekday_spending.reindex(weekday_order)

        weekday_spending = weekday_spending.rename(
            columns={'Сумма платежа': 'Средние траты'}
        )

        logger.info(
            f"Отчет сгенерирован за период {start_date.date()} - {end_date.date()}"
        )
        return weekday_spending

    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {e}")
        return pd.DataFrame()


@save_report_to_file("monthly_summary.json")
def monthly_summary(
    transactions: pd.DataFrame, year: int, month: int
) -> Dict[str, Any]:
    """
    Генерирует сводку по месяцу.

    Args:
        transactions: Датафрейм с транзакциями
        year: Год
        month: Месяц

    Returns:
        Dict: Сводная информация по месяцу
    """
    try:
        logger.info(f"Генерация сводки за {year}-{month:02d}")

        if transactions.empty:
            return {"error": "Нет данных"}

        # Фильтрация за месяц
        transactions['Дата операции'] = pd.to_datetime(
            transactions['Дата операции'],
            format='%d.%m.%Y %H:%M:%S',
            errors='coerce'
        )
        mask = (
            (transactions['Дата операции'].dt.year == year) &
            (transactions['Дата операции'].dt.month == month)
        )
        filtered_df = transactions[mask]

        if filtered_df.empty:
            return {"error": f"Нет данных за {year}-{month:02d}"}

        # Расчет метрик
        total_income = filtered_df[
            filtered_df['Сумма платежа'] > 0
        ]['Сумма платежа'].sum()
        total_expenses = abs(
            filtered_df[filtered_df['Сумма платежа'] < 0]['Сумма платежа'].sum()
        )
        transaction_count = len(filtered_df)
        avg_transaction = filtered_df['Сумма платежа'].mean()

        # Топ категории
        expenses_df = filtered_df[filtered_df['Сумма платежа'] < 0]
        top_categories = (
            expenses_df.groupby('Категория')['Сумма платежа']
            .sum().abs()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
        )

        summary = {
            "year": year,
            "month": month,
            "total_income": round(float(total_income), 2),
            "total_expenses": round(float(total_expenses), 2),
            "balance": round(float(total_income - total_expenses), 2),
            "transaction_count": int(transaction_count),
            "avg_transaction": round(float(avg_transaction), 2),
            "top_categories": top_categories
        }

        logger.info(f"Сводка сгенерирована: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Ошибка генерации сводки: {e}")
        return {"error": str(e)}


def generate_detailed_report(
    transactions: pd.DataFrame, start_date: str, end_date: str
) -> str:
    """
    Генерирует детальный отчет за период.

    Args:
        transactions: Датафрейм с транзакциями
        start_date: Начальная дата
        end_date: Конечная дата

    Returns:
        str: JSON-строка с отчетом
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        transactions['Дата операции'] = pd.to_datetime(
            transactions['Дата операции'],
            format='%d.%m.%Y %H:%M:%S',
            errors='coerce'
        )
        mask = (
            (transactions['Дата операции'].dt.date >= start.date()) &
            (transactions['Дата операции'].dt.date <= end.date())
        )
        filtered_df = transactions[mask]

        report = {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "total_transactions": len(filtered_df),
            "total_income": round(
                float(
                    filtered_df[filtered_df['Сумма платежа'] > 0]['Сумма платежа'].sum()
                ), 2
            ),
            "total_expenses": round(
                float(
                    abs(filtered_df[filtered_df['Сумма платежа'] < 0]['Сумма платежа'].sum())
                ), 2
            ),
            "transactions": filtered_df.to_dict(orient='records')
        }

        return json.dumps(report, ensure_ascii=False, indent=2, default=str)

    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
