# src/test_scan.py
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scanner import scan_many
from core.http_client import HttpClient
from core.module_loader import load_modules, shutdown_modules

async def main():
    if len(sys.argv) < 2:
        print("Использование: python src/test_scan.py <ник1> [ник2 ...]")
        sys.exit(1)
        
    # ИЗМЕНЕНИЕ: Явный и корректный порядок инициализации
    await HttpClient.initialize()
    await load_modules()

    usernames = sys.argv[1:]
    print(f"[*] Запускаю сканирование для: {', '.join(usernames)}")

    try:
        results = await scan_many(usernames)
        print("\n[+] Результаты сканирования:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n[!] Произошла критическая ошибка: {e}")
    finally:
        # ИЗМЕНЕНИЕ: Корректный порядок завершения
        await shutdown_modules()
        await HttpClient.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Ошибка во время выполнения: {e}")