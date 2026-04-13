import json
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.views import main_page
    from src.services import search_transactions
    from src.utils import load_transactions

    print("=" * 60)
    print("Быстрая проверка функциональности проекта")
    print("=" * 60)

    # Тест загрузки данных
    print("\n1. Проверка загрузки данных...")
    df = load_transactions()
    if df.empty:
        print("   ❌ Не удалось загрузить данные")
        sys.exit(1)
    print(f"   ✅ Загружено {len(df)} транзакций")

    # Тест главной страницы
    print("\n2. Проверка main_page...")
    try:
        result = main_page("2021-12-25 14:30:00")
        data = json.loads(result)

        print(f"   Приветствие: {data.get('greeting')}")
        print(f"   Количество карт: {len(data.get('cards', []))}")
        print(f"   Кешбэк: {data.get('total_cashback')} руб.")
        print(f"   Топ транзакций: {len(data.get('top_transactions', []))}")
        print(f"   Курсы валют: {data.get('exchange_rates')}")
        print(f"   Цены акций: {data.get('stock_prices')}")
        print("   ✅ main_page работает корректно!")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест поиска
    print("\n3. Проверка поиска транзакций...")
    try:
        transactions_list = df.to_dict(orient='records')
        result = search_transactions(transactions_list, "супермаркет")
        data = json.loads(result)

        if isinstance(data, list):
            print(f"   ✅ Поиск работает: найдено {len(data)} транзакций")
        else:
            print(f"   ⚠️ Результат поиска: {data}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест отчетов
    print("\n4. Проверка отчетов...")
    try:
        from src.reports import spending_by_weekday, monthly_summary

        # Отчет по дням недели
        report = spending_by_weekday(df, "2021-12-25")
        if not report.empty:
            print(f"   ✅ Отчет по дням недели сгенерирован: {len(report)} дней")
        else:
            print("   ⚠️ Отчет по дням недели пуст")

        # Месячная сводка
        summary = monthly_summary(df, 2021, 12)
        if 'error' not in summary:
            print(f"   ✅ Месячная сводка: доходы {summary.get('total_income', 0):.2f} руб.")
        else:
            print(f"   ⚠️ Месячная сводка: {summary.get('error')}")

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    print("\n" + "=" * 60)
    print("✅ Проверка завершена!")
    print("=" * 60)

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что все модули на месте")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")
