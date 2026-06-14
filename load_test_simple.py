# load_test_simple.py

import time
import random
from datetime import datetime
from urllib import request as urllib_request
from urllib.error import URLError

from config import BOT_TOKEN

# ===== НАСТРОЙКИ ТЕСТИРОВАНИЯ =====
BOT_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
REQUEST_COUNT = 50
DELAY_BETWEEN_REQUESTS = 0.3

# Методы API для тестирования
TEST_METHODS = ["getMe", "getUpdates"]

# ===== СБОР СТАТИСТИКИ =====
stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "response_times": []
}


def send_request(request_id: int, method: str) -> dict:
    """Отправляет запрос к Telegram Bot API"""
    url = f"{BOT_API_URL}/{method}"
    start_time = time.time()

    try:
        req = urllib_request.Request(url)
        with urllib_request.urlopen(req, timeout=10) as response:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000

            return {
                "request_id": request_id,
                "method": method,
                "status_code": response.getcode(),
                "response_time_ms": round(response_time, 2),
                "success": response.getcode() == 200
            }
    except URLError as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return {
            "request_id": request_id,
            "method": method,
            "status_code": None,
            "response_time_ms": round(response_time, 2),
            "success": False,
            "error": str(e)
        }


def run_load_test():
    """Запуск нагрузочного тестирования"""
    print("=" * 60)
    print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ TELEGRAM-БОТА")
    print("=" * 60)
    print(f"Начало теста: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Количество запросов: {REQUEST_COUNT}")
    print(f"Задержка между запросами: {DELAY_BETWEEN_REQUESTS} сек")
    print("-" * 60)

    start_all = time.time()

    for i in range(1, REQUEST_COUNT + 1):
        method = random.choice(TEST_METHODS)
        result = send_request(i, method)

        stats["total"] += 1
        if result["success"]:
            stats["success"] += 1
            print(f"#{result['request_id']}: {result['method']} - {result['response_time_ms']} мс")
        else:
            stats["failed"] += 1
            error_msg = result.get('error', f"HTTP {result['status_code']}")
            print(f"#{result['request_id']}: {result['method']} - ОШИБКА: {error_msg}")

        stats["response_times"].append(result["response_time_ms"])
        time.sleep(DELAY_BETWEEN_REQUESTS)

    end_all = time.time()
    total_time = end_all - start_all

    # Вывод статистики
    print("-" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("-" * 60)
    print(f"Общее время теста: {total_time:.2f} сек")
    print(f"Успешных запросов: {stats['success']} / {stats['total']}")
    print(f"Неудачных запросов: {stats['failed']} / {stats['total']}")

    if stats["response_times"]:
        avg_time = sum(stats["response_times"]) / len(stats["response_times"])
        min_time = min(stats["response_times"])
        max_time = max(stats["response_times"])

        print(f"\nСтатистика времени ответа (мс):")
        print(f"  Среднее: {avg_time:.2f} мс")
        print(f"  Минимум: {min_time:.2f} мс")
        print(f"  Максимум: {max_time:.2f} мс")

    # Оценка соответствия ТЗ
    print("-" * 60)
    print("ОЦЕНКА СООТВЕТСТВИЯ ТРЕБОВАНИЯМ ТЗ")
    print("-" * 60)

    success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
    print(f"Успешность выполнения запросов: {success_rate:.1f}%")
    print(f"Требование (≥99%) - {'ВЫПОЛНЕНО' if success_rate >= 99 else 'НЕ ВЫПОЛНЕНО'}")

    if stats["response_times"]:
        avg_time = sum(stats["response_times"]) / len(stats["response_times"])
        print(f"\nСреднее время ответа: {avg_time:.0f} мс")
        print(f"Требование (≤2000 мс) - {'ВЫПОЛНЕНО' if avg_time <= 2000 else 'НЕ ВЫПОЛНЕНО'}")

    print("=" * 60)


if __name__ == "__main__":
    print("Запуск нагрузочного тестирования...\n")
    run_load_test()