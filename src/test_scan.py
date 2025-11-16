# src/test_scan.py
import asyncio
import json
import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей,
# чтобы можно было запускать скрипт напрямую (python src/test_scan.py ...)
# и импорты вида 'from core.scanner' работали корректно.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scanner import scan_many
from core.http_client import HttpClient

async def main():
    """
    Основная асинхронная функция для запуска сканирования из командной строки.
    """
    if len(sys.argv) < 2:
        print("Использование: python src/test_scan.py <ник1> [ник2 ...]")
        sys.exit(1)

    usernames = sys.argv[1:]
    print(f"[*] Запускаю сканирование для: {', '.join(usernames)}")

    try:
        results = await scan_many(usernames)
        print("\n[+] Результаты сканирования:")
        # Используем json.dumps для красивого и детального вывода, включая ошибки
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n[!] Произошла критическая ошибка: {e}")
    finally:
        # Важно всегда закрывать сессию клиента, чтобы избежать предупреждений
        print("\n[*] Закрываю сетевую сессию...")
        await HttpClient.close_session()


if __name__ == "__main__":
    # В Windows может потребоваться другая политика цикла событий для qasync
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())