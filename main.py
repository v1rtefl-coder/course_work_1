import json
import logging
import os
import pandas as pd
from datetime import datetime, timedelta

from src.reports import generate_detailed_report, monthly_summary, spending_by_weekday
from src.services import calculate_total_by_category, filter_by_status, search_transactions
from src.utils import load_transactions
from src.views import main_page

# Создаем папку для логов если её нет
os.makedirs('logs', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Главная функция для демонстрации всех возможностей проекта."""
    print("=" * 60)
    print("Финансовый дашборд - Курсовая работа 1")
    print("=" * 60)

    # Загрузка данных
    print("\n1. Загрузка транзакций...")
    transactions_df = load_transactions()

    if transactions_df.empty:
        print("Ошибка: Нет данных о транзакциях. Проверьте файл data/operations.xlsx")
        return

    print(f"   Загружено {len(transactions_df)} транзакций")

    # Определяем диапазон дат в данных
    min_date = transactions_df['Дата операции'].min()
    max_date = transactions_df['Дата операции'].max()
    print(f"   Диапазон дат: {min_date.strftime('%Y-%m-%d')} - {max_date.strftime('%Y-%m-%d')}")

    # Демонстрация работы главной страницы
    print("\n2. Генерация ответа для главной страницы...")
    # Используем максимальную дату из данных для отображения актуальной информации
    current_datetime = max_date.strftime('%Y-%m-%d %H:%M:%S')
    main_response = main_page(current_datetime)
    print("   JSON ответ для главной страницы:")
    response_dict = json.loads(main_response)
    print(json.dumps(response_dict, indent=2, ensure_ascii=False)[:500] + "...")

    # Демонстрация работы сервисов
    print("\n3. Демонстрация работы сервисов...")

    # Конвертация DataFrame в список словарей для сервисов
    transactions_list = transactions_df.to_dict(orient='records')

    # Поиск транзакций
    search_query = "супермаркет"
    print(f"\n   Поиск транзакций по запросу '{search_query}':")
    search_results = search_transactions(transactions_list, search_query)
    results = json.loads(search_results)
    if isinstance(results, list):
        print(f"   Найдено транзакций: {len(results)}")
    else:
        print(f"   Результат: {results}")

    # Фильтрация по статусу
    print("\n   Фильтрация успешных транзакций:")
    successful = filter_by_status(transactions_list, "OK")
    success_list = json.loads(successful)
    if isinstance(success_list, list):
        print(f"   Успешных транзакций: {len(success_list)}")
    else:
        print(f"   Результат: {success_list}")

    # Расчет по категориям
    print("\n   Расчет расходов по категориям:")
    category_totals = calculate_total_by_category(transactions_list)
    categories = json.loads(category_totals)
    if isinstance(categories, dict) and "error" not in categories:
        print("   Топ-5 категорий расходов:")
        for i, (cat, amount) in enumerate(list(categories.items())[:5], 1):
            # Заменяем NaN, nan, None на 'Без категории'
            if cat in ['NaN', 'nan', 'None', None] or (isinstance(cat, float) and pd.isna(cat)):
                cat_name = 'Без категории'
            else:
                cat_name = str(cat)
            print(f"     {i}. {cat_name}: {amount:.2f} руб.")
    else:
        print(f"   Ошибка: {categories}")

    # Демонстрация работы отчетов
    print("\n4. Демонстрация работы отчетов...")

    # Отчет по дням недели (используем максимальную дату из данных)
    print("\n   Генерация отчета 'Траты по дням недели':")
    date_str = max_date.strftime('%Y-%m-%d')
    weekday_report = spending_by_weekday(transactions_df, date_str)
    if not weekday_report.empty:
        print("   Средние траты по дням недели:")
        for day, amount in weekday_report.iterrows():
            print(f"     {day}: {amount['Средние траты']:.2f} руб.")
    else:
        print("   Нет данных для отчета (возможно, нет расходов за период)")

    # Месячная сводка (используем максимальную дату из данных)
    print("\n   Генерация месячной сводки:")
    target_date = max_date
    monthly = monthly_summary(transactions_df, target_date.year, target_date.month)
    if isinstance(monthly, dict) and "error" not in monthly:
        print(f"   Сводка за {target_date.year}-{target_date.month:02d}:")
        print(f"     Доходы: {monthly.get('total_income', 0):.2f} руб.")
        print(f"     Расходы: {monthly.get('total_expenses', 0):.2f} руб.")
        print(f"     Баланс: {monthly.get('balance', 0):.2f} руб.")
        print(f"     Количество транзакций: {monthly.get('transaction_count', 0)}")
    else:
        print(f"   Ошибка: {monthly}")

    # Детальный отчет за последние 30 дней от максимальной даты
    print("\n   Генерация детального отчета за последние 30 дней:")
    end_date = max_date
    start_date = end_date - timedelta(days=30)
    detailed = generate_detailed_report(
        transactions_df,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    print("   Детальный отчет сгенерирован")

    print("\n" + "=" * 60)
    print("✅ Все функции успешно выполнены!")
    print("=" * 60)


if __name__ == "__main__":
    main()
